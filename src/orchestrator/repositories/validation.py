"""Input validation utilities for repository operations.

This module provides validation functions for repository inputs to prevent
invalid data from reaching the database layer.
"""


def validate_id(
    id_value: str,
    field_name: str = "id",
    max_length: int = 64,
) -> str:
    """Validate an ID string.

    Args:
        id_value: The ID value to validate.
        field_name: Name of the field for error messages.
        max_length: Maximum allowed length for the ID.

    Returns:
        The validated ID value.

    Raises:
        ValueError: If the ID is empty or exceeds max_length.
        TypeError: If the ID is not a string.
    """
    if not isinstance(id_value, str):
        raise TypeError(f"{field_name} must be a string, got {type(id_value).__name__}")
    if not id_value:
        raise ValueError(f"{field_name} cannot be empty")
    if len(id_value) > max_length:
        raise ValueError(
            f"{field_name} exceeds maximum length of {max_length} characters"
        )
    return id_value
