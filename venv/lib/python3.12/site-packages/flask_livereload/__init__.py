"""
Flask-LiveReload
----------------

A Flask extension that provides live reloading of web pages when template or
static files change.
"""

import os
import queue
import logging
import atexit
import fnmatch
from typing import Optional, List
from flask import Flask
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)

# JavaScript to be injected into the browser
LIVERELOAD_SCRIPT = b"""
<script>
(function() {
    if (!window.EventSource) {
        console.warn("EventSource not supported, LiveReload disabled");
        return;
    }
    var source = new EventSource("/_livereload");
    source.onmessage = function(event) {
        if (event.data === "reload") {
            console.info("LiveReload: Reloading page...");
            window.location.reload();
        } else if (event.data === "connected") {
            console.info("LiveReload: Connected to server");
        }
    };
    source.onerror = function(event) {
        console.warn("LiveReload connection error:", event);
    };
    window.addEventListener('beforeunload', function() {
        if (source) {
            source.close();
        }
    });
})();
</script>
"""


class _ChangeHandler(FileSystemEventHandler):
    """Handles file system events and puts a 'reload' message in the queue."""

    def __init__(
        self,
        change_queue: queue.Queue,
        watch_patterns: List[str],
        ignore_patterns: List[str],
    ):
        super().__init__()
        self.change_queue = change_queue
        self.watch_patterns = watch_patterns
        self.ignore_patterns = ignore_patterns

    def _is_watched(self, path: str) -> bool:
        """Check if a file path matches the watch/ignore patterns."""
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(path, pattern):
                return False

        if not self.watch_patterns:
            return True

        for pattern in self.watch_patterns:
            if fnmatch.fnmatch(path, pattern):
                return True
        return False

    def _dispatch(self, event: FileSystemEvent):
        """Dispatch events to the queue if they match watched patterns."""
        if event.is_directory:
            return

        # For moved events, the destination path is what matters.
        path = event.src_path

        if self._is_watched(path):
            logger.info(
                f"File change detected ({event.event_type} on {path}), triggering reload."
            )
            self.change_queue.put("reload")
        else:
            logger.debug(f"Ignored file change ({event.event_type} on {path}).")

    def on_modified(self, event: FileSystemEvent):
        self._dispatch(event)

    def on_created(self, event: FileSystemEvent):
        self._dispatch(event)

    def on_moved(self, event: FileSystemEvent):
        self._dispatch(event)


class LiveReload:
    """
    This class controls the Flask-LiveReload extension.
    """

    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.change_queue: queue.Queue[str] = queue.Queue()
        self.observer = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initializes the extension with the given application."""
        if not app.debug:
            logger.info("Flask-LiveReload disabled: app not in debug mode.")
            return

        self.app = app
        app.config.setdefault("LIVERELOAD_WATCH_PATTERNS", ["*.html", "*.css", "*.js"])
        app.config.setdefault(
            "LIVERELOAD_IGNORE_PATTERNS",
            [
                "*/__pycache__/*",
                "*/.venv/*",
                "*/.git/*",
                "*/.pytest_cache/*",
                "*.pyc",
                "*.pyo",
                "*.log",
            ],
        )
        app.extensions["livereload"] = self

        from .views import livereload_bp

        app.register_blueprint(livereload_bp)

        app.after_request(self.inject_script)

        self.start_watcher()
        atexit.register(self.stop_watcher)

        logger.info("Flask-LiveReload initialized successfully.")

    def start_watcher(self):
        """Starts the file system observer."""
        if self.observer and self.observer.is_alive():
            return

        self.observer = Observer()
        watch_patterns = self.app.config["LIVERELOAD_WATCH_PATTERNS"]
        ignore_patterns = self.app.config["LIVERELOAD_IGNORE_PATTERNS"]

        handler = _ChangeHandler(self.change_queue, watch_patterns, ignore_patterns)

        paths_to_watch = set()
        if self.app.template_folder:
            paths_to_watch.add(os.path.abspath(self.app.template_folder))
        if self.app.static_folder:
            paths_to_watch.add(os.path.abspath(self.app.static_folder))

        logger.info(f"Watching paths: {list(paths_to_watch)}")
        logger.info(f"Watch patterns: {watch_patterns}")
        logger.info(f"Ignore patterns: {ignore_patterns}")

        for path in paths_to_watch:
            if os.path.exists(path):
                self.observer.schedule(handler, path, recursive=True)

        self.observer.start()

    def stop_watcher(self):
        """Stops the file system observer."""
        if self.observer and self.observer.is_alive():
            self.observer.stop()
            self.observer.join()
            logger.info("Flask-LiveReload watcher stopped.")

    def inject_script(self, response):
        """Injects the LiveReload script into HTML responses."""
        if response.status_code == 200 and response.content_type.startswith(
            "text/html"
        ):
            content = response.get_data(as_text=True)
            if "</body>" in content and "_livereload" not in content:
                body_tag = "</body>"
                script_tag = LIVERELOAD_SCRIPT.decode("utf-8")
                content = content.replace(body_tag, script_tag + body_tag)
                response.set_data(content)
                response.headers["Content-Length"] = len(response.get_data())
        return response
