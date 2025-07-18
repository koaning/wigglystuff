import pytest
import numpy as np
from wigglystuff import Matrix


def test_matrix_with_valid_matrix_and_limits():
    """Test that Matrix accepts valid matrix within limits."""
    test_matrix = [[1.0, 2.0], [3.0, 4.0]]
    matrix = Matrix(matrix=test_matrix, min_value=0, max_value=10)
    assert matrix.matrix == test_matrix
    assert matrix.min_value == 0
    assert matrix.max_value == 10


def test_matrix_with_invalid_matrix_below_min():
    """Test that Matrix raises ValueError when matrix values are below min_value."""
    test_matrix = [[1.0, 2.0], [3.0, 4.0]]
    with pytest.raises(ValueError, match="Matrix contains values below min_value=5"):
        Matrix(matrix=test_matrix, min_value=5)


def test_matrix_with_invalid_matrix_above_max():
    """Test that Matrix raises ValueError when matrix values are above max_value."""
    test_matrix = [[1.0, 2.0], [3.0, 15.0]]
    with pytest.raises(ValueError, match="Matrix contains values above max_value=10"):
        Matrix(matrix=test_matrix, max_value=10)
