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

"""PDF to Markdown tool implementation using paper2md API."""

import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


def fix_base64_padding(base64_string: str) -> str:
    """
    Fix base64 string padding issues and remove data URI prefix.

    Base64 strings must have length divisible by 4.
    This function:
    1. Removes data URI prefix (e.g., "data:image/jpeg;base64,")
    2. Adds necessary '=' padding characters

    Args:
        base64_string: Potentially malformed base64 string

    Returns:
        Properly padded base64 string
    """
    # Remove data URI prefix if present
    if ',' in base64_string and base64_string.startswith('data:'):
        base64_string = base64_string.split(',', 1)[1]

    # Remove any whitespace
    base64_string = base64_string.strip()

    # Calculate missing padding
    missing_padding = len(base64_string) % 4

    if missing_padding:
        # Add the required number of '=' characters
        base64_string += '=' * (4 - missing_padding)

    return base64_string


def pdf_to_markdown_tool(
    pdf_path: str,
    output_dir: Optional[str] = None,
    api_url: str = None,
    cleanup_uuid_folders: bool = True
) -> Dict[str, Any]:
    """
    Convert PDF file to Markdown format using paper2md API.

    This tool calls the paper2md HTTP API to convert academic papers from PDF to Markdown.
    It's particularly useful for extracting structured content from research papers.

    Args:
        pdf_path: Path to the PDF file (required)
        output_dir: Output directory for the markdown file. If not provided,
                   creates 'output' folder next to the PDF file.
        api_url: API endpoint URL. If not provided, reads from PAPER2MD_API_URL
                environment variable, or defaults to http://127.0.0.1:8010/file_parse
        cleanup_uuid_folders: Whether to remove UUID folders created by API (default: True)

    Returns:
        Dict containing:
        - status: 'success' or 'error'
        - message: Status message or error description
        - markdown_path: Path to the generated markdown file (on success), None on error
    """
    # Get API URL from parameter, environment variable, or use default
    if api_url is None:
        api_url = os.getenv('PAPER2MD_API_URL', 'http://127.0.0.1:8010/file_parse')

    try:
        # Convert to Path object
        pdf_path_obj = Path(pdf_path).resolve()

        # Validate PDF file
        if not pdf_path_obj.exists():
            return {
                "status": "error",
                "message": f"PDF file not found: {pdf_path}",
                "markdown_path": None
            }

        if not pdf_path_obj.is_file():
            return {
                "status": "error",
                "message": f"Path is not a file: {pdf_path}",
                "markdown_path": None
            }

        if pdf_path_obj.suffix.lower() != '.pdf':
            return {
                "status": "error",
                "message": f"File is not a PDF: {pdf_path}",
                "markdown_path": None
            }

        # Determine output directory
        if output_dir is None:
            # Output directly in the same directory as the PDF
            output_dir_obj = pdf_path_obj.parent
        else:
            output_dir_obj = Path(output_dir).resolve()

        # Create output directory (in case it doesn't exist)
        output_dir_obj.mkdir(parents=True, exist_ok=True)

        pdf_name = pdf_path_obj.stem
        md_file_path = output_dir_obj / f"{pdf_name}.md"

        logger.info(f"Converting PDF to Markdown: {pdf_path}")
        logger.info(f"Output directory: {output_dir_obj}")

        # Check if markdown already exists
        if md_file_path.exists():
            try:
                with open(md_file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Verify content is valid
                if len(content.strip()) >= 100:
                    logger.info(f"Using existing markdown file: {md_file_path}")

                    return {
                        "status": "success",
                        "message": "Using existing markdown file",
                        "markdown_path": str(md_file_path)
                    }
                else:
                    logger.warning(f"Existing markdown file is too small, regenerating")
            except Exception as e:
                logger.warning(f"Could not read existing markdown file: {e}")

        # Prepare API request data
        data = {
            'return_middle_json': 'false',
            'return_model_output': 'false',
            'return_md': 'true',
            'return_images': 'true',
            'end_page_id': '99999',
            'parse_method': 'auto',
            'start_page_id': '0',
            'lang_list': 'ch',
            'output_dir': str(output_dir_obj),
            'server_url': 'string',
            'return_content_list': 'false',
            'backend': 'pipeline',
            'table_enable': 'true',
            'response_format_zip': 'false',
            'formula_enable': 'true'
        }

        # Prepare file for upload
        logger.info(f"Calling API: {api_url}")

        with open(pdf_path_obj, 'rb') as pdf_file:
            files = {
                'files': (pdf_path_obj.name, pdf_file, 'application/pdf')
            }

            # Call API
            response = requests.post(
                api_url,
                data=data,
                files=files,
                headers={'accept': 'application/json'},
                timeout=300  # 5 minutes timeout
            )

        # Check response status
        if response.status_code != 200:
            error_msg = f"API call failed with status {response.status_code}"
            logger.error(f"{error_msg}: {response.text}")
            return {
                "status": "error",
                "message": error_msg,
                "markdown_path": None
            }

        # Parse response
        result = response.json()
        backend = result.get('backend', 'N/A')
        version = result.get('version', 'N/A')

        logger.info(f"API response received - Backend: {backend}, Version: {version}")

        # Debug: log response structure
        logger.debug(f"API response keys: {list(result.keys())}")
        if 'results' in result:
            logger.debug(f"Results keys: {list(result['results'].keys())}")

        # Extract markdown content
        results = result.get('results', {})
        if not results:
            return {
                "status": "error",
                "message": "API response missing 'results' field",
                "markdown_path": None
            }

        # Get markdown content and images from first result
        md_content = None
        images_data = None
        source_key = None
        for key, value in results.items():
            logger.debug(f"Checking result key '{key}', value keys: {list(value.keys()) if isinstance(value, dict) else 'not a dict'}")
            if 'md_content' in value:
                md_content = value['md_content']
                images_data = value.get('images', [])
                source_key = key
                logger.debug(f"Found md_content in '{key}', images field exists: {'images' in value}, images count: {len(images_data) if images_data else 0}")
                break

        if md_content is None:
            return {
                "status": "error",
                "message": "API response missing 'md_content' field",
                "markdown_path": None
            }

        logger.info(f"Markdown content extracted from: {source_key}")
        logger.info(f"Found {len(images_data) if images_data else 0} images in API response")

        # Save markdown file
        with open(md_file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

        logger.info(f"Markdown file saved: {md_file_path}")

        # Process and save images
        images_info = []
        if images_data:
            images_dir = output_dir_obj / "images"
            images_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Processing {len(images_data)} images...")

            import base64

            # Handle both dict and list formats
            if isinstance(images_data, dict):
                # Images is a dictionary: {filename: base64_string}
                for img_idx, (img_filename, img_base64) in enumerate(images_data.items(), 1):
                    try:
                        if not img_base64:
                            logger.warning(f"Image {img_idx} ({img_filename}) missing base64 data")
                            continue

                        # Fix base64 padding and save image
                        img_save_path = images_dir / img_filename
                        img_base64_fixed = fix_base64_padding(img_base64)
                        img_bytes = base64.b64decode(img_base64_fixed)
                        with open(img_save_path, 'wb') as f:
                            f.write(img_bytes)

                        # Record image info
                        images_info.append({
                            'index': img_idx,
                            'filename': img_filename,
                            'path': str(img_save_path),
                            'relative_path': f"images/{img_filename}",
                            'size_bytes': len(img_bytes)
                        })

                        logger.info(f"Saved image {img_idx}: {img_filename} ({len(img_bytes)} bytes)")

                    except Exception as e:
                        logger.error(f"Failed to save image {img_idx} ({img_filename}): {e}")
                        continue

            elif isinstance(images_data, list):
                # Images is a list (legacy format)
                for img_idx, img_item in enumerate(images_data, 1):
                    try:
                        # Check if img_item is a string (base64) or dict
                        if isinstance(img_item, str):
                            # Direct base64 string
                            img_base64 = img_item
                            img_filename = f"image_{img_idx}.jpg"
                        elif isinstance(img_item, dict):
                            # Dictionary with img_path and img_base64
                            img_path = img_item.get('img_path', '')
                            img_base64 = img_item.get('img_base64', '')

                            if not img_base64:
                                logger.warning(f"Image {img_idx} missing base64 data")
                                continue

                            # Use API returned path name, or generate one
                            if img_path:
                                img_filename = Path(img_path).name
                            else:
                                img_filename = f"image_{img_idx}.jpg"
                        else:
                            logger.warning(f"Image {img_idx} has unexpected type: {type(img_item)}")
                            continue

                        # Fix base64 padding and save image
                        img_save_path = images_dir / img_filename
                        img_base64_fixed = fix_base64_padding(img_base64)
                        img_bytes = base64.b64decode(img_base64_fixed)
                        with open(img_save_path, 'wb') as f:
                            f.write(img_bytes)

                        # Record image info
                        images_info.append({
                            'index': img_idx,
                            'filename': img_filename,
                            'path': str(img_save_path),
                            'relative_path': f"images/{img_filename}",
                            'size_bytes': len(img_bytes)
                        })

                        logger.info(f"Saved image {img_idx}: {img_filename} ({len(img_bytes)} bytes)")

                    except Exception as e:
                        logger.error(f"Failed to save image {img_idx}: {e}")
                        continue

            logger.info(f"Successfully saved {len(images_info)}/{len(images_data)} images")

        # Cleanup UUID folders created by API if requested
        if cleanup_uuid_folders:
            import shutil
            import re
            # UUID pattern: 8-4-4-4-12 hex digits
            uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')

            for item in output_dir_obj.iterdir():
                if item.is_dir() and uuid_pattern.match(item.name):
                    try:
                        shutil.rmtree(item)
                        logger.info(f"Cleaned up UUID folder: {item.name}")
                    except Exception as e:
                        logger.warning(f"Failed to remove UUID folder {item.name}: {e}")

        # Calculate statistics
        lines = md_content.split('\n')
        file_stats = {
            "size_bytes": md_file_path.stat().st_size,
            "line_count": len(lines),
            "char_count": len(md_content)
        }

        return {
            "status": "success",
            "message": "PDF successfully converted to Markdown",
            "markdown_path": str(md_file_path),
            "file_stats": file_stats,
            "images_count": len(images_info),
            "images_dir": str(images_dir) if images_data else None,
            "images": images_info
        }

    except requests.exceptions.ConnectionError:
        error_msg = f"Cannot connect to API server: {api_url}. Please ensure paper2md service is running."
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "markdown_path": None
        }

    except requests.exceptions.Timeout:
        error_msg = "API request timed out after 5 minutes"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "markdown_path": None
        }

    except requests.exceptions.RequestException as e:
        error_msg = f"API request failed: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg,
            "markdown_path": None
        }

    except Exception as e:
        error_msg = f"Unexpected error during PDF conversion: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {
            "status": "error",
            "message": error_msg,
            "markdown_path": None
        }


def main():
    """Test function to demonstrate paper2md tool functionality."""
    # Enable debug logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("Paper2MD Tool Testing Started...")
    print("=" * 80)

    # Test PDF path
    test_pdf = "./examples/paper2poster/data/2411.04905v3.pdf"

    # Check if test file exists
    if not Path(test_pdf).exists():
        print(f"Warning: Test PDF file does not exist: {test_pdf}")
        print("Please provide a valid PDF file path")
        return

    # Test 1: Convert PDF
    print("\nTest 1: Convert PDF to Markdown")
    result = pdf_to_markdown_tool(pdf_path=test_pdf)

    if result["status"] == "success":
        print("Success: Conversion completed")
        print(f"Message: {result['message']}")
        print(f"Markdown file: {result['markdown_path']}")

        # Check if file exists and show basic info
        md_path = Path(result['markdown_path'])
        if md_path.exists():
            file_size = md_path.stat().st_size
            print(f"File size: {file_size:,} bytes")

            # Show content preview
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                print(f"Total lines: {len(lines):,}")
                print(f"\nContent preview (first 5 lines):")
                for i, line in enumerate(lines[:5], 1):
                    print(f"   {i}. {line[:80]}{'...' if len(line) > 80 else ''}")
    else:
        print("Failed: Conversion failed")
        print(f"Error: {result.get('message')}")
        print(f"Markdown path: {result.get('markdown_path')}")


if __name__ == "__main__":
    main()
