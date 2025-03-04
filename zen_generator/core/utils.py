from __future__ import annotations

import importlib


def import_string(dotted_path: str) -> type:
    try:
        module_path, class_name = dotted_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        raise ImportError(f"Could not import '{dotted_path}'. {e.__class__.__name__}: {e}")
