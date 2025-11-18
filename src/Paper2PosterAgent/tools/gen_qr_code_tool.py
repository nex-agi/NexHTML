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
arXiv paper QR code generation tool
Extracts arXiv links from PDF first page screenshot and generates corresponding abs link QR codes
"""

import os
import base64
import json
import re
from typing import Dict, Any
from io import BytesIO

# Check dependencies
try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

try:
    import qrcode
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

try:
    from PIL import Image  # noqa: F401
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

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


# VLM configuration - loaded from environment variables
MODEL = os.getenv("ARXIV_JUDGE_MODEL")
BASE_URL = os.getenv("ARXIV_JUDGE_BASE_URL")
API_KEY = os.getenv("ARXIV_JUDGE_API_KEY")
MAX_TOKENS = int(os.getenv("ARXIV_JUDGE_MAX_TOKENS") or "8000")
TIMEOUT = int(os.getenv("ARXIV_JUDGE_TIMEOUT") or "1000")


def gen_qr_code_tool(
    pdf_path: str,
    output_path: str = "",
    api_key: str = "",
    api_base: str = "",
    **kwargs  # noqa: ARG001
) -> Dict[str, Any]:
    """
    Extract arXiv link from PDF first page and generate corresponding abs link QR code.

    Args:
        pdf_path: PDF file path
        output_path: QR code output path (optional, defaults to {pdf_name}_qr_code.png in same directory)
        api_key: OpenAI API key (optional, uses environment variable by default)
        api_base: OpenAI API base URL (optional, uses environment variable by default)
        **kwargs: Other parameters

    Returns:
        Dict[str, Any]: Contains the following fields:
            - status: "success" or "error"
            - message: Operation result description
            - arxiv_id: Extracted arXiv ID (on success)
            - abs_link: Generated arXiv abs link (on success)
            - qr_code_path: QR code file path (on success)
            - pdf_path: Input PDF path (on success)
            - error: Error message (on failure)
    """
    # Check dependencies
    missing_deps = []
    if not PDF2IMAGE_AVAILABLE:
        missing_deps.append("pdf2image")
    if not QRCODE_AVAILABLE:
        missing_deps.append("qrcode")
    if not PIL_AVAILABLE:
        missing_deps.append("Pillow")
    if not OPENAI_AVAILABLE:
        missing_deps.append("openai")

    if missing_deps:
        return {
            "status": "error",
            "error": f"Missing dependencies: {', '.join(missing_deps)}. Please install using: pip install {' '.join(missing_deps)}"
        }

    try:
        # Convert PDF path to absolute path
        pdf_path = os.path.abspath(pdf_path)

        # Verify PDF file exists
        if not os.path.exists(pdf_path):
            return {
                "status": "error",
                "error": f"PDF file not found: {pdf_path}"
            }

        # Set output path (ensure absolute path)
        if not output_path:
            pdf_dir = os.path.dirname(pdf_path)
            pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
            output_path = os.path.join(pdf_dir, f"{pdf_name}_qr_code.png")
        else:
            # User provided path, convert to absolute path
            output_path = os.path.abspath(output_path)

        # Step 1: Extract PDF first page as image
        first_page_image = _extract_first_page(pdf_path)

        # Step 2: Use AI model to analyze image and extract arXiv link
        arxiv_info = _extract_arxiv_link(first_page_image, api_key, api_base, output_path)

        if arxiv_info["status"] == "error":
            return arxiv_info

        arxiv_id = arxiv_info["arxiv_id"]
        abs_link = arxiv_info["abs_link"]

        # Step 3: Generate QR code
        qr_result = _generate_qr_code(abs_link, output_path)

        if qr_result["status"] == "error":
            return qr_result

        return {
            "status": "success",
            "message": "QR code generated successfully",
            "arxiv_id": arxiv_id,
            "abs_link": abs_link,
            "qr_code_path": output_path,
            "pdf_path": pdf_path
        }

    except Exception as e:
        return {
            "status": "error",
            "error": f"QR code generation failed: {str(e)}"
        }


def _extract_first_page(pdf_path: str) -> Any:
    """Extract PDF first page as image"""
    try:
        # Only convert first page, set high DPI for clear image
        images = convert_from_path(
            pdf_path,
            first_page=1,
            last_page=1,
            dpi=200
        )
        return images[0]
    except Exception as e:
        raise Exception(f"PDF page extraction failed: {str(e)}")


def _extract_arxiv_link(
    image: Any,
    api_key: str = "",
    api_base: str = "",
    output_path: str = ""
) -> Dict[str, Any]:
    """Use AI model to analyze image and extract arXiv link"""
    try:
        # Convert image to base64 encoding
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()

        # Initialize OpenAI client
        client = OpenAI(
            base_url=api_base or BASE_URL,
            api_key=api_key or API_KEY
        )

        # Build prompt
        prompt = """Please analyze this screenshot of a PDF first page and determine if it is an arXiv paper.
If it is an arXiv paper, please extract the arXiv ID (format like: 2301.12345).

arXiv papers usually contain the following format information on the left side of the first page:
- arXiv:2301.12345v1 [cs.AI] 1 Jan 2023
- arXiv:cs/0001234

Please return the result strictly in the following JSON format:
{
    "is_arxiv": true/false,
    "arxiv_id": "Extracted arxiv ID, e.g., 2301.12345",
}

If it is not an arXiv paper or the arXiv ID cannot be identified, please set is_arxiv to false."""

        # Call AI model
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{img_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=MAX_TOKENS,
            timeout=TIMEOUT
        )

        # Parse response
        result_text = response.choices[0].message.content.strip()

        # Try to find JSON block
        json_match = re.search(r'\{[^}]+\}', result_text, re.DOTALL)
        if json_match:
            result_json = json.loads(json_match.group())
        else:
            result_json = json.loads(result_text)

        if not result_json.get("is_arxiv", False):
            return {
                "status": "error",
                "error": f"Not identified as arXiv paper. Reason: {result_json.get('reason', 'Unknown')}"
            }

        arxiv_id = result_json.get("arxiv_id", "").strip()
        if not arxiv_id:
            return {
                "status": "error",
                "error": "Failed to extract arXiv ID"
            }

        # Clean arXiv ID (remove version number, etc.)
        arxiv_id = re.sub(r'v\d+$', '', arxiv_id)

        # Generate abs link
        abs_link = f"https://arxiv.org/abs/{arxiv_id}"

        return {
            "status": "success",
            "arxiv_id": arxiv_id,
            "abs_link": abs_link,
            "qr_code_path": output_path,
            "reason": result_json.get("reason", "")
        }

    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "error": f"AI response parsing failed: {str(e)}. Response content: {result_text if 'result_text' in locals() else 'N/A'}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"arXiv link extraction failed: {str(e)}",
            "debug_info": {
                "model": MODEL,
                "base_url": api_base or BASE_URL,
                "has_api_key": bool(api_key or API_KEY)
            }
        }


def _generate_qr_code(url: str, output_path: str) -> Dict[str, Any]:
    """Generate QR code"""
    try:
        # Create QR code
        qr = qrcode.QRCode(
            version=1,  # Auto adjust size
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Generate image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save image
        img.save(output_path)

        return {
            "status": "success",
            "output_path": output_path
        }

    except Exception as e:
        return {
            "status": "error",
            "error": f"QR code generation failed: {str(e)}"
        }
