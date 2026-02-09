# ModuleTreeWidget API


 Bases: `AnyWidget`


Interactive tree viewer for PyTorch `nn.Module` architecture.


Displays the full module hierarchy with parameter counts, shapes, trainable/frozen/buffer badges, and a density indicator.



```
from wigglystuff import ModuleTreeWidget

import torch.nn as nn
from wigglystuff import ModuleTreeWidget

model = nn.Sequential(
    nn.Linear(784, 256),
    nn.ReLU(),
    nn.Linear(256, 10),
)
ModuleTreeWidget(model, initial_expand_depth=2)
```


Create a ModuleTreeWidget.


  Source code in `wigglystuff/module_tree.py`

```
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
```


## total_param_count `property`


```
total_param_count
```


Total number of (unique) parameters in the module.


## total_size_bytes `property`


```
total_size_bytes
```


Total memory footprint in bytes.


## total_trainable_count `property`


```
total_trainable_count
```


Total number of trainable parameters in the module.


## Synced traitlets


| Traitlet | Type | Notes |
| --- | --- | --- |
| `tree` | `dict` | JSON-serializable tree extracted from a PyTorch `nn.Module`. |
| `initial_expand_depth` | `int` | Number of tree levels to expand on first render (default: 1). |
