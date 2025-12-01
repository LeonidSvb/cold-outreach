"""
CSV Normalizer - Atomic module for applying normalization to DataFrames
"""
import pandas as pd
from typing import Literal
from .csv_cleaner import clean_email, clean_website_to_domain, clean_generic


KeyType = Literal['email', 'website', 'generic']


def normalize_key_column(
    df: pd.DataFrame,
    key_column: str,
    key_type: KeyType = 'email'
) -> pd.DataFrame:
    """
    Normalize key column in DataFrame based on type

    Args:
        df: Input DataFrame
        key_column: Column name to normalize
        key_type: Type of normalization ('email', 'website', 'generic')

    Returns:
        DataFrame with normalized key column
    """
    if key_column not in df.columns:
        raise ValueError(f"Column '{key_column}' not found in DataFrame")

    df = df.copy()

    # Apply appropriate cleaning function
    if key_type == 'email':
        df[key_column] = df[key_column].apply(clean_email)
    elif key_type == 'website':
        df[key_column] = df[key_column].apply(clean_website_to_domain)
    else:
        df[key_column] = df[key_column].apply(clean_generic)

    # Remove rows with null keys after cleaning
    df = df[df[key_column].notna()]

    return df


def deduplicate_by_key(df: pd.DataFrame, key_column: str) -> pd.DataFrame:
    """
    Remove duplicate rows based on key column

    Args:
        df: Input DataFrame
        key_column: Column to use for deduplication

    Returns:
        DataFrame with duplicates removed (keeps last occurrence)
    """
    return df.drop_duplicates(subset=[key_column], keep='last')
