import os
import sys
import threading
import time

from fastmcp import FastMCP
from tools_registry import get_all_tools


def create_server(name: str, server_file: str) -> FastMCP:
    """
    Create a FastMCP server, register all tools, and start the file watcher.
    Pass __file__ from the calling server.py as server_file.
    """
    os.environ["PYTHONPYCACHEPREFIX"] = os.path.join(os.path.dirname(server_file), ".pycache")

    server_dir = os.path.dirname(os.path.abspath(server_file))

    # Ensure the server's own directory is on sys.path so that
    # `import tools.*` resolves correctly via importlib.
    if server_dir not in sys.path:
        sys.path.insert(0, server_dir)
    mcp = FastMCP(name)

    for tool in get_all_tools(server_dir):
        mcp.tool(tool)

    _start_watcher(server_file, server_dir)

    return mcp


def _start_watcher(server_file: str, tools_dir_root: str):
    """Watch for new .py files and touch server_file to trigger mcp-hmr reload."""
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler

    _server = os.path.abspath(server_file)
    _tools_dir = os.path.join(tools_dir_root, "tools")
    _known = {f for _, _, files in os.walk(_tools_dir) for f in files if f.endswith(".py")}

    class NewFileHandler(FileSystemEventHandler):
        def on_created(self, event):
            if not event.is_directory and event.src_path.endswith(".py"):
                fname = os.path.basename(event.src_path)
                if fname not in _known and not fname.startswith("_"):
                    _known.add(fname)
                    time.sleep(0.5)
                    os.utime(_server, None)

    observer = Observer()
    observer.schedule(NewFileHandler(), _tools_dir, recursive=True)
    observer.start()

    threading.Thread(target=lambda: None, daemon=True).start()
