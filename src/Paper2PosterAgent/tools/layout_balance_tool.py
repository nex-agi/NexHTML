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
Poster layout balancing tool
Optimizes HTML poster layout based on three-column height information
"""

import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

# Check dependencies
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def layout_balance_tool(
    html_file_path: str,
    col_height_dict: Dict[str, str],
    markdown_file_path: str = "",
    output_path: str = "",
    **kwargs
) -> Dict[str, Any]:
    """
    Optimize HTML poster layout based on three-column height information.

    Args:
        html_file_path: HTML file path
        col_height_dict: Three-column height dictionary, containing height utilization of column_1, column_2, column_3
        markdown_file_path: Paper markdown file path (optional, for content expansion)
        output_path: Output HTML file path (optional, defaults to balanced_poster.html in same directory)
        **kwargs: Other parameters

    Returns:
        Dict[str, Any]: Contains the following fields:
            - status: "success" or "error"
            - message: Operation result description
            - output_path: Output HTML file path (on success)
            - input_html_path: Input HTML file path (on success)
            - markdown_path: Markdown file path (on success)
            - column_heights: Column height information (on success)
            - error: Error message (on failure)
    """
    # Check dependencies
    if not OPENAI_AVAILABLE:
        return {
            "status": "error",
            "error": "Missing dependency: openai. Please install using: pip install openai"
        }

    try:
        # Verify input files exist
        if not os.path.exists(html_file_path):
            return {
                "status": "error",
                "error": f"HTML file not found: {html_file_path}"
            }

        # Verify markdown file (if provided)
        if markdown_file_path and not os.path.exists(markdown_file_path):
            return {
                "status": "error",
                "error": f"Markdown file not found: {markdown_file_path}"
            }

        # Verify col_height_dict parameter
        if not col_height_dict:
            return {
                "status": "error",
                "error": "col_height_dict parameter cannot be empty"
            }

        # Execute layout balancing optimization
        result_path = _balance_poster_layout(
            html_file_path,
            col_height_dict,
            markdown_file_path,
            output_path
        )

        return {
            "status": "success",
            "message": "Poster layout balancing optimization completed",
            "output_path": result_path,
            "input_html_path": html_file_path,
            "markdown_path": markdown_file_path if markdown_file_path else "Not provided",
            "column_heights": col_height_dict
        }
    except FileNotFoundError as e:
        return {
            "status": "error",
            "error": f"File not found: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Layout balancing optimization failed: {str(e)}"
        }


def _read_file(file_path: str) -> str:
    """Read file content"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def _save_file(file_path: str, content: str) -> None:
    """Save file content"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def _extract_html(content: str) -> str:
    """Extract HTML code from API returned content"""
    # Try to match markdown code block format ```html...``` or ```...```
    pattern1 = r'```html\s*(.*?)\s*```'
    pattern2 = r'```\s*(.*?)\s*```'

    match = re.search(pattern1, content, re.DOTALL)
    if match:
        return match.group(1).strip()

    match = re.search(pattern2, content, re.DOTALL)
    if match:
        return match.group(1).strip()

    # If no code block marker, return original content directly
    return content.strip()


def _generate_html(html_content: str, col_height_dict: Dict, markdown_content: str, prompt_template: str) -> str:
    """Generate HTML using OpenAI API"""
    # Build image information string
    col_height_info_str = ""
    if col_height_dict:
        col_height_info_str = "\n\n**Column Height Information:**\n"
        for col in col_height_dict:
            col_height_info_str += f"- Column number: {col}\n"
            col_height_info_str += f"- Height utilization: {col_height_dict[col]}\n\n"

    # Replace placeholders with actual content
    prompt = prompt_template.replace("{{html_content}}", html_content)
    prompt = prompt.replace("{{col_height_info}}", col_height_info_str)
    prompt = prompt.replace("{{markdown_content}}", markdown_content if markdown_content else "(No paper markdown content provided)")

    # Get environment variables
    LLM_BASE_URL = os.getenv('LLM_BASE_URL')
    LLM_API_KEY = os.getenv('LLM_API_KEY')
    LLM_MODEL = os.getenv('LLM_MODEL')
    LLM_TEMPERATURE = float(os.getenv('LLM_TEMPERATURE') or '0.9')

    # Initialize OpenAI client
    client = OpenAI(
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY
    )

    # Call API
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=LLM_TEMPERATURE,
    )

    # Get API returned content
    raw_content = response.choices[0].message.content

    # Extract HTML content
    html_content = _extract_html(raw_content)

    return html_content


def _balance_poster_layout(
    html_file_path: str,
    col_height_dict: Dict,
    markdown_file_path: str = "",
    output_path: str = ""
) -> str:
    """
    Main function for generating and saving HTML poster

    Args:
        html_file_path: HTML file path
        col_height_dict: Three-column height dictionary
        markdown_file_path: Paper markdown file path (optional)
        output_path: Output path (optional)

    Returns:
        Modified HTML file path
    """
    # Step 1: Read HTML file
    html_content = _read_file(html_file_path)

    # Step 2: Read Markdown file (if provided)
    markdown_content = ""
    if markdown_file_path and os.path.exists(markdown_file_path):
        markdown_content = _read_file(markdown_file_path)

    # Step 3: Read prompt template
    prompt_template_path = Path(__file__).parent / "prompts" / "layout_balance.md"
    prompt_template = _read_file(str(prompt_template_path))

    # Step 4: Generate HTML
    html_content = _generate_html(html_content, col_height_dict, markdown_content, prompt_template)

    # Step 5: Save HTML file
    if not output_path:
        output_path = str(Path(html_file_path).parent / "balanced_poster_v2.html")

    _save_file(output_path, html_content)

    return output_path
