#!/usr/bin/env python3
"""
Pagination Utility Module.

This module provides helper functions for paginating datasets, including
index calculations and data filtering.

Functions:
    - index_range: Computes start and end indexes for pagination.
    - get_paginated_data: Retrieves and paginates data while filtering
      unwanted entries.
"""
import math
from typing import List, Dict, Tuple


def index_range(page: int, page_size: int) -> Tuple[int, int]:
    """
    Returns a tuple containing a start index and an end index
    for a list, based on the given page and page_size.

    Args:
        page (int): The current page number (1-indexed).
        page_size (int): The number of items per page.

    Returns:
        Tuple[int, int]: A tuple (start_index, end_index).
    """
    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    return start_index, end_index


def get_paginated_data(storage, cls,
                       page: int = 1,
                       page_size: int = 10) -> List[Dict]:
    """
    Returns a dictionary containing hypermedia pagination details.

    Args:
        page (int): The current page number (1-indexed).
        page_size (int): The number of items per page.

    Returns:
        Dict: A dictionary with hypermedia pagination details.
    """
    # Determine start and end indexes using index_range
    start_index, end_index = index_range(page, page_size)

    # Get all data and convert it to a list
    dataset = list(storage.all(cls).values())

    # Filter out objects where 'choice_text' is 'no_answer'
    filtered_dataset = [
        item for item in dataset
        if not hasattr(item, 'choice_text') or item.choice_text != 'no_answer'
    ]

    # Slice the data
    end = min(end_index, len(filtered_dataset))

    sliced_data = [
        item.to_json()
        for item in filtered_dataset[start_index:end]
    ]

    # data = get_page(page, page_size)
    total_items = len(dataset)
    total_pages = math.ceil(total_items / page_size)

    return {
        "page_size": len(sliced_data),
        "page": page,
        "data": sliced_data,
        "next_page": page + 1 if page < total_pages else None,
        "prev_page": page - 1 if page > 1 else None,
        "total_pages": total_pages,
    }
