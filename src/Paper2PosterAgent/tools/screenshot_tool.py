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
Tool for capturing full-page screenshots of web pages using Playwright
Supports both local HTML files and remote URLs
"""

import os
from typing import Dict, Any, List, Optional

# Check dependencies
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


def screenshot_tool(
    html_path_or_url: str,
    output_path: str,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    full_page: bool = True,
    wait_time: int = 1000,
    **kwargs
) -> Dict[str, Any]:
    """
    Capture full-page screenshot of a web page.

    Args:
        html_path_or_url: HTML file path or URL
        output_path: Output screenshot path (supports .png, .jpg, .jpeg)
        viewport_width: Viewport width (default 1920)
        viewport_height: Viewport height (default 1080)
        full_page: Whether to capture the full page (default True)
        wait_time: Page load wait time in milliseconds (default 1000)
        **kwargs: Other parameters

    Returns:
        Dict[str, Any]: Contains the following fields:
            - status: "success" or "error"
            - message: Operation result description
            - output_path: Output screenshot file path (on success)
            - input: Input HTML path or URL (on success)
            - error: Error message (on failure)
    """
    # Check dependencies
    if not PLAYWRIGHT_AVAILABLE:
        return {
            "status": "error",
            "error": "Missing dependency: playwright. Please install using: pip install playwright && playwright install"
        }

    try:
        # Execute screenshot
        result_path = _capture_full_page_screenshot(
            html_path_or_url,
            output_path,
            viewport_width,
            viewport_height,
            full_page,
            wait_time
        )

        return {
            "status": "success",
            "message": "Web page screenshot completed",
            "output_path": result_path,
            "input": html_path_or_url
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Screenshot failed: {str(e)}"
        }


def _capture_full_page_screenshot(
    html_path_or_url: str,
    output_path: str,
    viewport_width: int = 1920,
    viewport_height: int = 1080,
    full_page: bool = True,
    wait_time: int = 1000
) -> str:
    """
    Capture full-page screenshot of a web page

    Returns:
        str: Absolute path of the screenshot file
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Determine if it's a local file or URL
    if os.path.isfile(html_path_or_url):
        # Local file, convert to file:// URL
        absolute_path = os.path.abspath(html_path_or_url)
        url = f"file://{absolute_path}"
    else:
        # Assume it's a URL
        url = html_path_or_url

    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)

        # Create context and page
        context = browser.new_context(
            viewport={"width": viewport_width, "height": viewport_height}
        )
        page = context.new_page()

        try:
            # Visit page
            page.goto(url, wait_until="networkidle")

            # Wait additional time to ensure all content is loaded
            page.wait_for_timeout(wait_time)

            # Take screenshot
            page.screenshot(path=output_path, full_page=full_page)

            # Get absolute path
            absolute_output_path = os.path.abspath(output_path)

            return absolute_output_path

        finally:
            # Close browser
            browser.close()


def batch_screenshot(
    html_files: List[str],
    output_dir: str,
    viewport_width: int = 1920,
    viewport_height: int = 1080
) -> Dict[str, Any]:
    """
    Batch screenshot multiple web pages.

    Args:
        html_files: List of HTML file paths or URLs
        output_dir: Output directory
        viewport_width: Viewport width
        viewport_height: Viewport height

    Returns:
        Dict[str, Any]: Contains the following fields:
            - status: "success" or "error"
            - message: Operation result description
            - results: Screenshot results list (on success)
            - total: Total count (on success)
            - success_count: Success count (on success)
            - failed_count: Failure count (on success)
            - error: Error message (on failure)
    """
    if not PLAYWRIGHT_AVAILABLE:
        return {
            "status": "error",
            "error": "Missing dependency: playwright. Please install using: pip install playwright && playwright install"
        }

    try:
        os.makedirs(output_dir, exist_ok=True)
        results = []
        success_count = 0
        failed_count = 0

        for html_file in html_files:
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(html_file))[0]
            output_path = os.path.join(output_dir, f"{base_name}.png")

            try:
                result_path = _capture_full_page_screenshot(
                    html_file,
                    output_path,
                    viewport_width,
                    viewport_height
                )
                results.append({"input": html_file, "output": result_path, "status": "success"})
                success_count += 1
            except Exception as e:
                results.append({"input": html_file, "error": str(e), "status": "error"})
                failed_count += 1

        return {
            "status": "success",
            "message": f"Batch screenshot completed, successful: {success_count}/{len(html_files)}",
            "results": results,
            "total": len(html_files),
            "success_count": success_count,
            "failed_count": failed_count
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Batch screenshot failed: {str(e)}"
        }
