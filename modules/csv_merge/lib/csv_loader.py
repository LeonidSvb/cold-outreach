"""
CSV Loader - Atomic module for reading CSV files
"""
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple


def load_csv(file_path: str, encoding: str = 'utf-8') -> pd.DataFrame:
    """
    Load single CSV file with automatic delimiter detection

    Args:
        file_path: Path to CSV file
        encoding: File encoding (default: utf-8)

    Returns:
        DataFrame with normalized column names
    """
    try:
        df = pd.read_csv(file_path, encoding=encoding)
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='latin1')

    # Normalize column names: lowercase, replace spaces with underscores
    df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')

    return df


def get_all_columns(dataframes: List[pd.DataFrame]) -> List[str]:
    """
    Get union of all column names from multiple DataFrames

    Args:
        dataframes: List of DataFrames

    Returns:
        Sorted list of unique column names
    """
    all_columns = set()
    for df in dataframes:
        all_columns.update(df.columns)

    return sorted(list(all_columns))


def detect_file_encoding(file_path: str) -> str:
    """
    Detect file encoding by attempting to read first few lines

    Args:
        file_path: Path to file

    Returns:
        Detected encoding ('utf-8' or 'latin1')
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read(1024)
        return 'utf-8'
    except UnicodeDecodeError:
        return 'latin1'
