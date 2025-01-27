#!/usr/bin/env python3
import re

def format_text_to_title(text: str) -> str:
    """Removes unwanted characters and capitalizes each word"""
    if text:
        # Remove all non-letter characters at the beginning
        cleaned_text = re.sub(r'^[^a-zA-Z]+', '', text)

        # Remove all non-letter characters (including numbers) between or within letters
        cleaned_text = re.sub(r'(?<=[a-zA-Z])\d+(?=[a-zA-Z])', '', cleaned_text)

        # Remove all punctuation, but allow numbers and spaces between words
        cleaned_text = re.sub(r'[^a-zA-Z0-9 ]+', '', cleaned_text)

        # Ensure numbers, if present, only appear at the end (after the letters)
        cleaned_text = re.sub(r'(\d+)(?=\S)', r' \1', cleaned_text)  # Ensure there's a space before numbers, if needed

        # Normalize multiple spaces to a single space and strip any leading/trailing spaces
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        # Ensure numbers only come after the letters at the end
        cleaned_text = re.sub(r'([a-zA-Z]+)(\d+)', r'\1 \2', cleaned_text)

        # Remove any numbers that appear between or within the words
        cleaned_text = re.sub(r'(?<=\D)\d+(?=\D)', '', cleaned_text)  # Remove numbers between letters

        # Ensure there's only one space between the words and numbers
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

        # Capitalize the first letter of each word
        formatted_text = cleaned_text.title().strip()

        # Check if the formatted_text contains only 'none' or 'null' (and not part of another word)
        # Match when there are no other letters except for 'none' or 'null'
        if re.fullmatch(r'(none|null)( \d+)?', formatted_text.lower()):
            return None

        return formatted_text
    return None
