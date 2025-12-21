import re

def get_main_artist(artist: str) -> str:
    if not artist:
        return "Inconnu"

    original = artist.strip()

    # version minuscule pour la détection
    lower = original.lower()

    # séparateurs possibles (ordre important)
    separators = [
        r"\s+ft\.?\s+",
        r"\s+feat\.?\s+",
        r"\s+featuring\s+",
        r"\s*,\s*",
        r"\s*;\s*",
    ]

    for sep in separators:
        match = re.search(sep, lower)
        if match:
            return original[:match.start()].strip()

    return original

def valid_filename(filename: str) -> str:
    return "".join(c for c in filename if c.isalnum() or c.isspace()).removesuffix(" ")