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
Interactive Python executor tool for stateful code execution
Maintains persistent execution context across multiple calls
"""

import io
import traceback
import contextlib
from typing import Dict, Any

# Global execution context: all variables are preserved here
_GLOBAL_CONTEXT = {
    "__builtins__": __builtins__,  # Allow basic built-in functions
}


def interactive_python_executor(code: str, reset: bool = False) -> Dict[str, Any]:
    """
    Execute Python code in a persistent context, returning execution results.

    Args:
        code: Python code to execute
        reset: Whether to reset the execution environment (default: False)

    Returns:
        Dict[str, Any]: Contains the following fields:
            - ok: True if execution succeeded, False otherwise
            - stdout: Captured standard output
            - error: Error message and traceback (None if successful)
    """
    global _GLOBAL_CONTEXT

    # Reset context if requested
    if reset:
        _GLOBAL_CONTEXT = {
            "__builtins__": __builtins__,
        }

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            exec(code, _GLOBAL_CONTEXT)
            return {
                "ok": True,
                "stdout": buf.getvalue(),
                "error": None
            }
        except Exception:
            return {
                "ok": False,
                "stdout": buf.getvalue(),
                "error": traceback.format_exc()
            }
