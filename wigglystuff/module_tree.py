"""ModuleTreeWidget for visualising PyTorch nn.Module architecture."""

from pathlib import Path
from typing import Any, Optional

import anywidget
import traitlets


def _extract_tree(module, name=""):
    """Recursively extract a JSON-serializable tree from an nn.Module."""
    params = []
    own_param_count = 0
    own_trainable_count = 0

    for pname, param in module.named_parameters(recurse=False):
        shape = list(param.shape)
        numel = param.numel()
        trainable = param.requires_grad
        params.append({
            "name": pname,
            "shape": shape,
            "numel": numel,
            "trainable": trainable,
        })
        own_param_count += numel
        if trainable:
            own_trainable_count += numel

    for bname, buf in module.named_buffers(recurse=False):
        shape = list(buf.shape)
        numel = buf.numel()
        params.append({
            "name": bname,
            "shape": shape,
            "numel": numel,
            "trainable": False,
            "is_buffer": True,
        })
        own_param_count += numel

    children = []
    child_total = 0
    child_trainable = 0
    for child_name, child_module in module.named_children():
        child_tree = _extract_tree(child_module, child_name)
        children.append(child_tree)
        child_total += child_tree["total_param_count"]
        child_trainable += child_tree["total_trainable_count"]

    return {
        "name": name,
        "type": module.__class__.__name__,
        "params": params,
        "own_param_count": own_param_count,
        "total_param_count": own_param_count + child_total,
        "own_trainable_count": own_trainable_count,
        "total_trainable_count": own_trainable_count + child_trainable,
        "children": children,
    }


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
        **kwargs: Any,
    ):
        """Create a ModuleTreeWidget.

        Args:
            module: A PyTorch ``nn.Module`` to visualise.
            initial_expand_depth: Number of tree levels to expand initially.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        super().__init__(initial_expand_depth=initial_expand_depth, **kwargs)
        if module is not None:
            self.tree = _extract_tree(module)
