---
title: "SortableList: drag and drop list widget"
description: SortableList renders a list you reorder by dragging, with optional add, remove and inline edit, handing the current order back to Python in Colab.
image: sortablelist
image_alt: SortableList showing three draggable rows under a heading, with an add new item field below
---

# SortableList API

<!-- no-md -->
<div class="wiggly-demo-wrap">
<button class="wiggly-demo" type="button" data-demo="sortlist" data-demo-title="SortableList live demo">
<img class="wiggly-demo__poster" src="../assets/gallery/sortablelist.webp" alt="SortableList showing three draggable rows under a heading, with an add new item field below" decoding="async">
<span class="wiggly-demo__cta">Run this demo live in your browser <span class="wiggly-demo__play">▶</span></span>
</button>
</div>
<!-- /no-md -->

`SortableList` renders a list you reorder by dragging and hands the current order
back to Python as `value`. Turn on `addable`, `removable` and `editable` when the
list should be a small CRUD surface rather than a fixed set — ranking candidates,
sequencing pipeline steps, tidying up a label taxonomy.

See also: [Matrix](matrix.md) for editing a grid of numbers,
[TangleChoice](tangle.md) for picking one option inline in a sentence, and
[EdgeDraw](edge-draw.md) for sketching relationships between named items.

::: wigglystuff.sortable_list.SortableList

## Synced traitlets

| Traitlet | Type | Notes |
| --- | --- | --- |
| `value` | `list[str]` | Ordered list items. |
| `addable` | `bool` | Allow inserting new items. |
| `removable` | `bool` | Allow deleting items. |
| `editable` | `bool` | Allow inline edits. |
| `label` | `str` | Optional heading above the list. |

