from __future__ import annotations

import ast
import inspect
import io
import keyword
import sys
import textwrap
import tokenize
import traceback
from pathlib import Path
from typing import Any

import anywidget
import traitlets


def _empty_annotations(code: str) -> dict[str, Any]:
    return {
        "lines": [
            {
                "number": index,
                "text": line,
                "tokens": [],
                "assigns": [],
                "returns": [],
                "loop_body": [],
                "hover": None,
            }
            for index, line in enumerate(code.splitlines(), start=1)
        ],
        "loops": [],
        "variables": [],
    }


def _error_payload(exc: BaseException) -> dict[str, Any]:
    payload = {"type": type(exc).__name__, "message": str(exc)}
    lineno = getattr(exc, "lineno", None)
    if lineno is None:
        tb = traceback.extract_tb(exc.__traceback__) if exc.__traceback__ else []
        if tb:
            lineno = tb[-1].lineno
    if lineno is not None:
        payload["lineno"] = lineno
    return payload


_MAX_HTML_BYTES = 100_000  # skip giant payloads; fall back to repr


def _html_from_mime(mime: str, data: Any) -> str | None:
    if mime == "text/html" and isinstance(data, str):
        return data
    if mime.startswith("image/") and isinstance(data, str):
        # marimo hands back either a data URL or bare base64; normalize to a URL.
        src = data if data.startswith("data:") else f"data:{mime};base64,{data}"
        return f'<img src="{src}" alt="" />'
    return None


def _render_html(value: Any) -> str | None:
    """Best-effort rich HTML for a value, mirroring marimo's precedence.

    Detects (in order) marimo's ``_display_``/``_mime_`` protocols and the
    IPython ``_repr_html_`` protocol by duck typing, so no optional dependency
    (marimo, pandas, numpy) needs to be importable. Returns ``None`` whenever
    the value has no rich representation, rendering fails, or the payload is
    larger than ``_MAX_HTML_BYTES`` (the caller then falls back to ``repr``).
    """
    html: str | None = None
    try:
        display = getattr(value, "_display_", None)
        if callable(display):
            html = _render_html(display())
        if html is None:
            mime = getattr(value, "_mime_", None)
            if callable(mime):
                mimetype, data = mime()
                html = _html_from_mime(mimetype, data)
        if html is None:
            repr_html = getattr(value, "_repr_html_", None)
            if callable(repr_html):
                result = repr_html()
                html = result if isinstance(result, str) else None
    except Exception:  # noqa: BLE001 - rich rendering is best-effort, never fatal.
        return None
    if html is None or not html.strip():
        return None
    if len(html.encode("utf-8", "replace")) > _MAX_HTML_BYTES:
        return None
    return html


def _clear_trace() -> dict[str, Any]:
    return {"setup": [], "body": [], "returned": None}


def _target_names(target: ast.AST) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, (ast.Tuple, ast.List)):
        names: list[str] = []
        for element in target.elts:
            names.extend(_target_names(element))
        return names
    if isinstance(target, (ast.Attribute, ast.Subscript)):
        value = target.value
        while isinstance(value, (ast.Attribute, ast.Subscript)):
            value = value.value
        if isinstance(value, ast.Name):
            return [value.id]
    return []


def _assigned_names(statement: ast.AST) -> list[str]:
    if isinstance(statement, ast.Assign):
        names: list[str] = []
        for target in statement.targets:
            names.extend(_target_names(target))
        return names
    if isinstance(statement, (ast.AugAssign, ast.AnnAssign)):
        return _target_names(statement.target)
    return []


def _unique(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _as_float(value: Any) -> float | None:
    """Return a plottable float for ``value`` or ``None`` when it is not one.

    Booleans and non-finite floats (nan/inf) are treated as non-numeric so
    they never end up as chart data.
    """
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return number


class _Collector:
    def __init__(
        self,
        loop_meta: dict[str, dict[str, Any]],
        float_precision: int | None = None,
    ) -> None:
        self.loop_meta = loop_meta
        self.float_precision = float_precision
        self.setup_order: list[str] = []
        self.setup_values: dict[str, str] = {}
        self.setup_html: dict[str, str] = {}
        self.global_values: dict[str, str] = {}
        self.global_numerics: dict[str, float | None] = {}
        self.global_html: dict[str, str] = {}
        self.body: list[dict[str, Any]] = []
        self.loop_stack: list[str] = []
        self.pass_stack: list[dict[str, Any]] = []
        self.pending_passes: dict[str, dict[str, Any]] = {}
        self.returned: dict[str, str] | None = None

    def record_iter(self, loop_id: str) -> None:
        instance = self._loop_instance(loop_id)
        pass_record = {
            "cells": {},
            "cells_html": {},
            "changed": [],
            "children": [],
            "_numerics": {},
        }
        pass_record["_instance"] = instance
        instance["passes"].append(pass_record)
        self.pending_passes[loop_id] = pass_record

    def enter_loop(self, loop_id: str) -> None:
        self.loop_stack.append(loop_id)
        self.pass_stack.append(self.pending_passes.pop(loop_id))

    def exit_loop(self, loop_id: str) -> None:
        if not self.loop_stack or self.loop_stack[-1] != loop_id:
            return
        pass_record = self.pass_stack[-1]
        pass_record["_snapshot"] = dict(self.global_values)
        pass_record["_snapshot_numerics"] = dict(self.global_numerics)
        pass_record["_snapshot_html"] = dict(self.global_html)
        # exit_loop runs in the loop body's `finally`, so if an exception is
        # unwinding through it right now this pass is on the failure path.
        if sys.exc_info()[0] is not None:
            pass_record["_failed"] = True
        self.loop_stack.pop()
        self.pass_stack.pop()

    def _format_value(self, value: Any) -> str:
        # Trim only float scalars (numpy floats subclass float); ints, strings,
        # arrays, etc. keep their exact repr. Charts use the raw floats, so this
        # affects the displayed table cells only.
        if self.float_precision is not None and isinstance(value, float):
            return f"{value:.{self.float_precision}g}"
        return repr(value)

    def record_assign(self, name: str, value: Any, lineno: int) -> None:
        value_repr = self._format_value(value)
        numeric = _as_float(value)
        value_html = _render_html(value)
        self.global_values[name] = value_repr
        self.global_numerics[name] = numeric
        if value_html is not None:
            self.global_html[name] = value_html
        else:
            self.global_html.pop(name, None)
        if not self.loop_stack:
            if name not in self.setup_order:
                self.setup_order.append(name)
            self.setup_values[name] = value_repr
            if value_html is not None:
                self.setup_html[name] = value_html
            else:
                self.setup_html.pop(name, None)
            return

        pass_record = self.pass_stack[-1]
        instance = pass_record["_instance"]
        if name not in instance["_assigned_names"]:
            instance["_assigned_names"].append(name)
        if name not in instance["_assignment_order"]:
            instance["_assignment_order"].append(name)
        pass_record["cells"][name] = value_repr
        pass_record["_numerics"][name] = numeric
        if value_html is not None:
            pass_record["cells_html"][name] = value_html
        if name not in pass_record["changed"]:
            pass_record["changed"].append(name)

    def record_namedexpr(self, name: str, value: Any, lineno: int) -> Any:
        self.record_assign(name, value, lineno)
        return value

    def record_return(self, value: Any, lineno: int) -> Any:
        self.returned = {"repr": self._format_value(value)}
        value_html = _render_html(value)
        if value_html is not None:
            self.returned["html"] = value_html
        return value

    def trace(self) -> dict[str, Any]:
        return {
            "setup": [
                self._setup_entry(name)
                for name in self.setup_order
                if name in self.setup_values
            ],
            "body": [self._serialize_loop(loop) for loop in self.body],
            "returned": self.returned,
        }

    def _setup_entry(self, name: str) -> dict[str, Any]:
        entry = {"name": name, "repr": self.setup_values[name]}
        if name in self.setup_html:
            entry["html"] = self.setup_html[name]
        return entry

    def _loop_instance(self, loop_id: str) -> dict[str, Any]:
        container = self.pass_stack[-1]["children"] if self.pass_stack else self.body
        for loop in container:
            if loop["loop_id"] == loop_id:
                return loop
        meta = self.loop_meta[loop_id]
        loop = {
            "kind": "loop",
            "loop_id": loop_id,
            "loop_type": meta["loop_type"],
            "columns": [],
            "passes": [],
            "_target_names": meta.get("target_names", []),
            "_assigned_names": [],
            "_assignment_order": [],
        }
        container.append(loop)
        return loop

    def _columns_for(self, loop: dict[str, Any]) -> list[str]:
        assigned = set(loop["_assigned_names"])
        target_names = [name for name in loop["_target_names"] if name in assigned]
        setup_names = [name for name in self.setup_order if name in assigned]
        assignment_names = [name for name in loop["_assignment_order"] if name in assigned]
        return _unique(target_names + setup_names + assignment_names)

    def _serialize_loop(self, loop: dict[str, Any]) -> dict[str, Any]:
        columns = self._columns_for(loop)
        passes = []
        for pass_record in loop["passes"]:
            snapshot = pass_record.get("_snapshot", {})
            snapshot_html = pass_record.get("_snapshot_html", {})
            cells = {
                name: pass_record["cells"].get(name, snapshot.get(name, ""))
                for name in columns
                if name in pass_record["cells"] or name in snapshot
            }
            cells_html = {}
            for name in columns:
                if name in pass_record["cells_html"]:
                    cells_html[name] = pass_record["cells_html"][name]
                elif name not in pass_record["cells"] and name in snapshot_html:
                    cells_html[name] = snapshot_html[name]
            entry = {
                "cells": cells,
                "changed": list(pass_record["changed"]),
                "failed": pass_record.get("_failed", False),
                "children": [
                    self._serialize_loop(child)
                    for child in pass_record["children"]
                ],
            }
            if cells_html:
                entry["cells_html"] = cells_html
            passes.append(entry)
        return {
            "kind": "loop",
            "loop_id": loop["loop_id"],
            "loop_type": loop["loop_type"],
            "columns": columns,
            "passes": passes,
            "numerics": self._numerics_for(loop, columns),
        }

    def _numerics_for(
        self, loop: dict[str, Any], columns: list[str]
    ) -> dict[str, list[float]]:
        numerics: dict[str, list[float]] = {}
        for name in columns:
            values: list[float] = []
            for pass_record in loop["passes"]:
                snapshot = pass_record.get("_snapshot_numerics", {})
                pass_numerics = pass_record.get("_numerics", {})
                if name in pass_numerics:
                    value = pass_numerics[name]
                elif name in snapshot:
                    value = snapshot[name]
                else:
                    value = None
                if value is None:
                    break
                values.append(value)
            if len(values) == len(loop["passes"]) and values:
                numerics[name] = values
        return numerics


class _Instrumenter(ast.NodeTransformer):
    def __init__(self, function_name: str | None) -> None:
        self.function_name = function_name
        self.in_target = False
        self.instrumented = False
        self.loop_count = 0
        self.loop_meta: dict[str, dict[str, Any]] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        if self.in_target:
            return node
        if self.instrumented:
            return node
        if self.function_name is not None and node.name != self.function_name:
            return node

        self.in_target = True
        parameter_records = self._parameter_records(node)
        new_body = []
        for statement in node.body:
            transformed = self.visit(statement)
            if isinstance(transformed, list):
                new_body.extend(transformed)
            else:
                new_body.append(transformed)
        node.body = parameter_records + new_body
        self.in_target = False
        self.instrumented = True
        return node

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        return node

    def visit_Lambda(self, node: ast.Lambda) -> ast.AST:
        return node

    def visit_Assign(self, node: ast.Assign) -> list[ast.stmt]:
        self.generic_visit(node)
        return [node, *self._assign_records(_assigned_names(node), node.lineno)]

    def visit_AugAssign(self, node: ast.AugAssign) -> list[ast.stmt]:
        self.generic_visit(node)
        return [node, *self._assign_records(_assigned_names(node), node.lineno)]

    def visit_AnnAssign(self, node: ast.AnnAssign) -> list[ast.stmt]:
        self.generic_visit(node)
        return [node, *self._assign_records(_assigned_names(node), node.lineno)]

    def visit_NamedExpr(self, node: ast.NamedExpr) -> ast.AST:
        self.generic_visit(node)
        names = _target_names(node.target)
        if len(names) != 1:
            return node
        return ast.copy_location(
            ast.Call(
                func=ast.Name("__liveedit_record_namedexpr__", ast.Load()),
                args=[
                    ast.Constant(names[0]),
                    node,
                    ast.Constant(getattr(node, "lineno", 0)),
                ],
                keywords=[],
            ),
            node,
        )

    def visit_Return(self, node: ast.Return) -> ast.AST:
        self.generic_visit(node)
        value = node.value if node.value is not None else ast.Constant(None)
        node.value = ast.copy_location(
            ast.Call(
                func=ast.Name("__liveedit_record_return__", ast.Load()),
                args=[value, ast.Constant(node.lineno)],
                keywords=[],
            ),
            node,
        )
        return node

    def visit_For(self, node: ast.For) -> ast.AST:
        return self._loop(node, "for", _target_names(node.target))

    def visit_AsyncFor(self, node: ast.AsyncFor) -> ast.AST:
        return node

    def visit_While(self, node: ast.While) -> ast.AST:
        return self._loop(node, "while", [])

    def _loop(
        self, node: ast.For | ast.While, loop_type: str, target_names: list[str]
    ) -> ast.AST:
        self.loop_count += 1
        loop_id = f"loop_{node.lineno}_{self.loop_count}"
        self.loop_meta[loop_id] = {
            "loop_id": loop_id,
            "loop_type": loop_type,
            "lineno": node.lineno,
            "target_names": target_names,
        }
        if isinstance(node, ast.For):
            node.iter = self.visit(node.iter)
        else:
            node.test = self.visit(node.test)
        node.body = self._visit_statement_list(node.body)
        node.orelse = self._visit_statement_list(node.orelse)

        record_iter = ast.copy_location(
            ast.Expr(
                ast.Call(
                    func=ast.Name("__liveedit_record_iter__", ast.Load()),
                    args=[ast.Constant(loop_id)],
                    keywords=[],
                )
            ),
            node,
        )
        enter_loop = ast.copy_location(
            ast.Expr(
                ast.Call(
                    func=ast.Name("__liveedit_enter_loop__", ast.Load()),
                    args=[ast.Constant(loop_id)],
                    keywords=[],
                )
            ),
            node,
        )
        target_records = self._assign_records(target_names, node.lineno)
        exit_loop = ast.copy_location(
            ast.Expr(
                ast.Call(
                    func=ast.Name("__liveedit_exit_loop__", ast.Load()),
                    args=[ast.Constant(loop_id)],
                    keywords=[],
                )
            ),
            node,
        )
        wrapped_body = [
            ast.copy_location(
                ast.Try(
                    body=[enter_loop, *target_records, *node.body],
                    handlers=[],
                    orelse=[],
                    finalbody=[exit_loop],
                ),
                node,
            )
        ]
        node.body = [record_iter, *wrapped_body]
        return node

    def _visit_statement_list(self, statements: list[ast.stmt]) -> list[ast.stmt]:
        visited = []
        for statement in statements:
            transformed = self.visit(statement)
            if isinstance(transformed, list):
                visited.extend(transformed)
            else:
                visited.append(transformed)
        return visited

    def _parameter_records(self, node: ast.FunctionDef) -> list[ast.stmt]:
        args = node.args
        names = [arg.arg for arg in args.posonlyargs + args.args + args.kwonlyargs]
        if args.vararg is not None:
            names.append(args.vararg.arg)
        if args.kwarg is not None:
            names.append(args.kwarg.arg)
        return self._assign_records(names, node.lineno)

    def _assign_records(self, names: list[str], lineno: int) -> list[ast.stmt]:
        records = []
        for name in _unique(names):
            records.append(
                ast.copy_location(
                    ast.Expr(
                        ast.Call(
                            func=ast.Name("__liveedit_record_assign__", ast.Load()),
                            args=[
                                ast.Constant(name),
                                ast.Name(name, ast.Load()),
                                ast.Constant(lineno),
                            ],
                            keywords=[],
                        )
                    ),
                    ast.Constant(None, lineno=lineno, col_offset=0),
                )
            )
        return records


class _AnnotationBuilder(ast.NodeVisitor):
    def __init__(self, code: str, function_name: str | None) -> None:
        self.code = code
        self.function_name = function_name
        self.lines = _empty_annotations(code)["lines"]
        self.variables: set[str] = set()
        self.loops: list[dict[str, Any]] = []
        self.loop_stack: list[str] = []
        self.loop_count = 0
        self.in_target = False
        self.seen_target = False

    def build(self, tree: ast.Module) -> dict[str, Any]:
        self.visit(tree)
        self._apply_syntax_tokens()
        return {
            "lines": self.lines,
            "loops": self.loops,
            "variables": sorted(self.variables),
        }

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if self.in_target or self.seen_target:
            return
        if self.function_name is not None and node.name != self.function_name:
            return
        self.in_target = True
        self.seen_target = True
        args = node.args
        for arg in args.posonlyargs + args.args + args.kwonlyargs:
            self.variables.add(arg.arg)
        if args.vararg is not None:
            self.variables.add(args.vararg.arg)
        if args.kwarg is not None:
            self.variables.add(args.kwarg.arg)
        self.generic_visit(node)
        self.in_target = False

    def visit_Name(self, node: ast.Name) -> None:
        if not self.in_target:
            return
        self.variables.add(node.id)

    def visit_Assign(self, node: ast.Assign) -> None:
        self._mark_assign(node, _assigned_names(node))
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self._mark_assign(node, _assigned_names(node))
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._mark_assign(node, _assigned_names(node))
        self.generic_visit(node)

    def visit_Return(self, node: ast.Return) -> None:
        names = _names_in(node.value) if node.value is not None else []
        line = self._line(node.lineno)
        if line is not None:
            line["returns"] = _unique([*line["returns"], *names])
            if names:
                line["hover"] = f"var:{names[0]}"
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self._visit_loop(node, "for", _target_names(node.target))

    def visit_While(self, node: ast.While) -> None:
        self._visit_loop(node, "while", [])

    def _visit_loop(
        self, node: ast.For | ast.While, loop_type: str, target_names: list[str]
    ) -> None:
        self.loop_count += 1
        loop_id = f"loop_{node.lineno}_{self.loop_count}"
        self.loops.append(
            {
                "loop_id": loop_id,
                "loop_type": loop_type,
                "lineno": node.lineno,
                "target_names": target_names,
            }
        )
        self._mark_loop_line(node.lineno, loop_id)
        self.loop_stack.append(loop_id)
        for statement in node.body:
            self._mark_statement_range(statement, self.loop_stack)
            self.visit(statement)
        self.loop_stack.pop()
        for statement in node.orelse:
            self.visit(statement)

    def _mark_assign(self, node: ast.AST, names: list[str]) -> None:
        line = self._line(node.lineno)
        if line is not None:
            line["assigns"] = _unique([*line["assigns"], *names])
            if names:
                line["hover"] = f"var:{names[0]}"

    def _mark_loop_line(self, lineno: int, loop_id: str) -> None:
        line = self._line(lineno)
        if line is None:
            return
        line["loop_body"] = _unique([*line["loop_body"], loop_id])
        line["hover"] = f"loop:{' '.join(line['loop_body'])}"

    def _mark_statement_range(self, node: ast.AST, loop_ids: list[str]) -> None:
        start = getattr(node, "lineno", None)
        end = getattr(node, "end_lineno", start)
        if start is None:
            return
        for lineno in range(start, (end or start) + 1):
            line = self._line(lineno)
            if line is not None:
                line["loop_body"] = _unique([*line["loop_body"], *loop_ids])
                if line["hover"] is None:
                    line["hover"] = f"loop:{' '.join(line['loop_body'])}"

    def _line(self, lineno: int) -> dict[str, Any] | None:
        if 1 <= lineno <= len(self.lines):
            return self.lines[lineno - 1]
        return None

    def _apply_syntax_tokens(self) -> None:
        for line in self.lines:
            line["tokens"] = []
        try:
            tokens = list(tokenize.generate_tokens(io.StringIO(self.code).readline))
        except tokenize.TokenError:
            return
        for index, token in enumerate(tokens):
            token_type = self._syntax_type(tokens, index)
            if token_type is None:
                continue
            start_line, start_col = token.start
            end_line, end_col = token.end
            if start_line != end_line:
                continue
            line = self._line(start_line)
            if line is None:
                continue
            item = {"type": token_type, "start": start_col, "end": end_col}
            if token_type == "var":
                item["name"] = token.string
            line["tokens"].append(item)

    def _syntax_type(
        self, tokens: list[tokenize.TokenInfo], index: int
    ) -> str | None:
        token = tokens[index]
        if token.type == tokenize.NAME:
            if keyword.iskeyword(token.string):
                return "kw"
            previous_text = _previous_significant_token(tokens, index)
            next_text = _next_significant_token(tokens, index)
            if previous_text in {"def", "class"} or next_text == "(":
                return "fn"
            return "var"
        if token.type == tokenize.NUMBER:
            return "num"
        if token.type == tokenize.STRING:
            return "str"
        if token.type == tokenize.COMMENT:
            return "comment"
        return None


def _previous_significant_token(
    tokens: list[tokenize.TokenInfo], index: int
) -> str | None:
    for token in reversed(tokens[:index]):
        if token.type not in {
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.INDENT,
            tokenize.DEDENT,
            tokenize.COMMENT,
        }:
            return token.string
    return None


def _next_significant_token(
    tokens: list[tokenize.TokenInfo], index: int
) -> str | None:
    for token in tokens[index + 1 :]:
        if token.type not in {
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.INDENT,
            tokenize.DEDENT,
            tokenize.COMMENT,
        }:
            return token.string
    return None


def _names_in(node: ast.AST | None) -> list[str]:
    if node is None:
        return []
    names = []
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            names.append(child.id)
    return _unique(names)


def _find_function(tree: ast.Module, function_name: str | None) -> ast.FunctionDef:
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    if function_name is not None:
        for function in functions:
            if function.name == function_name:
                return function
    if functions:
        return functions[0]
    raise ValueError("LiveEdit requires source containing a top-level def.")


def _trace_code(
    code: str,
    args: tuple[Any, ...] = (),
    kwargs: dict[str, Any] | None = None,
    *,
    function_name: str | None = None,
    globalns: dict[str, Any] | None = None,
    float_precision: int | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
    kwargs = {} if kwargs is None else dict(kwargs)
    try:
        tree = ast.parse(code)
        function = _find_function(tree, function_name)
        target_name = function.name
    except SyntaxError as exc:
        return _clear_trace(), _empty_annotations(code), _error_payload(exc)
    except ValueError as exc:
        return _clear_trace(), _empty_annotations(code), _error_payload(exc)

    annotations = _AnnotationBuilder(code, target_name).build(tree)
    instrumenter = _Instrumenter(target_name)
    transformed = instrumenter.visit(tree)
    ast.fix_missing_locations(transformed)
    collector = _Collector(instrumenter.loop_meta, float_precision)
    namespace = dict(globalns or {})
    namespace.update(
        {
            "__liveedit_record_iter__": collector.record_iter,
            "__liveedit_enter_loop__": collector.enter_loop,
            "__liveedit_exit_loop__": collector.exit_loop,
            "__liveedit_record_assign__": collector.record_assign,
            "__liveedit_record_namedexpr__": collector.record_namedexpr,
            "__liveedit_record_return__": collector.record_return,
        }
    )
    try:
        compiled = compile(transformed, "<liveedit>", "exec")
        exec(compiled, namespace)
        traced_function = namespace[target_name]
        try:
            inspect.signature(traced_function).bind(*args, **kwargs)
        except TypeError as exc:
            raise TypeError(f"arguments don't match `{target_name}`: {exc}") from exc
        traced_function(*args, **kwargs)
        return collector.trace(), annotations, None
    except Exception as exc:  # noqa: BLE001 - widget errors are data, not crashes.
        return collector.trace(), annotations, _error_payload(exc)


def _source_for(fn: Any) -> tuple[str, str, dict[str, Any]]:
    if not inspect.isfunction(fn):
        raise TypeError(
            f"LiveEdit.inspect_run expected a Python function with Python source, "
            f"got {type(fn).__name__}."
        )
    try:
        source = inspect.getsource(fn)
    except (OSError, TypeError) as exc:
        raise TypeError(
            "LiveEdit.inspect_run could not find usable Python source for this "
            "function. Plain top-level `def` functions work best."
        ) from exc
    code = textwrap.dedent(source)
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise ValueError(f"LiveEdit.inspect_run found invalid Python source: {exc}") from exc
    _find_function(tree, fn.__name__)
    return code, fn.__name__, fn.__globals__


class LiveEdit(anywidget.AnyWidget):
    """Read-only function trace widget for inspecting one Python run.

    ``LiveEdit.inspect_run(fn, *args, **kwargs)`` is the primary constructor for
    v1. The widget stores the original Python args privately and only syncs
    repr-based trace data to the browser, which keeps future editable code
    updates possible without serializing arbitrary Python objects.
    """

    _esm = Path(__file__).parent / "static" / "liveedit.js"
    _css = Path(__file__).parent / "static" / "liveedit.css"

    code = traitlets.Unicode("").tag(sync=True)
    trace = traitlets.Dict(default_value={}).tag(sync=True)
    annotations = traitlets.Dict(default_value={}).tag(sync=True)
    error = traitlets.Dict(default_value=None, allow_none=True).tag(sync=True)
    editable = traitlets.Bool(False).tag(sync=True)
    theme = traitlets.Unicode("auto").tag(sync=True)
    # width: 0 means "grow to fit content" (host page scrolls); a positive value
    # caps the width and shows an internal horizontal scrollbar instead.
    width = traitlets.Int(0).tag(sync=True)
    height = traitlets.Int(520).tag(sync=True)
    # Round float cells to this many significant figures (None = exact repr).
    # Applied Python-side; charts keep full precision.
    float_precision = traitlets.Int(default_value=None, allow_none=True)
    # Show only these variables in the trace tables (empty = show all). Applied
    # in the browser, so it updates without re-running the function.
    visible_columns = traitlets.List(traitlets.Unicode()).tag(sync=True)

    def __init__(
        self,
        code: str,
        *,
        args: tuple[Any, ...] = (),
        kwargs: dict[str, Any] | None = None,
        editable: bool = False,
        function_name: str | None = None,
        globalns: dict[str, Any] | None = None,
        height: int | None = None,
        float_precision: int | None = None,
        visible_columns: list[str] | None = None,
        **widget_kwargs: Any,
    ) -> None:
        self._liveedit_args = tuple(args)
        self._liveedit_kwargs = {} if kwargs is None else dict(kwargs)
        self._liveedit_function_name = function_name
        self._liveedit_globalns = dict(globalns or {})
        trace, annotations, error = _trace_code(
            code,
            self._liveedit_args,
            self._liveedit_kwargs,
            function_name=function_name,
            globalns=self._liveedit_globalns,
            float_precision=float_precision,
        )
        if height is None:
            # Fit the source by default: ~21px per rendered line (13px font *
            # 1.55 line-height) plus top/bottom padding, floored at 520px so the
            # trace panel keeps a roomy scroll area. Lines never wrap (they sit
            # in an overflow-x panel), so a line-count estimate is accurate.
            n_lines = len(code.splitlines()) or 1
            height = max(520, n_lines * 21 + 40)
        super().__init__(
            code=code,
            trace=trace,
            annotations=annotations,
            error=error,
            editable=editable,
            height=height,
            float_precision=float_precision,
            visible_columns=list(visible_columns or []),
            **widget_kwargs,
        )

    def _recompute(self, code: str) -> None:
        trace, annotations, error = _trace_code(
            code,
            self._liveedit_args,
            self._liveedit_kwargs,
            function_name=self._liveedit_function_name,
            globalns=self._liveedit_globalns,
            float_precision=self.float_precision,
        )
        self.trace = trace
        self.annotations = annotations
        self.error = error

    @traitlets.observe("code")
    def _retrace(self, change: dict[str, Any]) -> None:
        self._recompute(change["new"])

    @traitlets.observe("float_precision")
    def _reformat(self, change: dict[str, Any]) -> None:
        self._recompute(self.code)

    @classmethod
    def inspect_run(
        cls,
        fn: Any,
        *args: Any,
        float_precision: int | None = None,
        visible_columns: list[str] | None = None,
        **kwargs: Any,
    ) -> "LiveEdit":
        code, function_name, globalns = _source_for(fn)
        return cls(
            code,
            args=args,
            kwargs=kwargs,
            editable=False,
            function_name=function_name,
            globalns=globalns,
            float_precision=float_precision,
            visible_columns=visible_columns,
        )


def inspect_run(fn: Any, *args: Any, **kwargs: Any) -> LiveEdit:
    """Inspect one run of a Python function with ``LiveEdit``."""

    return LiveEdit.inspect_run(fn, *args, **kwargs)
