import re


def extract_pax(text):
    match = re.search(r"(\d+)\s*pax", text.lower())
    if match:
        return int(match.group(1))
    return 1
