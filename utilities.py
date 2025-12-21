import re
import os
import shutil

from tinytag import TinyTag


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
    return "".join(c for c in filename if c.isalnum() or c.isspace() or c == ".").removesuffix(" ")


def trie(directory: str, file: TinyTag, sorter: str, errors: list[str]):
    try:
        if not os.path.exists(directory + "/" + valid_filename(sorter)):
            os.mkdir(directory + "/" + valid_filename(sorter))
        if not os.path.exists(directory + "/" + valid_filename(sorter) + "/" + file.filename):
            shutil.move(file.filename, directory + "/" + valid_filename(sorter) + "/")
        else:
            errors.append(
                f"Il existe déjà un fichier du même nom dans le dossier de destination pour {file.filename}")
    except FileNotFoundError:
        if not os.path.exists(directory + "/" + valid_filename(sorter) + "/" + file.filename):
            errors.append(f"Le fichier suivant n'existe pas : {file.filename}")
    except shutil.Error:
        errors.append(
            f"Il existe déjà un fichier du même nom dans le dossier de destination pour {file.filename}")
    except PermissionError:
        errors.append(f"Permission non accordé ! Impossible de déplacer le fichier {file.filename}")
