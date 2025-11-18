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
HTML poster generation tool
Generates academic poster HTML based on Markdown content and image caption information
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

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


# Configuration
AVAILABLE_HEIGHT_PER_COLUMN = int(os.getenv("AVAILABLE_HEIGHT_PER_COLUMN") or "1000")
REFERENCE_KEYWORDS = ['reference', 'references', '参考文献', 'bibliography']


def poster_tool(
    md_file_path: str,
    image_caption_json_path: str,
    qr_code_path: str = "",
    logo_list: List[str] = None,
    output_path: str = "",
    prompt_template_path: str = "",
    **kwargs
) -> Dict[str, Any]:
    """
    Generate academic poster HTML based on Markdown content and image caption information.

    Args:
        md_file_path: Markdown file path
        image_caption_json_path: Image caption JSON file path
        qr_code_path: QR code image path (optional)
        logo_list: Institution logo image path list (optional)
        output_path: Output HTML file path (optional, defaults to poster.html in md file directory)
        prompt_template_path: Prompt template file path (optional)
        **kwargs: Other parameters

    Returns:
        Dict[str, Any]: Contains the following fields:
            - status: "success" or "error"
            - message: Operation result description
            - output_path: Output HTML file path (on success)
            - md_file_path: Input Markdown file path (on success)
            - image_caption_json_path: Image caption JSON path (on success)
            - qr_code_path: QR code path (on success, if provided)
            - logo_list: Logo list (on success, if provided)
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
        if not os.path.exists(md_file_path):
            return {
                "status": "error",
                "error": f"Markdown file not found: {md_file_path}"
            }

        if not os.path.exists(image_caption_json_path):
            return {
                "status": "error",
                "error": f"Image caption JSON file not found: {image_caption_json_path}"
            }

        # Verify QR code file (if provided)
        if qr_code_path and not os.path.exists(qr_code_path):
            return {
                "status": "error",
                "error": f"QR code file not found: {qr_code_path}"
            }

        # Verify Logo files (if provided)
        if logo_list:
            for logo_path in logo_list:
                if not os.path.exists(logo_path):
                    return {
                        "status": "error",
                        "error": f"Logo file not found: {logo_path}"
                    }

        # Execute poster generation
        result_path = _generate_and_save_poster(
            md_file_path,
            image_caption_json_path,
            qr_code_path,
            logo_list,
            output_path,
            prompt_template_path
        )

        return {
            "status": "success",
            "message": f"HTML poster generated successfully",
            "output_path": str(result_path),
            "md_file_path": md_file_path,
            "image_caption_json_path": image_caption_json_path,
            "qr_code_path": qr_code_path if qr_code_path else None,
            "logo_list": logo_list if logo_list else None
        }
    except FileNotFoundError as e:
        return {
            "status": "error",
            "error": f"File not found: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Poster generation failed: {str(e)}"
        }


def _read_file(file_path: str) -> str:
    """Read file content"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


def _save_file(file_path: str, content: str) -> None:
    """Save file content"""
    os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


def _find_reference_section(lines: List[str]) -> Optional[int]:
    """Find the starting position of the Reference section"""
    for i, line in enumerate(lines):
        line_stripped = line.strip().lower()
        if line_stripped.startswith('#'):
            title = re.sub(r'^#+\s*', '', line_stripped)
            for keyword in REFERENCE_KEYWORDS:
                if title == keyword or title.startswith(keyword):
                    return i
    return None


def _extract_html(content: str) -> str:
    """Extract HTML code from API returned content"""
    pattern1 = r'```html\s*(.*?)\s*```'
    pattern2 = r'```\s*(.*?)\s*```'

    match = re.search(pattern1, content, re.DOTALL)
    if match:
        return match.group(1).strip()

    match = re.search(pattern2, content, re.DOTALL)
    if match:
        return match.group(1).strip()

    return content.strip()


def _generate_html(markdown_content: str, image_caption_data: List[Dict],
                  prompt_template: str, available_height_per_column: int,
                  qr_code_path: str = "", logo_list: List[str] = None) -> str:
    """Generate HTML using OpenAI API"""
    # Build image information string
    image_info_str = ""
    if image_caption_data:
        image_info_str = "\n\n**Image Information:**\n"
        for img in image_caption_data:
            image_info_str += f"- Image path: {img.get('path', '')}\n"
            image_info_str += f"- Pixel size: {img.get('pixel_size', '')}\n"
            image_info_str += f"- Section: {img.get('section', '')}\n"
            image_info_str += f"- Generated title: {img.get('generated_title', '')}\n"
            image_info_str += f"- Detailed description: {img.get('description', '')}\n\n"

    # Add institution logo information
    if logo_list:
        image_info_str += "\n\n**Institution Logo Information:**\n"
        image_info_str += f"- Logo count: {len(logo_list)}\n"
        for idx, logo_path in enumerate(logo_list, 1):
            image_info_str += f"- Logo {idx} path: {logo_path}\n"
        image_info_str += "- Please arrange these institution logos horizontally at the top or bottom of the poster in an appropriate position\n\n"

    # Add QR code information
    if qr_code_path:
        image_info_str += "\n\n**QR Code Information:**\n"
        image_info_str += f"- QR code path: {qr_code_path}\n"
        image_info_str += "- Please place this QR code at an appropriate position on the poster (e.g., bottom right corner)\n\n"

    # Replace template variables
    prompt = prompt_template.replace("{{markdown}}", markdown_content + image_info_str)
    prompt = prompt.replace("{{available_height_per_column}}", str(available_height_per_column))

    # Get environment variables
    LLM_MODEL = os.getenv("LLM_MODEL")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL")
    LLM_API_KEY = os.getenv("LLM_API_KEY")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE") or "0.7")

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
        timeout=3000,
    )

    # Get API returned content
    raw_content = response.choices[0].message.content

    # Extract HTML content
    html_content = _extract_html(raw_content)

    return html_content


def _generate_and_save_poster(md_file_path: str, image_caption_json_path: str,
                             qr_code_path: str = "", logo_list: List[str] = None,
                             output_html_path: str = "", prompt_template_path: str = "") -> str:
    """Main function for generating and saving HTML poster"""

    # Read markdown file
    markdown_content = _read_file(md_file_path)
    lines = markdown_content.split('\n')

    # Find Reference section position
    reference_line_idx = _find_reference_section(lines)
    if reference_line_idx is not None:
        markdown_content = '\n'.join(lines[:reference_line_idx])

    # Read image caption data
    with open(image_caption_json_path, 'r', encoding='utf-8') as f:
        image_caption_data = json.load(f)

    # Read prompt template
    if not prompt_template_path:
        # Use default prompt template path
        prompt_template_path = Path(__file__).parent / "prompts" / "poster_prompt.md"
        if not prompt_template_path.exists():
            # If default template doesn't exist, use environment variable
            prompt_template_path = os.getenv("PROMPT_TEMPLATE_PATH", "")
            if not prompt_template_path or not os.path.exists(prompt_template_path):
                raise FileNotFoundError("Prompt template file not found, please set PROMPT_TEMPLATE_PATH environment variable or provide prompt_template_path parameter")

    prompt_template = _read_file(str(prompt_template_path))

    # Generate HTML
    html_content = _generate_html(markdown_content, image_caption_data,
                                 prompt_template, AVAILABLE_HEIGHT_PER_COLUMN,
                                 qr_code_path, logo_list)

    # Save HTML file
    if output_html_path:
        output_path = Path(output_html_path)
    else:
        output_path = Path(md_file_path).parent / "poster.html"

    _save_file(str(output_path), html_content)

    return str(output_path)
