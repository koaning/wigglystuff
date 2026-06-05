// Tiny safe expression parser for AttractorWidget formulas.
// Grammar: expr = term (('+'|'-') term)*
//          term = factor (('*'|'/') factor)*
//          factor = unary ('^' factor)?      // right-assoc
//          unary = ('-'|'+') unary | atom
//          atom = number | ident | ident '(' expr (',' expr)* ')' | '(' expr ')'
//
// Output: AST nodes with codegen helpers toJS(ast, paramNames) and
// toGLSL(ast, paramNames). Both treat identifiers as:
//   - x / y      -> trajectory state
//   - pi / e     -> constants
//   - param key  -> uniform / object access
//   - func call  -> whitelisted math function

const FUNCS = new Set([
  "sin", "cos", "tan", "asin", "acos", "atan", "atan2",
  "exp", "log", "sqrt", "abs", "floor", "sign", "min", "max", "pow",
]);
const CONSTS = new Set(["pi", "e"]);
const VARS = new Set(["x", "y"]);

function tokenize(src) {
  const tokens = [];
  let i = 0;
  while (i < src.length) {
    const c = src[i];
    if (/\s/.test(c)) { i++; continue; }
    if (/[0-9]/.test(c) || (c === "." && /[0-9]/.test(src[i + 1] || ""))) {
      let j = i;
      while (j < src.length && /[0-9.]/.test(src[j])) j++;
      if (src[j] === "e" || src[j] === "E") {
        j++;
        if (src[j] === "+" || src[j] === "-") j++;
        while (j < src.length && /[0-9]/.test(src[j])) j++;
      }
      tokens.push({ type: "num", value: parseFloat(src.slice(i, j)) });
      i = j;
      continue;
    }
    if (/[A-Za-z_]/.test(c)) {
      let j = i;
      while (j < src.length && /[A-Za-z0-9_]/.test(src[j])) j++;
      tokens.push({ type: "ident", value: src.slice(i, j) });
      i = j;
      continue;
    }
    if ("+-*/^(),".includes(c)) {
      tokens.push({ type: c });
      i++;
      continue;
    }
    throw new Error(`Unexpected character '${c}' at position ${i}`);
  }
  return tokens;
}

export function parse(src) {
  const tokens = tokenize(src);
  let pos = 0;
  const peek = () => tokens[pos];
  const eat = (type) => {
    const t = tokens[pos];
    if (!t || t.type !== type) {
      throw new Error(`Expected ${type}, got ${t ? t.type : "end"}`);
    }
    pos++;
    return t;
  };

  function parseExpr() {
    let left = parseTerm();
    while (peek() && (peek().type === "+" || peek().type === "-")) {
      const op = peek().type;
      pos++;
      const right = parseTerm();
      left = { type: "binop", op, left, right };
    }
    return left;
  }

  function parseTerm() {
    let left = parseFactor();
    while (peek() && (peek().type === "*" || peek().type === "/")) {
      const op = peek().type;
      pos++;
      const right = parseFactor();
      left = { type: "binop", op, left, right };
    }
    return left;
  }

  function parseFactor() {
    const base = parseUnary();
    if (peek() && peek().type === "^") {
      pos++;
      const exp = parseFactor();
      return { type: "binop", op: "^", left: base, right: exp };
    }
    return base;
  }

  function parseUnary() {
    if (peek() && (peek().type === "-" || peek().type === "+")) {
      const op = peek().type;
      pos++;
      return { type: "unary", op, arg: parseUnary() };
    }
    return parseAtom();
  }

  function parseAtom() {
    const t = peek();
    if (!t) throw new Error("Unexpected end of expression");
    if (t.type === "num") {
      pos++;
      return { type: "num", value: t.value };
    }
    if (t.type === "(") {
      pos++;
      const inner = parseExpr();
      eat(")");
      return inner;
    }
    if (t.type === "ident") {
      pos++;
      if (peek() && peek().type === "(") {
        pos++;
        const args = [];
        if (peek() && peek().type !== ")") {
          args.push(parseExpr());
          while (peek() && peek().type === ",") {
            pos++;
            args.push(parseExpr());
          }
        }
        eat(")");
        if (!FUNCS.has(t.value)) {
          throw new Error(`Unknown function '${t.value}'`);
        }
        return { type: "call", name: t.value, args };
      }
      return { type: "ident", name: t.value };
    }
    throw new Error(`Unexpected token '${t.type}'`);
  }

  const ast = parseExpr();
  if (pos !== tokens.length) {
    throw new Error(`Trailing tokens at position ${pos}`);
  }
  return ast;
}

function formatFloat(n) {
  // Always emit a decimal so GLSL treats it as float.
  if (!Number.isFinite(n)) return "0.0";
  let s = String(n);
  if (!/[.eE]/.test(s)) s += ".0";
  return s;
}

export function toJS(ast, paramNames) {
  const params = new Set(paramNames);
  function gen(node) {
    switch (node.type) {
      case "num":
        return String(node.value);
      case "ident":
        if (node.name === "x" || node.name === "y") return node.name;
        if (node.name === "pi") return "Math.PI";
        if (node.name === "e") return "Math.E";
        if (params.has(node.name)) return `p.${node.name}`;
        throw new Error(`Unknown identifier '${node.name}'`);
      case "unary":
        return `(${node.op}${gen(node.arg)})`;
      case "binop": {
        if (node.op === "^") {
          return `Math.pow(${gen(node.left)}, ${gen(node.right)})`;
        }
        return `(${gen(node.left)} ${node.op} ${gen(node.right)})`;
      }
      case "call": {
        const args = node.args.map(gen).join(", ");
        return `Math.${node.name}(${args})`;
      }
      default:
        throw new Error(`Bad AST node ${node.type}`);
    }
  }
  return gen(ast);
}

export function toGLSL(ast, paramNames) {
  const params = new Set(paramNames);
  function gen(node) {
    switch (node.type) {
      case "num":
        return formatFloat(node.value);
      case "ident":
        if (node.name === "x") return "p_in.x";
        if (node.name === "y") return "p_in.y";
        if (node.name === "pi") return "3.14159265358979";
        if (node.name === "e") return "2.71828182845905";
        if (params.has(node.name)) return `u_${node.name}`;
        throw new Error(`Unknown identifier '${node.name}'`);
      case "unary":
        return `(${node.op}${gen(node.arg)})`;
      case "binop": {
        if (node.op === "^") {
          return `pow(${gen(node.left)}, ${gen(node.right)})`;
        }
        return `(${gen(node.left)} ${node.op} ${gen(node.right)})`;
      }
      case "call": {
        const args = node.args.map(gen).join(", ");
        // GLSL has no atan2; the two-argument form of atan is equivalent.
        const name = node.name === "atan2" ? "atan" : node.name;
        return `${name}(${args})`;
      }
      default:
        throw new Error(`Bad AST node ${node.type}`);
    }
  }
  return gen(ast);
}

// Compile a pair of expressions into a JS step function (x, y, p) => [nx, ny].
export function compileStep(xExpr, yExpr, paramNames) {
  const xAst = parse(xExpr);
  const yAst = parse(yExpr);
  const xSrc = toJS(xAst, paramNames);
  const ySrc = toJS(yAst, paramNames);
  // eslint-disable-next-line no-new-func
  const fn = new Function(
    "x", "y", "p",
    `return [${xSrc}, ${ySrc}];`
  );
  return fn;
}
