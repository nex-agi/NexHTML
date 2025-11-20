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
Kaggle dataset download tool
Downloads datasets from Kaggle using the kagglehub library
"""

import os
import shutil
from typing import Any, Dict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def KaggleDownload(dataset_name: str, download_path: str) -> Dict[str, Any]:
    """
    Download a Kaggle dataset to the specified path using kagglehub library.
    Supports reading Kaggle authentication info from environment variables:
    - KAGGLE_USERNAME: Kaggle username
    - KAGGLE_KEY: Kaggle API Key

    Also supports traditional ~/.kaggle/kaggle.json file authentication.

    Args:
        dataset_name: Kaggle dataset name, format "username/dataset-name"
        download_path: Target path for dataset download (absolute path)

    Returns:
        Dict[str, Any]: Contains the following fields:
            - success: True if download succeeded, False otherwise
            - tool_name: "KaggleDownload"
            - dataset_name: Name of the downloaded dataset (on success)
            - download_path: Final path where data was saved (on success)
            - cache_path: Kagglehub cache path (on success)
            - downloaded_files: List of downloaded file paths (on success)
            - message: Success message (on success)
            - error: Error message (on failure)
            - error_type: Error type (on failure)
    """
    try:
        import kagglehub

        # Check authentication configuration
        kaggle_username = os.environ.get("KAGGLE_USERNAME")
        kaggle_key = os.environ.get("KAGGLE_KEY")

        # If environment variables are configured, set them (kagglehub will read them automatically)
        if kaggle_username and kaggle_key:
            os.environ["KAGGLE_USERNAME"] = kaggle_username
            os.environ["KAGGLE_KEY"] = kaggle_key

        # Validate dataset name format
        if "/" not in dataset_name:
            return {
                "success": False,
                "tool_name": "KaggleDownload",
                "error": f"Invalid dataset name format: {dataset_name}. Expected format: 'username/dataset-name'",
                "error_type": "ValueError"
            }

        # Download dataset using kagglehub (downloads to cache directory)
        cache_path = kagglehub.dataset_download(dataset_name)

        # Create target directory if it doesn't exist
        if not os.path.exists(download_path):
            os.makedirs(download_path, exist_ok=True)

        # Copy data from cache path to target path
        target_path = os.path.join(download_path, os.path.basename(dataset_name))
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        shutil.copytree(cache_path, target_path)

        # List downloaded files
        downloaded_files = []
        for root, _, files in os.walk(target_path):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, target_path)
                downloaded_files.append(rel_path)

        return {
            "success": True,
            "tool_name": "KaggleDownload",
            "dataset_name": dataset_name,
            "download_path": target_path,
            "cache_path": cache_path,
            "downloaded_files": downloaded_files,
            "message": f"Successfully downloaded dataset '{dataset_name}' to '{target_path}'"
        }

    except ImportError:
        return {
            "success": False,
            "tool_name": "KaggleDownload",
            "error": "kagglehub library is not installed. Please install it with: pip install kagglehub",
            "error_type": "ImportError"
        }
    except Exception as e:
        return {
            "success": False,
            "tool_name": "KaggleDownload",
            "error": str(e),
            "error_type": type(e).__name__
        }
