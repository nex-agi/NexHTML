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
Three-column height detection tool
Detects the height of three columns in HTML poster and determines if they are balanced
"""

import os
import asyncio
import statistics
from typing import Dict, Any, Optional
from collections import defaultdict

# Check dependencies
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# Configuration
AVAILABLE_HEIGHT_PER_COLUMN = 1000


def _generate_suggestions(result: Dict[str, Any], available_height: int) -> Dict[str, Any]:
    """
    Generate detailed adjustment suggestions based on height detection results

    Args:
        result: Height detection results
        available_height: Available height

    Returns:
        Dictionary containing detailed suggestions
    """
    # Parse column height percentages
    col_heights = {}
    col_pixels = {}
    for i in range(1, 4):
        col_key = f"column_{i}"
        height_str = result.get(col_key, "0%")
        # Parse percentage
        height_percent = float(height_str.rstrip('%'))
        col_heights[i] = height_percent
        col_pixels[i] = (height_percent / 100) * available_height

    # Find highest and lowest columns
    max_col = max(col_heights, key=col_heights.get)
    min_col = min(col_heights, key=col_heights.get)
    max_height = col_heights[max_col]
    min_height = col_heights[min_col]

    # Calculate difference
    height_diff_percent = max_height - min_height
    height_diff_px = col_pixels[max_col] - col_pixels[min_col]

    # Determine balance status
    is_balanced = result.get("is_balanced", False)

    # Generate suggestions
    suggestions = {
        "overall_status": "",
        "column_analysis": {},
        "recommended_actions": [],
        "balance_tips": ""
    }

    # Overall status (5% threshold)
    if height_diff_percent <= 5:
        suggestions["overall_status"] = f"✓ Three columns well balanced, difference only {height_diff_percent:.1f}% ({height_diff_px:.0f}px), no adjustment needed"
    elif height_diff_percent <= 20:
        suggestions["overall_status"] = f"🔴 Column height difference {height_diff_percent:.1f}% ({height_diff_px:.0f}px), **must adjust content distribution**"
    else:
        suggestions["overall_status"] = f"🔴🔴 Severe imbalance in column heights, difference {height_diff_percent:.1f}% ({height_diff_px:.0f}px), **mandatory re-layout required**"

    # Column-by-column analysis
    for i in range(1, 4):
        col_name = f"Column {i}"
        height = col_heights[i]
        pixels = col_pixels[i]
        remaining = available_height - pixels

        analysis = {
            "height_usage": f"{height:.1f}%",
            "pixels_used": f"{pixels:.0f}px",
            "remaining_space": f"{remaining:.0f}px",
            "status": "",
            "suggestion": ""
        }

        # Determine column status
        if height < 60:
            analysis["status"] = "❌ Space utilization too low"
            analysis["suggestion"] = f"{remaining:.0f}px space remaining, suggest adding content:\n  - Move content from other columns (e.g., images, conclusion paragraphs)\n  - Add more experimental results or case studies\n  - Add visualization charts or example images"
        elif height < 75:
            analysis["status"] = "⚠ Insufficient space utilization"
            analysis["suggestion"] = f"{remaining:.0f}px space remaining, suggest adding:\n  - Move some content from highest column\n  - Add related work or background introduction\n  - Expand detailed description of existing sections"
        elif height < 90:
            analysis["status"] = "✓ Good space utilization"
            analysis["suggestion"] = f"{remaining:.0f}px space remaining, basically reasonable, can fine-tune:\n  - Can receive content if other columns are too full\n  - Maintain current content density"
        elif height < 100:
            analysis["status"] = "⚠ Space near saturation"
            analysis["suggestion"] = f"Only {remaining:.0f}px space remaining, suggest:\n  - Consider moving some content to columns with more space\n  - Streamline current content, keep core information\n  - Check for redundant content that can be removed"
        else:
            analysis["status"] = "❌ Space overloaded"
            analysis["suggestion"] = f"Exceeded available space by {pixels - available_height:.0f}px, must adjust:\n  - Move some content to other columns\n  - Remove secondary content or reduce font size\n  - Compress image sizes or reduce number of images"

        suggestions["column_analysis"][col_name] = analysis

    # Recommended actions (5% mandatory threshold)
    if height_diff_percent > 5:
        # Use mandatory language
        move_amount = height_diff_px / 2

        # Mandatory action for highest column
        suggestions["recommended_actions"].append(
            f"🔴 **Must do**: Move {move_amount:.0f}px content out from [Column {max_col}] ({max_height:.1f}%)"
        )

        # Mandatory action for lowest column
        suggestions["recommended_actions"].append(
            f"🔴 **Must do**: Add {move_amount:.0f}px content to [Column {min_col}] ({min_height:.1f}%)"
        )

        # Specific content requirements
        if height_diff_percent > 30:
            suggestions["recommended_actions"].append(
                "‼️ **Mandatory**: Must move entire sections (e.g., Methods, Results, Related Work, etc.)"
            )
            suggestions["recommended_actions"].append(
                f"‼️ **Specific action**: Reorganize three-column content distribution, move at least 1 complete section from highest column to lowest column"
            )
        elif height_diff_percent > 20:
            suggestions["recommended_actions"].append(
                "‼️ **Mandatory**: Must move 1-2 complete paragraphs or one medium-sized image"
            )
            suggestions["recommended_actions"].append(
                f"‼️ **Specific action**: Select content block of approximately {move_amount:.0f}px from Column {max_col} and move to Column {min_col}"
            )
        elif height_diff_percent > 10:
            suggestions["recommended_actions"].append(
                "‼️ **Mandatory**: Must move at least 1 paragraph or adjust image size"
            )
            suggestions["recommended_actions"].append(
                f"‼️ **Specific action**: Reduce image in Column {max_col} or move a text paragraph to Column {min_col}"
            )
        else:  # 5% < diff <= 10%
            suggestions["recommended_actions"].append(
                "⚠️ **Adjustment required**: Move small text or slightly adjust image size"
            )
            suggestions["recommended_actions"].append(
                f"⚠️ **Specific action**: Adjust image height in Column {max_col} to reduce {move_amount:.0f}px, or move small amount of text to Column {min_col}"
            )
    elif height_diff_percent > 0:
        # 0-5%: Minor suggestion
        suggestions["recommended_actions"].append(
            f"💡 Minor difference ({height_diff_percent:.1f}%), optional adjustment: Fine-tune image size or font spacing"
        )

    # Balance tips (mandatory judgment)
    balance_tips = []

    # Check for extreme cases
    if max_height > 95:
        balance_tips.append("🔴 **Serious issue**: Highest column near saturation (>95%), must remove content immediately!")

    if min_height < 65:
        balance_tips.append("🔴 **Serious issue**: Lowest column utilization too low (<65%), must add substantial content!")

    # Middle column suggestion
    middle_col = 6 - max_col - min_col  # 1+2+3=6
    middle_height = col_heights[middle_col]
    if 75 <= middle_height <= 85:
        balance_tips.append(f"✓ Column {middle_col} height moderate ({middle_height:.1f}%), can serve as buffer zone for balance adjustment")

    # Overall suggestion (5% mandatory threshold)
    if height_diff_percent <= 5:
        balance_tips.append(f"✅ Perfect balance: difference only {height_diff_percent:.1f}%, no adjustment needed")
    elif height_diff_percent < 10:
        balance_tips.append(f"⚠️ Needs adjustment: difference {height_diff_percent:.1f}%, fine-tuning can achieve balance")
    elif height_diff_percent < 20:
        balance_tips.append(f"🔴 **Must adjust**: difference {height_diff_percent:.1f}%, must move 1-2 elements")
    elif height_diff_percent < 30:
        balance_tips.append(f"🔴🔴 **Mandatory**: difference {height_diff_percent:.1f}%, must move entire paragraph or large image")
    else:
        balance_tips.append(f"🔴🔴🔴 **Urgent adjustment**: difference as high as {height_diff_percent:.1f}%, must reorganize overall layout!")

    # Add specific execution steps (only when adjustment needed)
    if height_diff_percent > 5:
        balance_tips.append(f"\n**Execution steps**:")
        balance_tips.append(f"1️⃣ Check movable content in Column {max_col} (paragraphs, images, tables)")
        balance_tips.append(f"2️⃣ Select content block of approximately {height_diff_px/2:.0f}px")
        balance_tips.append(f"3️⃣ Move it to appropriate position in Column {min_col}")
        balance_tips.append(f"4️⃣ Re-detect height, ensure difference reduced to within 5%")

    suggestions["balance_tips"] = "\n".join(balance_tips) if balance_tips else "✅ All columns perfectly balanced"

    return suggestions


def height_detect_tool(
    html_path: str,
    available_height: int = AVAILABLE_HEIGHT_PER_COLUMN,
    **kwargs
) -> Dict[str, Any]:
    """
    Detect the heights of three columns in HTML poster and determine if column heights are balanced.

    Args:
        html_path: HTML file path
        available_height: Available height per column (pixels, default 1000px)
        **kwargs: Other parameters

    Returns:
        Dict[str, Any]: Contains the following fields:
            - status: "success" or "error"
            - message: Operation result description
            - column_heights: Three-column height information dictionary (on success)
                - column_1: First column height utilization (e.g., "85.2%")
                - column_2: Second column height utilization (e.g., "82.7%")
                - column_3: Third column height utilization (e.g., "87.1%")
            - is_balanced: Whether balanced (height difference within 20%)
            - max_height: Highest column height
            - min_height: Lowest column height
            - height_diff: Height difference (pixels and percentage)
            - suggestions: Detailed adjustment suggestions (on success)
                - overall_status: Overall balance status assessment
                - column_analysis: Detailed analysis for each column (Column 1, Column 2, Column 3)
                    - height_usage: Height utilization
                    - pixels_used: Pixels used
                    - remaining_space: Remaining space
                    - status: Status assessment
                    - suggestion: Specific adjustment suggestions
                - recommended_actions: Recommended actions list
                - balance_tips: Balance tips
            - html_path: Input HTML path (on success)
            - error: Error message (on failure)
    """
    # Check dependencies
    if not PLAYWRIGHT_AVAILABLE:
        return {
            "status": "error",
            "error": "Missing dependency: playwright. Please install using: pip install playwright && playwright install"
        }

    try:
        # Verify input file exists
        if not os.path.exists(html_path):
            return {
                "status": "error",
                "error": f"HTML file does not exist: {html_path}"
            }

        # Convert to absolute path
        html_path = os.path.abspath(html_path)

        # Execute height detection
        result = asyncio.run(_detect_columns(html_path, available_height))

        if result is None:
            return {
                "status": "error",
                "error": "Three-column structure not detected"
            }

        # Generate detailed suggestions
        suggestions = _generate_suggestions(result, available_height)

        return {
            "status": "success",
            "message": "Three-column height detection completed",
            "column_heights": {
                "column_1": result.get("column_1", "0%"),
                "column_2": result.get("column_2", "0%"),
                "column_3": result.get("column_3", "0%")
            },
            "is_balanced": result.get("is_balanced", False),
            "max_height": result.get("max_height", "0px"),
            "min_height": result.get("min_height", "0px"),
            "height_diff": result.get("height_diff", "0px (0%)"),
            "suggestions": suggestions,
            "html_path": html_path
        }
    except FileNotFoundError as e:
        return {
            "status": "error",
            "error": f"File not found: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Height detection failed: {str(e)}"
        }


async def _detect_columns(
    html_path: str,
    available_height: int = AVAILABLE_HEIGHT_PER_COLUMN
) -> Optional[Dict[str, Any]]:
    """
    Three-column detection script (improved version)
    Input: HTML file absolute path
    Output: Visual content height of each of the three columns

    Detection strategy:
    1. Priority: Look for .column class elements (most direct)
    2. If not found, try width grouping to find groups that can be divided into 3 columns
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(f"file://{html_path}")

        # 策略1: 优先查找 .column 类的元素，并计算实际内容高度
        column_data = await page.evaluate("""
        () => {
            const cols = document.querySelectorAll('div.column, div[class*="column"], div[class*="col-"], div[class~="col"]');
            if (cols.length === 3) {
                return [...cols].map(col => {
                    const rect = col.getBoundingClientRect();
                    const sections = col.querySelectorAll('.section');

                    // Calculate actual content height
                    let contentHeight = 0;
                    sections.forEach(section => {
                        contentHeight += section.scrollHeight;
                    });

                    // Get gap value (from computed style)
                    const computedStyle = window.getComputedStyle(col);
                    const gap = parseFloat(computedStyle.gap) || 25; // Default 25px

                    // Add gap
                    const totalGap = (sections.length - 1) * gap;
                    const actualHeight = contentHeight + totalGap;

                    return {
                        x: rect.left,
                        y: rect.top,
                        width: rect.width,
                        containerHeight: col.scrollHeight,
                        actualHeight: actualHeight,
                        sectionsCount: sections.length,
                        className: col.className
                    };
                });
            }
            return null;
        }
        """)

        col_heights = []

        if column_data and len(column_data) == 3:
            # Found clear three-column structure
            column_data.sort(key=lambda d: d["x"])
            col_heights = [d["actualHeight"] for d in column_data]
        else:
            # Strategy 2: Use width grouping method
            divs = await page.evaluate("""
            () => {
                return [...document.querySelectorAll('div')].map((div, i) => {
                    const rect = div.getBoundingClientRect();
                    return {
                        i,
                        className: div.className,
                        x: rect.left,
                        y: rect.top,
                        width: rect.width,
                        height: div.scrollHeight
                    };
                });
            }
            """)

            # Filter: both width and height should be reasonable
            divs = [d for d in divs if d["width"] > 50 and d["height"] > 50]

            # Group by width
            groups = defaultdict(list)
            for d in divs:
                groups[round(d["width"], 1)].append(d)

            # Look for width groups that can be divided into 3 columns
            best_group = None
            for width, lst in groups.items():
                if len(lst) < 3:
                    continue

                # Sort by x coordinate
                lst.sort(key=lambda d: d["x"])

                # Try to divide into columns
                temp_columns = []
                current_col = [lst[0]]
                for d in lst[1:]:
                    if abs(d["x"] - statistics.mean([x["x"] for x in current_col])) < 10:
                        current_col.append(d)
                    else:
                        temp_columns.append(current_col)
                        current_col = [d]
                temp_columns.append(current_col)

                # If exactly 3 columns and width in reasonable range (200-800px)
                if len(temp_columns) == 3 and 200 <= width <= 800:
                    best_group = (width, temp_columns)
                    break

            if not best_group:
                await browser.close()
                return None

            _, columns = best_group
            columns = sorted(columns, key=lambda c: statistics.mean([x["x"] for x in c]))

            # Calculate actual content height for each column
            for col in columns:
                center_x = statistics.mean([d["x"] for d in col])
                actual_h = await page.evaluate(f"""
                () => {{
                    const divs = [...document.querySelectorAll('div')];
                    // Find the column container at this position
                    const columnDiv = divs.find(d => {{
                        const r = d.getBoundingClientRect();
                        return Math.abs(r.left - {center_x}) < 50 && d.classList.contains('column');
                    }});

                    if (columnDiv) {{
                        const sections = columnDiv.querySelectorAll('.section');
                        let contentHeight = 0;
                        sections.forEach(section => {{
                            contentHeight += section.scrollHeight;
                        }});

                        const computedStyle = window.getComputedStyle(columnDiv);
                        const gap = parseFloat(computedStyle.gap) || 25;
                        const totalGap = (sections.length - 1) * gap;

                        return contentHeight + totalGap;
                    }}

                    // If .column container not found, fall back to finding max scrollHeight
                    const targetDivs = divs.filter(d => {{
                        const r = d.getBoundingClientRect();
                        return Math.abs(r.left - {center_x}) < 50;
                    }});
                    return Math.max(...targetDivs.map(d => d.scrollHeight || 0));
                }}
                """)
                col_heights.append(actual_h)

        # Verify results
        if len(col_heights) != 3:
            await browser.close()
            return None

        # Calculate balance
        max_height = max(col_heights)
        min_height = min(col_heights)
        height_diff = max_height - min_height
        height_diff_percent = (height_diff / available_height) * 100
        is_balanced = height_diff <= available_height * 0.2

        await browser.close()

        # Build results
        col_height_dict = {}
        for i, h in enumerate(col_heights, 1):
            col_height_dict[f"column_{i}"] = f"{100*h/available_height:.1f}%"

        col_height_dict["is_balanced"] = is_balanced
        col_height_dict["max_height"] = f"{max_height}px"
        col_height_dict["min_height"] = f"{min_height}px"
        col_height_dict["height_diff"] = f"{height_diff}px ({height_diff_percent:.1f}%)"

        return col_height_dict
