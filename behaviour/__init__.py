import os

from resource_path import resource_path


def get_image_path(relative_path: str) -> str:
    """
    Build an absolute path to an image file.\n
    Args:
        relative_path: Path relative to the images directory (e.g. "apps/word.png")
    """
    return os.path.join(resource_path("images"), relative_path)
