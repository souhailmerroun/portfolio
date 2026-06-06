"""Run a compiled browser recipe (a learned, verified flow) in one call.

Recipes live in tools/recipes/<site>/<action>.py, each exposing run(**params)
that builds a pw_act step-list. They are intentionally NOT registered as MCP
tools (tools/recipes is excluded from enabled_categories), so they cost zero
schema tokens — this single dispatcher is the only entry point.

Usage:
    pw_recipe(catalog=True)                              -> list available recipes
    pw_recipe(name="the_internet/login")                 -> run it
    pw_recipe(name="x_com/post", params={"text": "hi"},
              allow_mutations=True)                       -> run a state-changing recipe
"""
import importlib
import os

_RECIPES_PKG = "tools.recipes"
_RECIPES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "recipes"))


def _catalog():
    out = []
    if not os.path.isdir(_RECIPES_DIR):
        return out
    for root, dirs, files in os.walk(_RECIPES_DIR):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in sorted(files):
            if not f.endswith(".py") or f.startswith("_"):
                continue
            rel = os.path.relpath(os.path.join(root, f), _RECIPES_DIR)[:-3].replace(os.sep, "/")
            summary, mutates = "", False
            try:
                mod = importlib.import_module(_RECIPES_PKG + "." + rel.replace("/", "."))
                doc = (mod.__doc__ or "").strip().split("\n", 1)[0]
                summary = doc
                mutates = bool(getattr(mod, "MUTATES", False))
            except Exception as e:
                summary = f"(import error: {e})"
            out.append({"name": rel, "summary": summary, "mutates": mutates})
    return out


def pw_recipe(name: str = None, params: dict = None,
              catalog: bool = False, allow_mutations: bool = False) -> dict:
    """Run a compiled recipe by name, or list the catalog.

    Args:
        name: recipe path like "the_internet/login" (file tools/recipes/the_internet/login.py).
        params: kwargs passed to the recipe's run().
        catalog: if true (or name omitted), return the list of available recipes.
        allow_mutations: required to run a recipe whose module sets MUTATES = True.

    Returns:
        catalog -> { status, recipes: [{name, summary, mutates}] }
        run     -> the recipe's pw_act result ({ status, url, results: [...] }),
                   or { status: "error", error } if not found / blocked.
    """
    if catalog or not name:
        return {"status": "ok", "recipes": _catalog()}

    mod_name = _RECIPES_PKG + "." + name.strip("/").replace("/", ".")
    try:
        mod = importlib.import_module(mod_name)
    except Exception as e:
        return {"status": "error", "error": f"recipe '{name}' not found ({e})"}

    if getattr(mod, "MUTATES", False) and not allow_mutations:
        return {"status": "error",
                "error": f"recipe '{name}' changes real state; pass allow_mutations=true to run it"}

    run = getattr(mod, "run", None)
    if not callable(run):
        return {"status": "error", "error": f"recipe '{name}' has no run()"}

    try:
        return run(**(params or {}))
    except TypeError as e:
        return {"status": "error", "error": f"bad params for '{name}': {e}"}
    except Exception as e:
        return {"status": "error", "error": f"recipe '{name}' failed: {e}"}
