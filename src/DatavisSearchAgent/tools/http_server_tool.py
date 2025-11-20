# Copyright (c) Nex-AGI. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
HTTP server tool for serving static files
Starts a non-blocking local HTTP server for dashboard display
"""

import os
import shlex
import socket
import subprocess
from typing import Any, Dict


def _is_port_open(port: int) -> bool:
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _find_available_port(start: int, max_tries: int = 10) -> int:
    """Find an available port starting from the given port number"""
    port = start
    tries = 0
    while tries < max_tries:
        if not _is_port_open(port):
            return port
        port += 1
        tries += 1
    return start  # fallback


def http_server(serve_dir: str, port: int = 8765) -> Dict[str, Any]:
    """
    Start a non-blocking HTTP server using UV: uv run python -m http.server {port} --directory {serve_dir}.
    Returns accessible URL and startup log. Paths are properly escaped and quoted. Port conflicts are auto-incremented.

    Args:
        serve_dir: Directory to serve (absolute path)
        port: Starting port number (default: 8765)

    Returns:
        Dict[str, Any]: Contains the following fields:
            - success: True if server started successfully, False otherwise
            - tool_name: "http_server"
            - url: Accessible URL (on success)
            - port: Actual port used (on success)
            - serve_dir: Directory being served (on success)
            - message: Success message (on success)
            - error: Error message (on failure)
            - error_type: Error type (on failure)
    """
    try:
        if not os.path.isdir(serve_dir):
            return {
                "success": False,
                "tool_name": "http_server",
                "error": f"Directory not found: {serve_dir}",
                "error_type": "FileNotFoundError"
            }

        # Find available port
        port = _find_available_port(port)
        quoted_dir = shlex.quote(serve_dir)
        cmd = f"uv run python -m http.server {port} --directory {quoted_dir}"

        # Start non-blocking background process
        proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        url = f"http://127.0.0.1:{port}/"

        return {
            "success": True,
            "tool_name": "http_server",
            "url": url,
            "message": "HTTP server started (non-blocking)",
            "port": port,
            "serve_dir": serve_dir
        }
    except Exception as e:
        return {
            "success": False,
            "tool_name": "http_server",
            "error": str(e),
            "error_type": type(e).__name__
        }
