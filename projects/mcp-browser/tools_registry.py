import importlib
import inspect
import json
import os


def get_all_tools(server_dir: str):
    """
    Auto-discover all tool functions from the tools/, web_apps/, and web_apis/
    directories next to server_dir. The web_apps/ root mirrors the layout of
    the actual web_apps repo so a tool that just points back at a web app can
    live next to its sibling apps in the tree (e.g.
    web_apps/wellbeing/habits/habits.py). The web_apis/ root holds direct
    third-party HTTP API clients grouped by service (e.g. web_apis/slack/).

    Skips disabled.* dirs/files and __pycache__.
    Optionally filters by enabled_categories in tools_config.json.
    """
    config_path = os.path.join(server_dir, "tools_config.json")

    # Load optional category filter
    enabled = None
    try:
        with open(config_path) as f:
            enabled = set(json.load(f).get("enabled_categories", []))
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    tools = []

    for root_name in ("tools", "web_apps", "web_apis"):
        root_dir = os.path.join(server_dir, root_name)
        if not os.path.isdir(root_dir):
            continue

        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d != "__pycache__" and not d.startswith("disabled.")]

            for filename in sorted(files):
                if not filename.endswith(".py") or filename.startswith("_") or filename.startswith("disabled."):
                    continue

                filepath = os.path.join(root, filename)
                rel_path = os.path.relpath(filepath, server_dir)
                module_path = rel_path.replace(os.sep, ".").removesuffix(".py")

                # Category = first folder under the root (tools/ or web_apps/)
                parts = rel_path.split(os.sep)
                if len(parts) < 3:
                    continue
                category = parts[1]

                if enabled is not None and category not in enabled:
                    continue

                try:
                    if module_path in importlib.sys.modules:
                        module = importlib.reload(importlib.sys.modules[module_path])
                    else:
                        module = importlib.import_module(module_path)
                except Exception as e:
                    print(f"Warning: Failed to import {module_path}: {e}")
                    continue

                for name, obj in inspect.getmembers(module, inspect.isfunction):
                    if not name.startswith("_") and obj.__module__ == module.__name__:
                        tools.append(obj)

    return tools
