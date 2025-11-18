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
Image caption generation tool
Extracts images from Markdown documents and uses VLM to generate image titles and descriptions
"""

import re
import os
import json
import base64
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Check dependencies
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


# ==================== Configuration Parameters ====================

# VLM configuration - loaded from environment variables
VLM_CONFIG = {
    'base_url': os.getenv("VLM_BASE_URL"),
    'api_key': os.getenv("VLM_API_KEY"),
    'model': os.getenv("VLM_MODEL")
}

# Section keyword definitions (sorted by priority)
SECTION_KEYWORDS = {
    'abstract': ['abstract', 'summary', '摘要'],
    'appendix': ['appendix', 'supplementary', '附录'],
    'introduction': ['introduction', '引言', '介绍'],
    'related_work': ['related work', 'background', '相关工作', '背景'],
    'experiment': ['experiment', 'result', 'evaluation', '实验', '结果', '评估'],
    'method': ['method', 'approach', 'methodology', '方法'],
    'conclusion': ['conclusion', 'future work', '结论', '总结']
}

# Reference section keywords
REFERENCE_KEYWORDS = ['reference', 'references', '参考文献', 'bibliography']

# VLM caption generation prompt
VLM_CAPTION_PROMPT = """Please generate a concise Chinese title and detailed description for this image from an academic paper.

Requirements:
1. Title: Concise and clear, no more than 20 characters, summarizing the main content of the image
2. Description: Detailed description of the image content, structure, key information, etc., 100-200 characters

Current section: {section}
Original title (if any): {original_title}

Please return in the following JSON format:
{{
    "title": "Image title",
    "description": "Detailed description of the image"
}}
"""

# Default configuration
DEFAULT_MAX_WORKERS = 5
VLM_TIMEOUT = int(os.getenv("VLM_TIMEOUT") or "1000")
VLM_MAX_TOKENS = int(os.getenv("VLM_MAX_TOKENS") or "6000")
VLM_TEMPERATURE = float(os.getenv("VLM_TEMPERATURE") or "0.9")


def image_caption_tool(
    md_file_path: str,
    max_workers: int = DEFAULT_MAX_WORKERS,
    output_json: bool = True,
    output_html: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Generate Chinese titles and detailed descriptions for images in a Markdown document.

    Args:
        md_file_path: Markdown file path
        max_workers: Maximum number of concurrent processing threads (default 5)
        output_json: Whether to output JSON file (default True)
        output_html: Whether to output HTML file (default True)
        **kwargs: Other parameters

    Returns:
        Dict[str, Any]: Contains the following fields:
            - status: "success" or "error"
            - message: Operation result description
            - total_images: Total image count (on success)
            - success_count: Successful generation count (on success)
            - failed_count: Failure count (on success)
            - output_dir: Output directory (on success)
            - json_path: JSON file path (on success, if output_json=True)
            - html_path: HTML file path (on success, if output_html=True)
            - images: Image information list (on success)
            - error: Error message (on failure)
    """
    # Check dependencies
    missing_deps = []
    if not PIL_AVAILABLE:
        missing_deps.append("Pillow")
    if not REQUESTS_AVAILABLE:
        missing_deps.append("requests")

    if missing_deps:
        return {
            "status": "error",
            "error": f"Missing dependencies: {', '.join(missing_deps)}. Please install using: pip install {' '.join(missing_deps)}"
        }

    try:
        # Create generator
        generator = ImageCaptionGenerator(md_file_path, max_workers=max_workers)

        # Execute complete workflow
        results = generator.process()

        # Save results
        output_dir = Path(md_file_path).parent
        output_dir.mkdir(exist_ok=True, parents=True)

        output_files = {}

        # Save as JSON
        if output_json:
            json_output = output_dir / "image_captions.json"
            generator.save_to_json(str(json_output))
            output_files['json_path'] = str(json_output)

        # Save as HTML
        if output_html:
            html_output = output_dir / "image_captions.html"
            generator.save_to_html(str(html_output))
            output_files['html_path'] = str(html_output)

        # Statistics
        success_count = len([img for img in results if img.get('generated_title')])
        total_count = len(results)

        return {
            "status": "success",
            "message": f"Image caption generation completed, successfully processed {success_count}/{total_count} images",
            "total_images": total_count,
            "success_count": success_count,
            "failed_count": total_count - success_count,
            "md_file_path": md_file_path,
            "output_dir": str(output_dir),
            **output_files,
            "images": results
        }

    except FileNotFoundError as e:
        return {
            "status": "error",
            "error": f"File not found: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Generation failed: {str(e)}"
        }


class ImageCaptionGenerator:
    """Image caption generator"""

    def __init__(self, md_file_path: str, max_workers: int = DEFAULT_MAX_WORKERS):
        self.md_file_path = Path(md_file_path)
        self.md_dir = self.md_file_path.parent
        self.content = ""
        self.images = []
        self.max_workers = max_workers

    def load_markdown(self) -> None:
        """Load Markdown file content into memory"""
        if not self.md_file_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {self.md_file_path}")

        with open(self.md_file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()

    def _find_reference_section(self, lines: List[str]) -> Optional[int]:
        """Find the starting position of the Reference section"""
        for i, line in enumerate(lines):
            line_stripped = line.strip().lower()
            if line_stripped.startswith('#'):
                title = re.sub(r'^#+\s*', '', line_stripped)
                for keyword in REFERENCE_KEYWORDS:
                    if title == keyword or title.startswith(keyword):
                        return i
        return None

    def _get_section(self, lines: List[str], image_line_idx: int) -> str:
        """Get the section name where the image is located"""
        for i in range(image_line_idx, -1, -1):
            line = lines[i].strip()
            if line.startswith('#'):
                title = re.sub(r'^#+\s*', '', line).lower()
                for section_type, keywords in SECTION_KEYWORDS.items():
                    for keyword in keywords:
                        if keyword in title:
                            return section_type
                return re.sub(r'^#+\s*', '', lines[i].strip())
        return "unknown"

    def _get_image_size(self, image_path: str) -> Tuple[str, Optional[Tuple[int, int]]]:
        """Get the pixel size of the image"""
        try:
            full_path = self.md_dir / image_path
            if not full_path.exists():
                return "Unknown", None
            with Image.open(full_path) as img:
                width, height = img.size
                return f"{width}x{height}", (width, height)
        except Exception:
            return "Error", None

    def _encode_image_to_base64(self, image_path: str) -> Optional[str]:
        """Encode image file to base64 string"""
        try:
            path = Path(image_path)
            if not path.is_absolute():
                path = self.md_dir / image_path
            if not path.exists():
                return None
            with open(path, 'rb') as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception:
            return None

    def _generate_caption_with_vlm(self, image_path: str, section: str,
                                   original_title: str) -> Optional[Dict[str, str]]:
        """Use VLM to generate image title and description"""
        base64_image = self._encode_image_to_base64(image_path)
        if not base64_image:
            return None

        prompt = VLM_CAPTION_PROMPT.format(
            section=section,
            original_title=original_title if original_title else 'None'
        )

        try:
            headers = {
                'Authorization': f"Bearer {VLM_CONFIG['api_key']}",
                'Content-Type': 'application/json'
            }

            payload = {
                'model': VLM_CONFIG['model'],
                'messages': [
                    {
                        'role': 'user',
                        'content': [
                            {'type': 'text', 'text': prompt},
                            {
                                'type': 'image_url',
                                'image_url': {
                                    'url': f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                'max_tokens': VLM_MAX_TOKENS,
                'temperature': VLM_TEMPERATURE
            }

            response = requests.post(
                f"{VLM_CONFIG['base_url']}/chat/completions",
                headers=headers,
                json=payload,
                timeout=VLM_TIMEOUT
            )

            if response.status_code == 200:
                result = response.json()
                answer = result.get('choices', [{}])[0].get('message', {}).get('content', '').strip()

                if not answer:
                    return None

                # Try to parse JSON format
                try:
                    json_match = re.search(r'```json\s*(\{.*?\})\s*```', answer, re.DOTALL)
                    if json_match:
                        answer = json_match.group(1)

                    caption_data = json.loads(answer)
                    if 'title' in caption_data and 'description' in caption_data:
                        return caption_data
                    return None
                except json.JSONDecodeError:
                    return {
                        'title': answer[:50] if len(answer) <= 50 else answer[:47] + "...",
                        'description': answer
                    }
            return None
        except Exception:
            return None

    def extract_images(self) -> List[Dict]:
        """Extract basic information of all images from Markdown document"""
        self.load_markdown()
        lines = self.content.split('\n')

        reference_line_idx = self._find_reference_section(lines)
        image_pattern = r'!\[.*?\]\((.*?)\)'
        idx = 1

        i = 0
        while i < len(lines):
            if reference_line_idx is not None and i >= reference_line_idx:
                break

            line = lines[i]
            match = re.search(image_pattern, line)

            if match:
                image_path = match.group(1)
                absolute_path = str((self.md_dir / image_path).resolve())

                original_title = ""
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if next_line.startswith('Figure') or next_line.startswith('Table'):
                        original_title = next_line

                pixel_size, dimensions = self._get_image_size(image_path)
                section = self._get_section(lines, i)

                image_info = {
                    'idx': idx,
                    'path': absolute_path,
                    'pixel_size': pixel_size,
                    'dimensions': dimensions,
                    'original_title': original_title,
                    'section': section,
                    'generated_title': '',
                    'description': '',
                    'line_number': i
                }

                self.images.append(image_info)
                idx += 1

            i += 1

        return self.images

    def generate_captions_batch(self) -> None:
        """Batch and concurrently generate titles and descriptions for all images"""
        if not self.images:
            return

        def generate_single_caption(img_info: Dict) -> Tuple[int, Optional[Dict[str, str]]]:
            idx = img_info['idx']
            image_path = img_info['path']
            section = img_info['section']
            original_title = img_info['original_title']

            caption_result = self._generate_caption_with_vlm(
                image_path, section, original_title
            )

            if caption_result:
                return (idx, caption_result)
            else:
                return (idx, None)

        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_img = {
                executor.submit(generate_single_caption, img): img
                for img in self.images
            }

            for future in as_completed(future_to_img):
                try:
                    idx, caption_result = future.result()
                    if caption_result:
                        results[idx] = caption_result
                except Exception:
                    pass

        # Update image titles and descriptions
        for img in self.images:
            if img['idx'] in results:
                img['generated_title'] = results[img['idx']]['title']
                img['description'] = results[img['idx']]['description']

    def process(self) -> List[Dict]:
        """Complete workflow: extract images + generate titles"""
        self.extract_images()
        self.generate_captions_batch()
        return self.images

    def save_to_json(self, output_path: str) -> None:
        """Save results as JSON file"""
        output_data = []
        for img in self.images:
            output_data.append({
                'idx': img['idx'],
                'path': img['path'],
                'pixel_size': img['pixel_size'],
                'section': img['section'],
                'original_title': img['original_title'],
                'generated_title': img['generated_title'],
                'description': img['description']
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

    def save_to_html(self, output_path: str) -> None:
        """Save results as HTML file (visual display)"""
        # HTML template (simplified version)
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Image Caption Generation Results</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1400px; margin: 0 auto; background: white; border-radius: 10px; padding: 30px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .stats {{ display: flex; justify-content: space-around; margin-bottom: 30px; }}
        .stat-item {{ text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .image-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(450px, 1fr)); gap: 30px; }}
        .image-card {{ border: 1px solid #ddd; border-radius: 10px; overflow: hidden; }}
        .image-preview {{ width: 100%; height: 300px; object-fit: contain; padding: 10px; background: #f8f9fa; }}
        .image-info {{ padding: 20px; }}
        .generated-title {{ font-size: 1.2em; color: #667eea; font-weight: bold; margin-bottom: 10px; }}
        .description {{ padding: 10px; background: #f8f9fa; border-radius: 5px; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Image Caption Generation Results</h1>
        </div>
        <div class="stats">
            <div class="stat-item"><div class="stat-number">{len(self.images)}</div><div>Total Images</div></div>
            <div class="stat-item"><div class="stat-number">{len([img for img in self.images if img['generated_title']])}</div><div>Success</div></div>
            <div class="stat-item"><div class="stat-number">{len([img for img in self.images if not img['generated_title']])}</div><div>Failed</div></div>
        </div>
        <div class="image-grid">
"""

        for img in self.images:
            html_content += f"""
            <div class="image-card">
                <img src="{img['path']}" alt="Image {img['idx']}" class="image-preview">
                <div class="image-info">
                    <div class="generated-title">{img['generated_title'] if img['generated_title'] else 'Title generation failed'}</div>
                    {f'<div class="description">{img["description"]}</div>' if img['description'] else ''}
                    <div><strong>Path:</strong> {img['path']}</div>
                    <div><strong>Size:</strong> {img['pixel_size']}</div>
                    <div><strong>Section:</strong> {img['section']}</div>
                </div>
            </div>
"""

        html_content += """
        </div>
    </div>
</body>
</html>
"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
