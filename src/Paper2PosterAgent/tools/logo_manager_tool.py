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
Logo Manager Tool for NexAU Framework
Provides logo search, download, and matching functionality
"""

import os
import re
import logging
import requests
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from difflib import SequenceMatcher
from PIL import Image
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class LogoManager:
    """Class for managing logo storage and retrieval (using file matching)"""

    def __init__(self, base_path: str = "logo_store"):
        """
        Initialize LogoManager

        Args:
            base_path: Base directory for logo storage
        """
        self.base_path = Path(base_path)
        self._setup_directories()

    def _setup_directories(self):
        """Create necessary logo storage directories"""
        directories = [
            self.base_path,
            self.base_path / "conferences",
            self.base_path / "institutes",
            self.base_path / "raw_downloads"
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _extract_abbreviation(self, name: str) -> Optional[str]:
        """
        Extract abbreviation form
        MIT, CMU, UCLA etc. are returned directly
        University of California Berkeley → UCB
        """
        # Common abbreviation mappings
        abbrev_map = {
            # Universities
            r'\bmit\b': 'mit',
            r'\bcmu\b': 'cmu',
            r'\bucla\b': 'ucla',
            r'\bucsd\b': 'ucsd',
            r'\bucsb\b': 'ucsb',
            r'\bucb\b|berkeley': 'ucb',
            r'\bnyu\b': 'nyu',
            r'\beth\b': 'eth',
            r'\bepfl\b': 'epfl',
            r'\bcal\s*tech|caltech': 'caltech',

            # Conferences
            r'\bneurips\b|\bnips\b': 'neurips',
            r'\biclr\b': 'iclr',
            r'\bicml\b': 'icml',
            r'\bcvpr\b': 'cvpr',
            r'\biccv\b': 'iccv',
            r'\beccv\b': 'eccv',
            r'\baaai\b': 'aaai',
            r'\bijcai\b': 'ijcai',
            r'\bacl\b': 'acl',
            r'\bemnlp\b': 'emnlp',

            # Companies/Labs
            r'\bgoogle\b': 'google',
            r'\bdeep\s*mind|deepmind\b': 'deepmind',
            r'\bmeta\b|\bfair\b': 'meta',
            r'\bopenai\b': 'openai',
            r'\bmicrosoft\b|\bmsr\b': 'microsoft',
            r'\bnvidia\b': 'nvidia',
            r'\bamazon\b': 'amazon',
            r'\bapple\b': 'apple',
        }

        name_lower = name.lower()

        # Check if it matches known abbreviations
        for pattern, abbrev in abbrev_map.items():
            if re.search(pattern, name_lower):
                return abbrev

        # If it's all uppercase and short (possibly an abbreviation)
        if name.isupper() and len(name) <= 6:
            return name.lower()

        # Try to generate abbreviation: take first letter of each capitalized word
        words = re.findall(r'\b[A-Z][a-z]*', name)
        if len(words) >= 2:
            abbrev = ''.join(w[0].lower() for w in words)
            if len(abbrev) <= 6:
                return abbrev

        return None

    def _normalize_name(self, name: str) -> str:
        """Normalize name for matching"""
        # Remove year suffix
        name = re.sub(r'\s*\d{4}\s*$', '', name)
        # Convert to lowercase and replace special characters
        name = name.lower()
        name = re.sub(r'[^a-z0-9]+', '_', name)
        name = name.strip('_')
        return name

    def _fuzzy_match(self, query: str, candidates: List[str]) -> Tuple[Optional[str], float]:
        """
        Find the best fuzzy match in the candidate list
        Supports abbreviation matching: MIT = Massachusetts Institute of Technology

        Args:
            query: Search query
            candidates: List of candidate strings

        Returns:
            Best matching candidate and similarity score (0-1)
        """
        query_norm = self._normalize_name(query)
        query_abbrev = self._extract_abbreviation(query)

        best_match = None
        best_score = 0.0

        for candidate in candidates:
            # Level 1: Exact match
            if query_norm == candidate:
                return candidate, 1.0

            # Level 2: Abbreviation match (high priority)
            if query_abbrev:
                candidate_abbrev = self._extract_abbreviation(candidate)
                if query_abbrev == candidate:  # MIT matches mit.png
                    logger.info(f"Abbreviation exact match: {query_abbrev} == {candidate}")
                    return candidate, 0.98
                if candidate_abbrev and query_abbrev == candidate_abbrev:
                    logger.info(f"Abbreviation match: {query_abbrev} == {candidate_abbrev}")
                    score = 0.95
                    if score > best_score:
                        best_match = candidate
                        best_score = score
                    continue

            # Level 3: Contains relationship
            if query_norm in candidate or candidate in query_norm:
                score = 0.85
                if score > best_score:
                    best_match = candidate
                    best_score = score
                continue

            # Level 4: Token-based matching (keyword overlap)
            query_tokens = set(query_norm.split('_'))
            candidate_tokens = set(candidate.split('_'))

            if query_tokens and candidate_tokens:
                intersection = query_tokens & candidate_tokens
                union = query_tokens | candidate_tokens
                jaccard = len(intersection) / len(union) if union else 0

                if jaccard >= 0.5:  # 50% keyword overlap
                    score = 0.7 + (jaccard * 0.2)  # 0.7-0.9 score range
                    if score > best_score:
                        best_match = candidate
                        best_score = score
                    continue

            # Level 5: Sequence similarity (Levenshtein)
            score = SequenceMatcher(None, query_norm, candidate).ratio()
            if score > best_score:
                best_match = candidate
                best_score = score

        # Lower threshold because abbreviation matching is smarter
        if best_score >= 0.5:  # 50% similarity threshold
            return best_match, best_score

        return None, 0.0

    def _scan_directory(self, directory: Path) -> Dict[str, Path]:
        """
        Scan PNG files in directory

        Returns:
            Dictionary mapping normalized names to file paths
        """
        logos = {}
        if directory.exists():
            for file in directory.glob("*.png"):
                name = file.stem.lower()
                logos[name] = file
        return logos

    def get_logo_path(self, name: str, category: str = "auto", use_google: bool = False) -> Optional[Path]:
        """
        Get logo file path using fuzzy matching

        Args:
            name: Conference/institution name
            category: Logo type ("conference", "institute", or "auto")
            use_google: Whether to use Google custom search

        Returns:
            Logo file path, or None if not found
        """
        logger.info(f"Looking for logo: '{name}' (category: {category})")

        # Scan available logos
        conference_logos = self._scan_directory(self.base_path / "conferences")
        institute_logos = self._scan_directory(self.base_path / "institutes")

        # Determine which directories to search
        if category == "conference":
            search_dirs = [("conferences", conference_logos)]
            logger.info(f"Searching in: conferences/ ({len(conference_logos)} logos)")
        elif category == "institute":
            search_dirs = [("institutes", institute_logos)]
            logger.info(f"Searching in: institutes/ ({len(institute_logos)} logos)")
        else:  # auto
            search_dirs = [("conferences", conference_logos), ("institutes", institute_logos)]
            logger.info(f"Searching in: conferences/ ({len(conference_logos)} logos), institutes/ ({len(institute_logos)} logos)")

        # Try to find best match
        best_match = None
        best_score = 0.0
        best_path = None
        best_dir = None

        for dir_name, logos in search_dirs:
            if logos:
                match, score = self._fuzzy_match(name, list(logos.keys()))
                if match and score > best_score:
                    best_match = match
                    best_score = score
                    best_path = logos[match]
                    best_dir = dir_name

        if best_path and best_path.exists():
            logger.info(f"MATCH FOUND: '{best_match}' in {best_dir}/ (similarity: {best_score:.1%})")
            logger.info(f"File: {best_path.name}")
            return best_path

        # If no match found, try downloading
        logger.info(f"No local match found (threshold: 60%)")
        logger.info(f"Attempting to download from web...")
        return self._download_and_save_logo(name, category, use_google=use_google)

    def _download_and_save_logo(self, name: str, category: str, use_google: bool = False) -> Optional[Path]:
        """
        Try to download logo from web and save

        Args:
            name: Name to search for
            category: Category to save to
            use_google: Whether to use Google search

        Returns:
            Downloaded logo path or None
        """
        search_query = f"{name} logo"
        logger.info(f"Web search query: '{search_query}'")
        if use_google:
            logger.info(f"Using Google Custom Search API")
        url = self.search_logo_web(search_query, use_google=use_google)

        if not url:
            logger.debug(f"No logo found online for: {name}")
            return None

        logger.info(f"Found URL: {url[:80]}...")

        # Determine save directory
        if category == "conference":
            save_dir = self.base_path / "conferences"
        else:
            save_dir = self.base_path / "institutes"

        # Generate filename
        filename = self._normalize_name(name) + ".png"
        save_path = save_dir / filename

        logger.info(f"Downloading to: {save_path}")
        if self.download_logo(url, save_path):
            logger.info(f"Successfully downloaded and saved: {filename}")
            return save_path
        else:
            logger.warning(f"Failed to download/convert logo")
            return None

    def search_logo_web(self, query: str, use_google: bool = False) -> Optional[str]:
        """
        Search for logo using DuckDuckGo or Google

        Args:
            query: Search query
            use_google: Whether to use Google custom search (requires API key)

        Returns:
            Found logo image URL or None
        """
        # First try DuckDuckGo (no API key needed)
        try:
            from fastbook import search_images_ddg

            results = search_images_ddg(
                f"{query} official transparent PNG SVG",
                max_images=5
            )

            for result in results:
                url = result.get('image')
                if url and any(ext in url.lower() for ext in ['.png', '.svg', '.jpg', '.jpeg']):
                    logger.info(f"Found potential logo: {url}")
                    return url

        except Exception as e:
            logger.debug(f"DuckDuckGo search failed: {e}")

        # If enabled and has API key, try Google custom search
        if use_google:
            try:
                google_api_key = os.getenv('GOOGLE_SEARCH_API_KEY')
                google_engine_id = os.getenv('GOOGLE_SEARCH_ENGINE_ID')

                if google_api_key and google_engine_id:
                    url = "https://www.googleapis.com/customsearch/v1"
                    params = {
                        'key': google_api_key,
                        'cx': google_engine_id,
                        'q': f"{query} official logo transparent PNG",
                        'searchType': 'image',
                        'num': 5,
                        'fileType': 'png|svg'
                    }

                    response = requests.get(url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        items = data.get('items', [])
                        if items:
                            return items[0].get('link')
                else:
                    logger.warning("Google API keys not found in environment")

            except Exception as e:
                logger.warning(f"Google search failed: {e}")

        return None

    def download_logo(self, url: str, save_path: Path) -> bool:
        """
        Download logo from URL

        Args:
            url: Logo URL
            save_path: Save path

        Returns:
            True on success, False on failure
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            save_path.parent.mkdir(parents=True, exist_ok=True)

            # If it's SVG, try to convert to PNG
            if url.lower().endswith('.svg'):
                try:
                    import cairosvg
                    png_bytes = cairosvg.svg2png(bytestring=response.content, output_width=800)
                    img = Image.open(BytesIO(png_bytes))
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    img.save(save_path, 'PNG', optimize=True)
                    logger.info(f"Converted SVG to PNG and saved to {save_path}")
                    return True
                except Exception as e:
                    logger.warning(f"Could not convert SVG: {e}")
                    return False

            # If it's other image format, convert to PNG
            elif any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.gif', '.bmp', '.png']):
                try:
                    img = Image.open(BytesIO(response.content))
                    if img.mode != 'RGBA':
                        img = img.convert('RGBA')
                    img.save(save_path, 'PNG')
                    logger.info(f"Downloaded and saved logo to {save_path}")
                    return True
                except Exception as e:
                    logger.warning(f"Could not process image: {e}")
                    return False

            else:
                logger.warning(f"Unsupported file format: {url}")
                return False

        except Exception as e:
            logger.error(f"Failed to download logo from {url}: {e}")
            return False

    def list_available_logos(self) -> Dict[str, List[str]]:
        """List all available logos in the system"""
        conference_logos = self._scan_directory(self.base_path / "conferences")
        institute_logos = self._scan_directory(self.base_path / "institutes")

        return {
            "conferences": sorted(conference_logos.keys()),
            "institutes": sorted(institute_logos.keys())
        }

    def extract_first_author_institution(self, paper_content: str) -> Optional[str]:
        """
        Extract first author's institution from paper content

        Args:
            paper_content: Paper text content (markdown format)

        Returns:
            First author's institution if found
        """
        logger.info("Looking for first author's institution...")

        # Focus on first 100 lines (authors usually appear here)
        lines = paper_content.split('\n')[:100]

        # Common institution patterns
        institution_patterns = [
            r"(?:University of|University) [\w\s]+",
            r"[\w\s]+ University",
            r"[\w\s]+ Institute of Technology",
            r"[\w\s]+ Institute",
            r"MIT|CMU|UCLA|UCSD|NYU|ETH|EPFL|Stanford|Berkeley|Harvard|Princeton|Oxford|Cambridge",
            r"Google Research|DeepMind|Microsoft Research|Facebook AI Research|OpenAI|NVIDIA Research",
            r"Max Planck Institute",
            r"[\w\s]+ College",
            r"[\w\s]+ Research",
            r"[\w\s]+ Lab",
            r"[\w\s]+ Laboratory"
        ]

        all_pattern = '|'.join(f'({p})' for p in institution_patterns)

        # First pass: look for lines with superscript 1 (¹), usually indicating first author affiliation
        first_institution = None
        for i, line in enumerate(lines):
            if 'abstract' in line.lower() or 'introduction' in line.lower():
                break

            if '¹' in line:
                matches = re.findall(all_pattern, line, re.IGNORECASE)
                if matches:
                    for match_groups in matches:
                        for inst in match_groups:
                            if inst:
                                first_institution = inst.strip()
                                logger.info(f"Found first author institution (from affiliation marker): {first_institution}")
                                break
                        if first_institution:
                            break
            if first_institution:
                break

        # Second pass: if no superscript found, look for institution after author name
        if not first_institution:
            for i, line in enumerate(lines):
                if 'abstract' in line.lower() or 'introduction' in line.lower():
                    break

                if i < 2:
                    continue

                if '(' in line and ')' in line:
                    paren_content = re.findall(r'\((.*?)\)', line)
                    for content in paren_content:
                        inst_matches = re.findall(all_pattern, content, re.IGNORECASE)
                        if inst_matches:
                            for match_groups in inst_matches:
                                for inst in match_groups:
                                    if inst:
                                        first_institution = inst.strip()
                                        logger.info(f"Found first author institution (from parentheses): {first_institution}")
                                        break
                                if first_institution:
                                    break
                        if first_institution:
                            break
                if first_institution:
                    break

        # Third pass: if still not found, just look for first mentioned institution
        if not first_institution:
            for line in lines[:30]:
                if 'abstract' in line.lower() or 'introduction' in line.lower():
                    break

                matches = re.findall(all_pattern, line, re.IGNORECASE)
                if matches:
                    for match_groups in matches:
                        for inst in match_groups:
                            if inst:
                                first_institution = inst.strip()
                                logger.info(f"Found institution (general search): {first_institution}")
                                break
                        if first_institution:
                            break
                if first_institution:
                    break

        if not first_institution:
            logger.warning("No institution found in author section")
            return None

        logger.info(f"Extracted institution: '{first_institution}'")
        return first_institution


def get_logo_dimensions(logo_path: str, target_height: float) -> Tuple[float, float]:
    """
    Calculate logo width maintaining aspect ratio

    Args:
        logo_path: Logo image path
        target_height: Target height (inches)

    Returns:
        (width, height) tuple (inches)
    """
    try:
        with Image.open(logo_path) as img:
            aspect_ratio = img.width / img.height
            target_width = target_height * aspect_ratio
            return target_width, target_height
    except Exception:
        # If unable to read image, return square
        return target_height, target_height


def logo_manager_tool(
    action: str,
    base_path: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Logo manager tool entry function

    Args:
        action: Action type (get_logo, get_logo_url, list_logos, extract_institution, get_dimensions)
        base_path: Base path for logo storage (if not provided, reads from environment variable LOGO_STORE_BASE_PATH, defaults to "logo_store")
        **kwargs: Parameters required for each action

    Returns:
        Operation result dictionary
    """
    try:
        # If no base_path provided, read from environment variable
        if base_path is None:
            base_path = os.getenv('LOGO_STORE_BASE_PATH', 'logo_store')

        manager = LogoManager(base_path)

        if action == "get_logo":
            return _get_logo(manager, **kwargs)
        elif action == "get_logo_url":
            return _get_logo_url(manager, **kwargs)
        elif action == "list_logos":
            return _list_logos(manager)
        elif action == "extract_institution":
            return _extract_institution(manager, **kwargs)
        elif action == "get_dimensions":
            return _get_dimensions(**kwargs)
        else:
            return {
                "status": "error",
                "error": f"Unknown action: {action}. Available actions: get_logo, get_logo_url, list_logos, extract_institution, get_dimensions"
            }
    except Exception as e:
        logger.error(f"Error executing action '{action}': {e}", exc_info=True)
        return {
            "status": "error",
            "error": f"Error executing action '{action}': {str(e)}",
            "error_type": type(e).__name__
        }


def _get_logo(manager: LogoManager, name: str = "", category: str = "auto", use_google: bool = False, **kwargs) -> Dict[str, Any]:
    """Get logo path"""
    if not name:
        return {
            "status": "error",
            "error": "Parameter 'name' is required for get_logo action"
        }

    logo_path = manager.get_logo_path(name, category, use_google)

    if logo_path and logo_path.exists():
        return {
            "status": "success",
            "action": "get_logo",
            "logo_path": str(logo_path.absolute()),
            "name": name,
            "category": category,
            "message": f"Successfully found logo for '{name}' at {logo_path}"
        }
    else:
        return {
            "status": "error",
            "action": "get_logo",
            "name": name,
            "category": category,
            "error": f"Could not find or download logo for '{name}'"
        }


def _list_logos(manager: LogoManager, **kwargs) -> Dict[str, Any]:
    """List all available logos"""
    available_logos = manager.list_available_logos()

    return {
        "status": "success",
        "action": "list_logos",
        "logos": available_logos,
        "total_conferences": len(available_logos.get("conferences", [])),
        "total_institutes": len(available_logos.get("institutes", [])),
        "message": f"Found {len(available_logos.get('conferences', []))} conference logos and {len(available_logos.get('institutes', []))} institute logos"
    }


def _extract_institution(manager: LogoManager, paper_content: str = "", **kwargs) -> Dict[str, Any]:
    """Extract institution information from paper content"""
    if not paper_content:
        return {
            "status": "error",
            "error": "Parameter 'paper_content' is required for extract_institution action"
        }

    institution = manager.extract_first_author_institution(paper_content)

    if institution:
        return {
            "status": "success",
            "action": "extract_institution",
            "institution": institution,
            "message": f"Successfully extracted institution: '{institution}'"
        }
    else:
        return {
            "status": "error",
            "action": "extract_institution",
            "error": "Could not extract institution from paper content"
        }


def _get_dimensions(logo_path: str = "", target_height: float = 0, **kwargs) -> Dict[str, Any]:
    """Get logo dimensions (maintaining aspect ratio)"""
    if not logo_path:
        return {
            "status": "error",
            "error": "Parameter 'logo_path' is required for get_dimensions action"
        }
    if not target_height:
        return {
            "status": "error",
            "error": "Parameter 'target_height' is required for get_dimensions action"
        }

    if not os.path.exists(logo_path):
        return {
            "status": "error",
            "error": f"Logo file does not exist: {logo_path}"
        }

    width, height = get_logo_dimensions(logo_path, target_height)

    return {
        "status": "success",
        "action": "get_dimensions",
        "logo_path": logo_path,
        "width": width,
        "height": height,
        "target_height": target_height,
        "message": f"Logo dimensions: {width:.2f}\" x {height:.2f}\" (aspect ratio preserved)"
    }


def _get_logo_url(manager: LogoManager, name: str = "", use_google: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Get image link URL based on institution English name

    Args:
        name: English name of institution or conference
        use_google: Whether to use Google search (requires API key), default is False

    Returns:
        Result dictionary containing image URL
    """
    if not name:
        return {
            "status": "error",
            "error": "Parameter 'name' is required for get_logo_url action"
        }

    logger.info(f"Searching for logo URL: '{name}'")

    search_query = f"{name} logo"
    logger.info(f"Search query: '{search_query}'")

    # Use search_logo_web method to get URL
    url = manager.search_logo_web(search_query, use_google=use_google)

    if url:
        logger.info(f"Found logo URL: {url[:100]}...")
        return {
            "status": "success",
            "action": "get_logo_url",
            "name": name,
            "url": url,
            "message": f"Successfully found logo URL for '{name}'"
        }
    else:
        logger.warning(f"No logo URL found for: {name}")
        return {
            "status": "error",
            "action": "get_logo_url",
            "name": name,
            "error": f"Could not find logo URL for '{name}'. Try using use_google=True or check the institution name."
        }


def main():
    """Test function to demonstrate logo manager tool functionality."""
    print("Logo Manager Tool Testing Started...")
    print("=" * 80)

    # Test 1: List logos
    print("\nTest 1: List all available logos")
    result = logo_manager_tool(action="list_logos")
    if result["status"] == "success":
        print("Success: Listed logos")
        print(f"  Conference logos: {result['total_conferences']}")
        print(f"  Institute logos: {result['total_institutes']}")
    else:
        print(f"Failed: {result.get('error')}")

    # Test 2: Get logo
    print("\nTest 2: Get specific logo")
    result = logo_manager_tool(action="get_logo", name="Shanghai Innovation Institute", category="institute")
    if result["status"] == "success":
        print("Success: Retrieved logo")
        print(f"  Path: {result['logo_path']}")
    else:
        print(f"Failed: {result.get('error')}")

    print("\n" + "=" * 80)
    print("Logo Manager Tool Testing Completed!")

    print("\nUsage Tips:")
    print("  • logo_store contains conference and institute logos")
    print("  • Supports fuzzy matching and automatic download")
    print("  • Can extract institution information from papers")
    print("  • Can get logo dimension information")


if __name__ == "__main__":
    main()
