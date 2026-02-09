"""ModuleTreeWidget for visualising PyTorch nn.Module architecture."""

from pathlib import Path

import anywidget
import traitlets


def _is_uninitialized(param):
    """Check if a parameter is a lazy/uninitialized parameter."""
    try:
        from torch.nn.parameter import UninitializedParameter
        return isinstance(param, UninitializedParameter)
    except ImportError:
        return False


def _find_unregistered_modules(module):
    """Find nn.Module instances stored in plain Python containers."""
    import torch.nn as nn

    registered = {id(child) for _, child in module.named_children()}
    warnings = []
    for attr_name, attr_val in vars(module).items():
        if attr_name.startswith("_"):
            continue
        items = []
        if isinstance(attr_val, (list, tuple)):
            items = [v for v in attr_val if isinstance(v, nn.Module)]
        elif isinstance(attr_val, dict):
            items = [v for v in attr_val.values() if isinstance(v, nn.Module)]
        hidden = [m for m in items if id(m) not in registered]
        if hidden:
            warnings.append({
                "attr": attr_name,
                "count": len(hidden),
            })
    return warnings


def _extract_tree(module, name="", _seen=None):
    """Recursively extract a JSON-serializable tree from an nn.Module."""
    if _seen is None:
        _seen = set()

    params = []
    own_param_count = 0
    own_trainable_count = 0
    own_size_bytes = 0

    for pname, param in module.named_parameters(recurse=False):
        is_lazy = _is_uninitialized(param)
        ptr = param.data_ptr() if not is_lazy else None
        is_shared = ptr is not None and ptr in _seen
        if ptr is not None:
            _seen.add(ptr)

        if is_lazy:
            shape = []
            numel = 0
            size_bytes = 0
        else:
            shape = list(param.shape)
            numel = param.numel()
            size_bytes = numel * param.element_size()

        trainable = param.requires_grad
        dtype_str = str(param.dtype).replace("torch.", "")
        entry = {
            "name": pname,
            "shape": shape,
            "numel": numel,
            "trainable": trainable,
            "dtype": dtype_str,
        }
        if is_shared:
            entry["is_shared"] = True
        if is_lazy:
            entry["is_lazy"] = True
        params.append(entry)

        if not is_shared:
            own_param_count += numel
            own_size_bytes += size_bytes
            if trainable:
                own_trainable_count += numel

    for bname, buf in module.named_buffers(recurse=False):
        shape = list(buf.shape)
        numel = buf.numel()
        dtype_str = str(buf.dtype).replace("torch.", "")
        params.append({
            "name": bname,
            "shape": shape,
            "numel": numel,
            "trainable": False,
            "is_buffer": True,
            "dtype": dtype_str,
        })
        own_param_count += numel
        own_size_bytes += numel * buf.element_size()

    children = []
    child_total = 0
    child_trainable = 0
    child_size_bytes = 0
    for child_name, child_module in module.named_children():
        child_tree = _extract_tree(child_module, child_name, _seen)
        children.append(child_tree)
        child_total += child_tree["total_param_count"]
        child_trainable += child_tree["total_trainable_count"]
        child_size_bytes += child_tree["total_size_bytes"]

    # Detect unregistered nn.Module instances in plain containers
    unregistered = _find_unregistered_modules(module)

    result = {
        "name": name,
        "type": module.__class__.__name__,
        "params": params,
        "own_param_count": own_param_count,
        "total_param_count": own_param_count + child_total,
        "own_trainable_count": own_trainable_count,
        "total_trainable_count": own_trainable_count + child_trainable,
        "total_size_bytes": own_size_bytes + child_size_bytes,
        "children": children,
    }
    if unregistered:
        result["unregistered_warnings"] = unregistered
    return result


class ModuleTreeWidget(anywidget.AnyWidget):
    """Interactive tree viewer for PyTorch ``nn.Module`` architecture.

    Displays the full module hierarchy with parameter counts, shapes,
    trainable/frozen/buffer badges, and a density indicator.

    Examples:
        ```python
        import torch.nn as nn
        from wigglystuff import ModuleTreeWidget

        model = nn.Sequential(
            nn.Linear(784, 256),
            nn.ReLU(),
            nn.Linear(256, 10),
        )
        ModuleTreeWidget(model, initial_expand_depth=2)
        ```
    """

    _esm = Path(__file__).parent / "static" / "moduletree.js"
    _css = Path(__file__).parent / "static" / "moduletree.css"

    tree = traitlets.Dict(default_value={}).tag(sync=True)
    initial_expand_depth = traitlets.Int(default_value=1).tag(sync=True)

    def __init__(
        self,
        module=None,
        *,
        initial_expand_depth: int = 1,
    ):
        """Create a ModuleTreeWidget.

        Args:
            module: A PyTorch ``nn.Module`` to visualise.
            initial_expand_depth: Number of tree levels to expand initially.
        """
        super().__init__(initial_expand_depth=initial_expand_depth)
        if module is not None:
            self.tree = _extract_tree(module)

    @property
    def total_param_count(self):
        """Total number of (unique) parameters in the module."""
        return self.tree.get("total_param_count", 0)

    @property
    def total_trainable_count(self):
        """Total number of trainable parameters in the module."""
        return self.tree.get("total_trainable_count", 0)

    @property
    def total_size_bytes(self):
        """Total memory footprint in bytes."""
        return self.tree.get("total_size_bytes", 0)
