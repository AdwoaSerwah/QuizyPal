#!/usr/bin/env python3
import re

def format_text_to_title(text: str) -> str:
    """Removes unwanted characters and capitalizes each word"""
    # Remove non-alphabetic characters from the ends
    cleaned_text = re.sub(
        r'^[\s!"#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~]+|[\s!"#$%&\'()*+,\-./:;<=>?@\[\\\]^_`{|}~]+$',
        '', text)
    # Capitalize the first letter of each word
    formatted_text = cleaned_text.title().strip()

    print(formatted_text)
    return formatted_text
