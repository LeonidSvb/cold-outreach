#!/usr/bin/env python3
"""
Universal column selector component
"""

import streamlit as st
from typing import List, Optional


def render_column_selector(
    columns: List[str],
    label: str = "Select columns",
    multiselect: bool = True,
    default_selection: Optional[List[str]] = None,
    help_text: Optional[str] = None,
    key_prefix: str = "col_selector"
) -> List[str]:
    """
    Universal column selector.

    Args:
        columns: List of available columns
        label: Selector label
        multiselect: If True, allows multiple selections
        default_selection: Default selected columns
        help_text: Help text to display
        key_prefix: Unique key prefix

    Returns:
        List of selected column names (or single item if multiselect=False)
    """
    if not columns:
        st.warning("No columns available")
        return []

    if multiselect:
        selected = st.multiselect(
            label,
            options=columns,
            default=default_selection or [],
            help=help_text,
            key=f"{key_prefix}_multi"
        )
        return selected
    else:
        selected = st.selectbox(
            label,
            options=columns,
            index=0 if not default_selection else (
                columns.index(default_selection[0])
                if default_selection[0] in columns
                else 0
            ),
            help=help_text,
            key=f"{key_prefix}_single"
        )
        return [selected] if selected else []


def render_column_mapper(
    columns: List[str],
    required_fields: dict,
    key_prefix: str = "col_mapper"
) -> dict:
    """
    Map DataFrame columns to required fields.

    Args:
        columns: Available columns
        required_fields: Dict of {field_name: description}
        key_prefix: Unique key prefix

    Returns:
        Dict of {field_name: selected_column}
    """
    st.subheader("Column Mapping")

    mapping = {}

    for field_name, description in required_fields.items():
        # Auto-detect column
        auto_detected = None
        field_lower = field_name.lower()

        for col in columns:
            if field_lower in col.lower():
                auto_detected = col
                break

        selected = st.selectbox(
            f"{field_name}",
            options=["-- Not mapped --"] + columns,
            index=columns.index(auto_detected) + 1 if auto_detected else 0,
            help=description,
            key=f"{key_prefix}_{field_name}"
        )

        if selected != "-- Not mapped --":
            mapping[field_name] = selected

    return mapping
