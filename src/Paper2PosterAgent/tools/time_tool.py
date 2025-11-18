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

"""Time tool implementation for getting current date and time information."""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
import zoneinfo

logger = logging.getLogger(__name__)


def get_current_time(timezone: str = "local") -> Dict[str, Any]:
    """
    Get current date and time information.

    Args:
        timezone: Timezone name (e.g., 'Asia/Shanghai', 'UTC', 'America/New_York')
                 or 'local' for local time. Default is 'local'.

    Returns:
        Dict containing current time information including:
        - status: success/error
        - datetime: formatted datetime string (YYYY-MM-DD HH:MM:SS)
        - date: formatted date string (YYYY-MM-DD)
        - time: formatted time string (HH:MM:SS)
        - timestamp: Unix timestamp (seconds since epoch)
        - timezone: timezone used
        - weekday: day of the week name
        - year, month, day: individual date components
    """
    try:
        # Get current time based on timezone
        if timezone == "local":
            current_time = datetime.now()
            tz_display = "local"
        else:
            try:
                tz = zoneinfo.ZoneInfo(timezone)
                current_time = datetime.now(tz)
                tz_display = timezone
            except zoneinfo.ZoneInfoNotFoundError:
                return {
                    "status": "error",
                    "error": f"Invalid timezone: {timezone}. Use 'local' or valid timezone names like 'Asia/Shanghai', 'UTC', 'America/New_York'",
                    "timezone": timezone
                }

        # Format and return time information
        result = {
            "status": "success",
            "datetime": current_time.strftime("%Y-%m-%d %H:%M:%S"),
            "date": current_time.strftime("%Y-%m-%d"),
            "time": current_time.strftime("%H:%M:%S"),
            "timestamp": int(current_time.timestamp()),
            "timezone": tz_display,
            "weekday": current_time.strftime("%A"),
            "year": current_time.year,
            "month": current_time.month,
            "day": current_time.day,
            "hour": current_time.hour,
            "minute": current_time.minute,
            "second": current_time.second
        }

        logger.info(f"Time retrieved successfully for timezone: {tz_display}")
        return result

    except Exception as e:
        logger.error(f"Error getting current time: {e}")
        return {
            "status": "error",
            "error": f"Failed to get current time: {str(e)}",
            "error_type": type(e).__name__,
            "timezone": timezone
        }


def format_time(
    timestamp: Optional[int] = None,
    format_string: str = "%Y-%m-%d %H:%M:%S",
    timezone: str = "local"
) -> Dict[str, Any]:
    """
    Format a timestamp or current time with custom format.

    Args:
        timestamp: Unix timestamp to format. If None, uses current time.
        format_string: Python datetime format string (default: "%Y-%m-%d %H:%M:%S")
        timezone: Timezone for formatting

    Returns:
        Dict containing formatted time information
    """
    try:
        # Get datetime object
        if timestamp is None:
            if timezone == "local":
                dt = datetime.now()
            else:
                tz = zoneinfo.ZoneInfo(timezone)
                dt = datetime.now(tz)
        else:
            if timezone == "local":
                dt = datetime.fromtimestamp(timestamp)
            else:
                tz = zoneinfo.ZoneInfo(timezone)
                dt = datetime.fromtimestamp(timestamp, tz)

        # Format the time
        formatted = dt.strftime(format_string)

        return {
            "status": "success",
            "formatted_time": formatted,
            "format_string": format_string,
            "timezone": timezone,
            "timestamp": int(dt.timestamp())
        }

    except ValueError as e:
        return {
            "status": "error",
            "error": f"Invalid timestamp or format string: {str(e)}",
            "timestamp": timestamp,
            "format_string": format_string
        }
    except zoneinfo.ZoneInfoNotFoundError:
        return {
            "status": "error",
            "error": f"Invalid timezone: {timezone}",
            "timezone": timezone
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }


def main():
    """Test function to demonstrate time tool functionality."""
    print("Time Tool Testing Started...")
    print("=" * 60)

    # Test 1: Get local time
    print("\nTest 1: Get Local Time")
    result = get_current_time()
    if result["status"] == "success":
        print(f"Success: Retrieved time")
        print(f"DateTime: {result['datetime']}")
        print(f"Date: {result['date']}")
        print(f"Time: {result['time']}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"Weekday: {result['weekday']}")
    else:
        print(f"Failed: {result.get('error')}")

    # Test 2: Get time with timezone
    print("\nTest 2: Get Time with Timezone (Asia/Shanghai)")
    result = get_current_time(timezone="Asia/Shanghai")
    if result["status"] == "success":
        print(f"Success: Retrieved time")
        print(f"Shanghai Time: {result['datetime']}")
        print(f"Timezone: {result['timezone']}")
    else:
        print(f"Failed: {result.get('error')}")

    # Test 3: Get UTC time
    print("\nTest 3: Get UTC Time")
    result = get_current_time(timezone="UTC")
    if result["status"] == "success":
        print(f"Success: Retrieved time")
        print(f"UTC Time: {result['datetime']}")
        print(f"Timezone: {result['timezone']}")
    else:
        print(f"Failed: {result.get('error')}")

    # Test 4: Invalid timezone
    print("\nTest 4: Invalid Timezone Test")
    result = get_current_time(timezone="Invalid/Timezone")
    if result["status"] == "error":
        print(f"Success: Correctly handled invalid timezone")
        print(f"Error message: {result['error']}")
    else:
        print(f"Warning: Should have returned error but succeeded")

    # Test 5: Format time
    print("\nTest 5: Custom Time Formatting")
    result = format_time(format_string="%Y-%m-%d %H:%M:%S")
    if result["status"] == "success":
        print(f"Success: Formatted time")
        print(f"Formatted result: {result['formatted_time']}")
    else:
        print(f"Failed: {result.get('error')}")

    # Test 6: Format timestamp
    print("\nTest 6: Format Specific Timestamp")
    result = format_time(timestamp=1704067200, timezone="Asia/Shanghai")  # 2024-01-01 00:00:00 UTC
    if result["status"] == "success":
        print(f"Success: Formatted timestamp")
        print(f"Formatted result: {result['formatted_time']}")
        print(f"Timezone: {result['timezone']}")
    else:
        print(f"Failed: {result.get('error')}")

    print("\n" + "=" * 60)
    print("Time Tool Testing Completed!")

    # Usage tips
    print("\nUsage Tips:")
    print("  • Use 'local' to get local time")
    print("  • Use standard timezone names like 'Asia/Shanghai', 'UTC', 'America/New_York'")
    print("  • Returned timestamp can be used for time comparison and calculation")
    print("  • weekday field returns English weekday name")


if __name__ == "__main__":
    main()
