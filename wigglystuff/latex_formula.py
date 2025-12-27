from pathlib import Path
from typing import Any, List, Optional

import anywidget
import traitlets


class LatexFormula(anywidget.AnyWidget):
    """Widget for rendering large LaTeX formulas with support for chaining parts.

    This widget can render LaTeX formulas and chain together multiple parts.
    It can also integrate with other widgets like Matrix for displaying
    matrices within formulas.

    Examples:
        ```python
        # Simple formula
        formula = LatexFormula(parts=["x^2 + y^2 = r^2"])
        
        # Chained parts
        formula = LatexFormula(parts=["A", "=", "\\begin{pmatrix} 1 & 2 \\\\ 3 & 4 \\end{pmatrix}"])
        
        # With matrix widget integration
        from wigglystuff import Matrix
        matrix = Matrix(rows=2, cols=2)
        # Use matrix values in formula parts
        formula = LatexFormula(parts=["A", "=", f"\\begin{{pmatrix}} {matrix.matrix[0][0]} & {matrix.matrix[0][1]} \\\\ {matrix.matrix[1][0]} & {matrix.matrix[1][1]} \\end{{pmatrix}}"])
        ```
    """

    _esm = Path(__file__).parent / "static" / "latex_formula.js"
    _css = Path(__file__).parent / "static" / "latex_formula.css"
    parts = traitlets.List([]).tag(sync=True)
    font_size = traitlets.Float(16.0).tag(sync=True)
    display_mode = traitlets.Bool(False).tag(sync=True)  # True for block, False for inline

    def __init__(
        self,
        parts: Optional[List[str]] = None,
        font_size: float = 16.0,
        display_mode: bool = False,
        **kwargs: Any,
    ) -> None:
        """Create a LaTeX formula widget.

        Args:
            parts: List of LaTeX strings to render. Parts are rendered sequentially
                and can be chained together. Use empty strings for spacing.
            font_size: Font size in pixels for the formula.
            display_mode: If True, renders as a block (centered, larger spacing).
                If False, renders inline.
            **kwargs: Forwarded to ``anywidget.AnyWidget``.
        """
        if parts is None:
            parts = [""]

        super().__init__(
            parts=parts,
            font_size=font_size,
            display_mode=display_mode,
            **kwargs,
        )

    def add_part(self, part: str) -> None:
        """Add a new part to the formula.

        Args:
            part: LaTeX string to add.
        """
        current_parts = list(self.parts)
        current_parts.append(part)
        self.parts = current_parts

    def set_parts(self, parts: List[str]) -> None:
        """Replace all parts with a new list.

        Args:
            parts: New list of LaTeX strings.
        """
        self.parts = parts
