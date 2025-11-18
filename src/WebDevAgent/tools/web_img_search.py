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

import os
from typing import Any
import httpx
from openai import OpenAI
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import subprocess
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unsplash_search.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def clean_url(url: str, params_to_remove: list[str] = ['ixid', 'ixlib']) -> str:
    """
    Remove specified query parameters from URL

    Args:
        url: Original URL
        params_to_remove: List of parameter names to remove

    Returns:
        Cleaned URL without specified parameters
    """
    if not url:
        return url

    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    # Remove specified parameters
    for param in params_to_remove:
        query_params.pop(param, None)

    # Reconstruct URL
    new_query = urlencode(query_params, doseq=True)
    cleaned_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment
    ))

    return cleaned_url

IMAGE_CAPTIONER_SYSTEM_PROMPT = """
You are a helpful assistant that captions images.
Your task:
1. Generate a natural, detailed caption describing the image content in exactly 100 words.
2. Evaluate and report whether the image contains any visible watermark (Yes/No + short explanation).
3. Assess the image clarity (e.g., Clear, Slightly Blurry, Blurry) with a brief justification.
Your response must follow this structure:
- Caption (100 words)
- Watermark Analysis
- Clarity Analysis
"""

def image_captioner(image_url: str) -> str:
    """Synchronous version of image captioner"""
    logger.info(f"Generating caption for image: {image_url}")
    try:
        # Load configuration from environment variables
        api_key = os.getenv('IMAGE_CAPTIONER_API_KEY')
        base_url = os.getenv('IMAGE_CAPTIONER_BASE_URL')
        model = os.getenv('IMAGE_CAPTIONER_MODEL')

        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": IMAGE_CAPTIONER_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Please caption this image:"},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ]
                }
            ],
        )
        caption = response.choices[0].message.content
        logger.info(f"Successfully generated caption for {image_url}")
        return caption
    except Exception as e:
        logger.error(f"Failed to generate caption for {image_url}: {str(e)}")
        raise


def generate_caption_for_result(result: dict, index: int) -> tuple[int, str]:
    """
    Helper function to generate caption for a single result.
    Returns a tuple of (index, caption) for concurrent processing.
    """
    try:
        caption = image_captioner(result['imageUrl'])
        return (index, caption)
    except Exception as e:
        logger.warning(f"Failed to generate caption for {result.get('imageUrl', 'unknown')}: {str(e)}")
        return (index, f"Failed to generate caption: {str(e)}")


class UnsplashSearch:
    def __init__(self, timeout: float = 30.0, max_retries: int = 3):
        # Get API keys from environment variable (comma-separated string)
        access_keys_str = os.getenv('UNSPLASH_ACCESS_KEYS', '')

        if access_keys_str:
            # Split comma-separated keys and strip whitespace
            self.ACCESS_KEY_LIST = [key.strip() for key in access_keys_str.split(',') if key.strip()]
        else:
            # Fallback to default keys if not set in environment
            self.ACCESS_KEY_LIST = [
                ""
            ]

        self.base_url = 'https://api.unsplash.com/'
        self.timeout = timeout
        self.max_retries = max_retries
        logger.info(f"Initialized UnsplashSearch with {len(self.ACCESS_KEY_LIST)} API keys, timeout={timeout}s, max_retries={max_retries}")

    def search(
        self,
        query: str,
        num_results: int = 10,
        orientation: str = None,  # 'landscape', 'portrait', 'squarish'
        order_by: str = 'relevant',  # 'latest' or 'relevant'
        add_caption: bool = False,  # Whether to add AI-generated captions
    ) -> list[dict[str, Any]] | str:
        """
        Search for images on Unsplash

        Args:
            query: Search query string
            num_results: Number of results to return (max 30 per page)
            orientation: Filter by photo orientation
            order_by: How to sort results ('latest' or 'relevant')
            add_caption: Whether to generate AI captions for images

        Returns:
            List of image results or error message string
        """
        logger.info(f"Starting search: query='{query}', num_results={num_results}, orientation={orientation}, order_by={order_by}, add_caption={add_caption}")

        access_key = random.choice(self.ACCESS_KEY_LIST)
        logger.info(f"Using access key: {access_key}")
        headers = {
            'Authorization': f'Client-ID {access_key}',
            'Accept-Version': 'v1',
        }

        # Calculate pages needed (Unsplash max per_page is 30)
        per_page = min(num_results, 30)
        pages_needed = (num_results + per_page - 1) // per_page
        # logger.info(f"Will fetch {pages_needed} page(s) with {per_page} results per page")

        all_results = []

        for page in range(1, pages_needed + 1):
            # logger.info(f"Fetching page {page}/{pages_needed}")
            params = {
                'query': query,
                'per_page': per_page,
                'page': page,
                'order_by': order_by,
            }

            if orientation:
                params['orientation'] = orientation

            for attempt in range(self.max_retries):
                try:
                    with httpx.Client(
                        timeout=httpx.Timeout(
                            connect=self.timeout,
                            read=self.timeout,
                            write=self.timeout,
                            pool=self.timeout,
                        ),
                    ) as client:
                        response = client.get(
                            self.base_url + 'search/photos',
                            headers=headers,
                            params=params,
                        )
                        response.raise_for_status()
                        data = response.json()

                        results = data.get('results', [])
                        # logger.info(f"Page {page}: Received {len(results)} images from Unsplash API")

                        # Process results to match the format of SerperSearch
                        processed_results = []
                        for item in results:
                            # Clean URLs to remove ixid and ixlib parameters
                            # Unsplash provides multiple sizes: raw, full, regular, small, thumb
                            image_url = clean_url(item['urls'].get('regular'))  # ~1080px
                            small_url = clean_url(item['urls'].get('small'))    # ~400px
                            thumbnail_url = clean_url(item['urls'].get('thumb'))  # ~200px

                            result = {
                                'title': item.get('alt_description') or item.get('description') or 'Untitled',
                                'imageUrl': image_url,  # Regular size image URL (cleaned)
                                'smallUrl': small_url,  # Small size for cards (cleaned)
                                'imageWidth': item.get('width'),
                                'imageHeight': item.get('height'),
                                'thumbnailUrl': thumbnail_url,  # Thumbnail URL (cleaned)
                                'source': 'Unsplash',
                                'link': item['links'].get('html'),  # Link to Unsplash page
                                'photographer': item['user'].get('name'),
                                'photographer_url': item['user']['links'].get('html'),
                                'color': item.get('color'),
                                'likes': item.get('likes'),
                                'created_at': item.get('created_at'),
                            }

                            processed_results.append(result)

                        # Add AI-generated captions concurrently if requested
                        if add_caption:
                            # Filter results that have valid imageUrl
                            results_to_caption = [
                                (i, res) for i, res in enumerate(processed_results)
                                if res.get('imageUrl') and not res['imageUrl'].startswith('data:')
                            ]

                            if results_to_caption:
                                # logger.info(f"Starting concurrent caption generation for {len(results_to_caption)} images")
                                max_workers = min(10, len(results_to_caption))  # Limit concurrent workers
                                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                                    # Submit all caption generation tasks
                                    future_to_index = {
                                        executor.submit(generate_caption_for_result, res, i): i
                                        for i, res in results_to_caption
                                    }

                                    # Collect results as they complete
                                    for future in as_completed(future_to_index):
                                        index, caption = future.result()
                                        processed_results[index]['caption'] = caption

                                logger.info(f"Completed concurrent caption generation for {len(results_to_caption)} images")

                        all_results.extend(processed_results)
                        logger.info(f"Page {page}: Processed {len(processed_results)} images, total so far: {len(all_results)}")

                        # Stop if we have enough results
                        if len(all_results) >= num_results:
                            final_results = all_results[:num_results]
                            logger.info(f"Search completed successfully: Returning {len(final_results)} results")
                            return final_results

                        # Break retry loop on success
                        break

                except httpx.ConnectTimeout as e:
                    logger.error(f"Page {page}, Attempt {attempt + 1}/{self.max_retries}: Connection timeout - {str(e)}")
                    if attempt == self.max_retries - 1:
                        return f"Connection timeout after {self.max_retries} attempts: {str(e)}"
                    time.sleep(2**attempt)  # Exponential backoff
                    continue
                except httpx.TimeoutException as e:
                    logger.error(f"Page {page}, Attempt {attempt + 1}/{self.max_retries}: Request timeout - {str(e)}")
                    if attempt == self.max_retries - 1:
                        return f"Request timeout after {self.max_retries} attempts: {str(e)}"
                    time.sleep(2**attempt)
                    continue
                except httpx.HTTPStatusError as e:
                    logger.error(f"Page {page}, Attempt {attempt + 1}/{self.max_retries}: HTTP error {e.response.status_code} - {str(e)}")
                    if attempt == self.max_retries - 1:
                        return f"HTTP error {e.response.status_code}: {str(e)}"
                    time.sleep(2**attempt)
                    continue
                except Exception as e:
                    logger.error(f"Page {page}, Attempt {attempt + 1}/{self.max_retries}: Unexpected error - {str(e)}")
                    if attempt == self.max_retries - 1:
                        return f"Unexpected error: {str(e)}"
                    time.sleep(2**attempt)
                    continue

        logger.info(f"Search completed: Returning {len(all_results)} results")
        return all_results


def save_results(results: list[dict[str, Any]], query: str, output_dir: str = 'search_results') -> str:
    """
    Save search results to a JSON file

    Args:
        results: List of search results
        query: Search query used
        output_dir: Directory to save results

    Returns:
        Path to the saved file
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_query = "".join(c if c.isalnum() else "_" for c in query)[:50]
    filename = f"{safe_query}_{timestamp}.json"
    filepath = output_path / filename

    # Prepare data to save
    data = {
        'query': query,
        'timestamp': datetime.now().isoformat(),
        'num_results': len(results),
        'results': results
    }

    # Save to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info(f"Results saved to {filepath}")
    return str(filepath)


def download_images(results: list[dict[str, Any]], query: str, output_dir: str = 'downloaded_images', use_wget: bool = True) -> dict[str, Any]:
    """
    Download images from search results

    Args:
        results: List of search results containing imageUrl
        query: Search query used (for directory naming)
        output_dir: Base directory to save images
        use_wget: Whether to use wget command (True) or httpx (False)

    Returns:
        Dictionary with download statistics
    """
    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_query = "".join(c if c.isalnum() else "_" for c in query)[:50]
    download_path = Path(output_dir) / f"{safe_query}_{timestamp}"
    download_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting to download {len(results)} images to {download_path}")

    stats = {
        'total': len(results),
        'success': 0,
        'failed': 0,
        'downloaded_files': [],
        'failed_urls': []
    }

    for i, result in enumerate(results, 1):
        image_url = result.get('imageUrl')
        if not image_url:
            logger.warning(f"Image {i}: No imageUrl found")
            stats['failed'] += 1
            continue

        # Generate filename
        photographer = result.get('photographer', 'unknown').replace(' ', '_')
        ext = 'jpg'  # Unsplash images are typically JPG
        filename = f"{i:02d}_{photographer}_{safe_query}.{ext}"
        filepath = download_path / filename

        logger.info(f"Downloading image {i}/{len(results)}: {filename}")

        try:
            if use_wget:
                # Use wget command
                cmd = [
                    'wget',
                    '-q',  # Quiet mode
                    '-O', str(filepath),  # Output file
                    image_url
                ]
                result_code = subprocess.run(cmd, capture_output=True, timeout=60)

                if result_code.returncode == 0:
                    logger.info(f"Successfully downloaded: {filename}")
                    stats['success'] += 1
                    stats['downloaded_files'].append(str(filepath))
                else:
                    logger.error(f"wget failed for {filename}: {result_code.stderr.decode()}")
                    stats['failed'] += 1
                    stats['failed_urls'].append(image_url)
            else:
                # Use httpx
                with httpx.Client(timeout=60.0) as client:
                    response = client.get(image_url)
                    response.raise_for_status()

                    with open(filepath, 'wb') as f:
                        f.write(response.content)

                    logger.info(f"Successfully downloaded: {filename}")
                    stats['success'] += 1
                    stats['downloaded_files'].append(str(filepath))

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout downloading {filename}")
            stats['failed'] += 1
            stats['failed_urls'].append(image_url)
        except Exception as e:
            logger.error(f"Failed to download {filename}: {str(e)}")
            stats['failed'] += 1
            stats['failed_urls'].append(image_url)

    logger.info(f"Download completed: {stats['success']}/{stats['total']} successful, {stats['failed']} failed")

    # Save download info
    info_file = download_path / '_download_info.json'
    with open(info_file, 'w', encoding='utf-8') as f:
        json.dump({
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'statistics': stats
        }, f, ensure_ascii=False, indent=2)

    return stats


def web_img_search(query: str, search_type: str = 'images', num_results: int = 10):
    """
    Compatible interface for web image search using Unsplash.
    This function maintains compatibility with the old SerperSearch interface.

    NOTE: This function ALWAYS adds AI-generated captions to match the old behavior.

    Args:
        query: Search query string
        search_type: Search type (only 'images' is supported)
        num_results: Number of results to return

    Returns:
        List of image results or error message string
    """
    searcher = UnsplashSearch()
    image_results = searcher.search(query, num_results)

    # Process image results to add captions concurrently (matching old SerperSearch behavior)
    if isinstance(image_results, list) and search_type == 'images':
        # Filter results that have valid imageUrl
        results_to_caption = [
            (i, result) for i, result in enumerate(image_results)
            if 'imageUrl' in result and not result['imageUrl'].startswith('data:')
        ]

        # Remove base64 images
        for result in image_results:
            if 'imageUrl' in result and result['imageUrl'].startswith('data:'):
                del result['imageUrl']

        # Concurrently generate captions for all valid images
        if results_to_caption:
            logger.info(f"Starting concurrent caption generation for {len(results_to_caption)} images in web_img_search")
            max_workers = min(10, len(results_to_caption))  # Limit concurrent workers
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit all caption generation tasks
                future_to_index = {
                    executor.submit(generate_caption_for_result, result, i): i
                    for i, result in results_to_caption
                }

                # Collect results as they complete
                for future in as_completed(future_to_index):
                    index, caption = future.result()
                    image_results[index]['caption'] = caption

            logger.info(f"Completed concurrent caption generation for {len(results_to_caption)} images in web_img_search")

    return image_results


def unsplash_img_search(
    query: str,
    num_results: int = 10,
    orientation: str = None,
    order_by: str = 'relevant',
    add_caption: bool = False,
    save_to_file: bool = True,
    download_images_flag: bool = False,
    use_wget: bool = True,
) -> list[dict[str, Any]] | str:
    """
    Search for images on Unsplash

    Args:
        query: Search query string
        num_results: Number of results to return
        orientation: Filter by photo orientation ('landscape', 'portrait', 'squarish')
        order_by: How to sort results ('latest' or 'relevant')
        add_caption: Whether to generate AI captions for images
        save_to_file: Whether to save results to a JSON file
        download_images_flag: Whether to download the images
        use_wget: Whether to use wget for downloading (True) or httpx (False)

    Returns:
        List of image results or error message string
    """
    logger.info(f"Calling unsplash_img_search with query='{query}'")
    searcher = UnsplashSearch()
    image_results = searcher.search(
        query=query,
        num_results=num_results,
        orientation=orientation,
        order_by=order_by,
        add_caption=add_caption,
    )

    # Save results if requested and search was successful
    if save_to_file and isinstance(image_results, list):
        try:
            saved_path = save_results(image_results, query)
            logger.info(f"Search results saved to {saved_path}")
        except Exception as e:
            logger.error(f"Failed to save results: {str(e)}")

    # Download images if requested and search was successful
    if download_images_flag and isinstance(image_results, list):
        try:
            stats = download_images(image_results, query, use_wget=use_wget)
            logger.info(f"Download statistics: {stats['success']}/{stats['total']} successful")
        except Exception as e:
            logger.error(f"Failed to download images: {str(e)}")

    return image_results


if __name__ == '__main__':
    # Example usage
    print("=" * 60)
    print("Unsplash Image Search Test")
    print("=" * 60)

    results = unsplash_img_search(
        query='village',
        num_results=5,
        save_to_file=True,
        download_images_flag=True,  # Enable image downloading
        use_wget=True  # Use wget for downloading
    )

    if isinstance(results, str):
        print(f"Error: {results}")
    else:
        print(f"\nFound {len(results)} images:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   URL: {result['imageUrl']}")
            print(f"   Photographer: {result['photographer']}")
            print(f"   Likes: {result['likes']}")

        print("\n" + "=" * 60)
        print(f"Results have been saved to the 'search_results' directory")
        print(f"Images have been downloaded to the 'downloaded_images' directory")
        print(f"Log file: unsplash_search.log")
        print("=" * 60)
