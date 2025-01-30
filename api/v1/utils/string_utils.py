#!/usr/bin/env python3
"""
Text Formatting Utility

This module provides a function to clean and format text into a
properly capitalized title while removing unwanted characters.
It ensures numbers appear only at the end and filters out invalid values
like 'none' or 'null'.
"""
from typing import Optional
import re


def format_text_to_title(text: str) -> Optional[str]:
    """
    Cleans and formats text into a title-like structure.

    - Removes leading non-letter characters.
    - Eliminates numbers within words but allows them at the end.
    - Strips punctuation except spaces and numbers at valid positions.
    - Normalizes spaces and capitalizes each word.
    - Returns None if the result is 'none' or 'null'.

    Args:
        text (str): The input text to format.

    Returns:
        str | None: The formatted text or None if invalid.
    """
    if text:
        # Remove all non-letter characters at the beginning
        cleaned_text = re.sub(r'^[^a-zA-Z]+', '', text)

        # Remove all non-letter characters between or within letters
        cleaned_text = re.sub(r'(?<=[a-zA-Z])\d+(?=[a-zA-Z])',
                              '', cleaned_text)

        # Remove all punctuation, but allow numbers and spaces between words
        cleaned_text = re.sub(r'[^a-zA-Z0-9 ]+', '', cleaned_text)

        # Ensure numbers, if present, only appear at the end after the letters
        # Ensure there's a space before numbers, if needed
        cleaned_text = re.sub(r'(\d+)(?=\S)', r' \1', cleaned_text)

        # Normalize multiple spaces to a single space and strip
        # any leading/trailing spaces
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        # Ensure numbers only come after the letters at the end
        cleaned_text = re.sub(r'([a-zA-Z]+)(\d+)', r'\1 \2', cleaned_text)

        # Remove any numbers that appear between or within the words
        cleaned_text = re.sub(r'(?<=\D)\d+(?=\D)', '', cleaned_text)

        # Ensure there's only one space between the words and numbers
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        # Capitalize the first letter of each word
        formatted_text = cleaned_text.title().strip()

        # Check if the formatted_text contains only 'none' or
        # 'null' (and not part of another word)
        # Match when there are no other letters except for 'none' or 'null'
        if re.fullmatch(r'(none|null)( \d+)?', formatted_text.lower()):
            return None

        return formatted_text
    return None
