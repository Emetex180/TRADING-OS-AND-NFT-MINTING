import logging
import queue
import time

from flask import Blueprint, Response, current_app

logger = logging.getLogger(__name__)
livereload_bp = Blueprint("livereload", __name__)


@livereload_bp.route("/_livereload")
def sse():
    """Server-Sent Events endpoint to notify the client of changes."""
    change_queue = current_app.extensions["livereload"].change_queue

    def gen():
        try:
            yield "data: connected\n\n"
            while True:
                try:
                    message = change_queue.get(timeout=30)
                    time.sleep(0.2)
                    logger.debug(f"Sending SSE message: {message}")
                    yield f"data: {message}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        except GeneratorExit:

            logger.info("SSE connection closed by client.")
        except Exception as e:
            logger.error(f"Error in SSE stream: {e}")
            yield f"data: error\n\n"

    response = Response(gen(), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Connection"] = "keep-alive"
    return response
