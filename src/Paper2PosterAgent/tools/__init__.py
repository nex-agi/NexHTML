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

"""Custom tools for the NexAU framework.

This module contains custom tool implementations that are configured
via YAML files in the tools/ directory.
"""

from .paper2md_tool import pdf_to_markdown_tool
from .time_tool import get_current_time, format_time
from .logo_manager_tool import logo_manager_tool
from .gen_qr_code_tool import gen_qr_code_tool
from .height_detect_tool import height_detect_tool
from .image_caption_tool import image_caption_tool
from .layout_balance_tool import layout_balance_tool
from .poster_tool import poster_tool
from .screenshot_tool import screenshot_tool

__all__ = [
    "pdf_to_markdown_tool",
    "get_current_time",
    "format_time",
    "logo_manager_tool",
    "gen_qr_code_tool",
    "height_detect_tool",
    "image_caption_tool",
    "layout_balance_tool",
    "poster_tool",
    "screenshot_tool",
]
