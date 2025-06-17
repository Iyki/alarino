import os

from pathlib import Path
from typing import Optional, Union, List

# Define paths to look for static files
def get_static_file_paths() -> List[Path]:
    """Returns ordered list of paths to check for static files"""
    base = Path(__file__).resolve().parent
    return [
        (base / "../static").resolve(),
        (base / "../data").resolve(),
        base,
        (base / "../../alarino_frontend").resolve(),
    ]

def find_file(filename: str, get_dir: bool = False,
              recursive: bool = True, paths: Optional[List[Path]] = None) -> Optional[Union[str, Path]]:
    """Search for a file in multiple directories, optionally recursively"""
    if paths is None:
        paths = get_static_file_paths()

    for path in paths:
        if recursive:
            # Walk through subdirectories
            matches = list(path.rglob(filename))
        else:
            # Only search top-level of each base path
            matches = list(path.glob(filename))

        if matches:
            return matches[0].parent if get_dir else matches[0]
    return None

