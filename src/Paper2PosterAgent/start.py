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

"""Start the Paper2PosterAgent - An intelligent academic poster generation AI system."""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# ANSI Color codes
class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"

    # Basic colors
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

    # Background colors
    BG_RED = "\033[101m"
    BG_GREEN = "\033[102m"
    BG_BLUE = "\033[104m"

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"{Colors.GREEN}✓ Loaded environment variables from {env_path}{Colors.RESET}")
    else:
        print(f"{Colors.YELLOW}⚠️  No .env file found at {env_path}{Colors.RESET}")
except ImportError:
    print(f"{Colors.YELLOW}⚠️  python-dotenv not installed, skipping .env file loading{Colors.RESET}")

import langfuse
import requests
from nexau.archs.config.config_loader import load_agent_config
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style

# Configure logging: only show WARNING and above levels, hide framework's detailed INFO logs
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s: %(message)s'
)

# Disable nexau framework's detailed logs
logging.getLogger('nexau').setLevel(logging.WARNING)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)


def get_date():
    """Get current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def colorize_response(text: str) -> str:
    """
    Add rich colors and markers to Agent responses

    Supported patterns:
    - Tool calls → Yellow + 🔧
    - Success messages → Green + ✓
    - Errors/warnings → Red + ✗
    - File paths → Cyan + 📁
    - Numbers/percentages → Blue
    - Quoted content → Magenta
    - Step markers → Numbered colored markers
    """
    import re

    lines = text.split('\n')
    colored_lines = []
    step_counter = 0

    for line in lines:
        # Keep empty lines as-is
        if not line.strip():
            colored_lines.append(line)
            continue

        # Step markers (Step 1, 步骤 1, 1., etc)
        step_match = re.match(r'^(Step|步骤|阶段)\s*(\d+)', line, re.IGNORECASE)
        if step_match:
            step_num = step_match.group(2)
            step_counter += 1
            # Use different colors in rotation
            step_colors = [Colors.CYAN, Colors.MAGENTA, Colors.YELLOW, Colors.GREEN]
            color = step_colors[step_counter % len(step_colors)]
            colored_lines.append(f"\n{color}{Colors.BOLD}{'▶' * 3} {line}{Colors.RESET}")
            continue

        # Tool calls
        if re.search(r'(使用工具|using tool|calling|tool call|调用|执行工具)', line, re.IGNORECASE):
            # Extract tool name
            tool_match = re.search(r'(tool|工具)[:：]?\s*(\w+)', line, re.IGNORECASE)
            if tool_match:
                tool_name = tool_match.group(2)
                colored_lines.append(f"{Colors.YELLOW}  🔧 Tool call: {Colors.BOLD}{tool_name}{Colors.RESET}")
            else:
                colored_lines.append(f"{Colors.YELLOW}  🔧 {line}{Colors.RESET}")
            continue

        # Success messages
        if re.search(r'(success|成功|完成|done|saved|generated|已生成|已保存)', line, re.IGNORECASE):
            if '✓' not in line and '✅' not in line:
                colored_lines.append(f"{Colors.GREEN}  ✓ {line}{Colors.RESET}")
            else:
                colored_lines.append(f"{Colors.GREEN}  {line}{Colors.RESET}")
            continue

        # Errors/warnings
        if re.search(r'(error|错误|失败|failed|warning|warn)', line, re.IGNORECASE):
            if '✗' not in line and '❌' not in line:
                colored_lines.append(f"{Colors.RED}  ✗ {line}{Colors.RESET}")
            else:
                colored_lines.append(f"{Colors.RED}  {line}{Colors.RESET}")
            continue

        # Processing/in progress
        if re.search(r'(processing|处理中|正在|analyzing|分析中)', line, re.IGNORECASE):
            colored_lines.append(f"{Colors.YELLOW}  ⟳ {line}{Colors.RESET}")
            continue

        # File paths
        if re.search(r'(/[\w/.-]+\.\w+|\\[\w\\.-]+\.\w+|[\w_-]+\.(png|pdf|html|json|md))', line):
            # Colorize path parts
            line = re.sub(
                r'(/[\w/.-]+\.\w+|\\[\w\\.-]+\.\w+|[\w_-]+\.(png|pdf|html|json|md))',
                f'{Colors.CYAN}{Colors.BOLD}\\g<0>{Colors.RESET}{Colors.WHITE}',
                line
            )
            # If no other markers, add file icon
            if not line.strip().startswith(('📁', '📄', '🖼️', '✓', '✗', '🔧')):
                colored_lines.append(f"{Colors.WHITE}  📁 {line}{Colors.RESET}")
            else:
                colored_lines.append(f"{Colors.WHITE}  {line}{Colors.RESET}")
            continue

        # Numbers, percentages, dimensions
        if re.search(r'\d+%|\d+x\d+|\d+\.\d+', line):
            line = re.sub(r'(\d+%|\d+x\d+|\d+\.\d+)', f'{Colors.BLUE}{Colors.BOLD}\\1{Colors.RESET}{Colors.WHITE}', line)
            colored_lines.append(f"{Colors.WHITE}  {line}{Colors.RESET}")
            continue

        # Quoted content
        if re.search(r'["\'"](.+?)["\'"]', line):
            line = re.sub(
                r'(["\'"])(.+?)(["\'"])',
                f'{Colors.MAGENTA}{Colors.BOLD}\\1\\2\\3{Colors.RESET}{Colors.WHITE}',
                line
            )
            colored_lines.append(f"{Colors.WHITE}  {line}{Colors.RESET}")
            continue

        # Heading lines (## or ###)
        if re.match(r'^#+\s+', line):
            level = len(re.match(r'^(#+)', line).group(1))
            if level == 1:
                colored_lines.append(f"\n{Colors.CYAN}{Colors.BOLD}{'═' * 60}{Colors.RESET}")
                colored_lines.append(f"{Colors.CYAN}{Colors.BOLD}{line}{Colors.RESET}")
                colored_lines.append(f"{Colors.CYAN}{Colors.BOLD}{'═' * 60}{Colors.RESET}")
            else:
                colored_lines.append(f"\n{Colors.CYAN}{Colors.BOLD}▸ {line.lstrip('#').strip()}{Colors.RESET}")
            continue

        # List items
        if re.match(r'^\s*[-*•]\s+', line):
            colored_lines.append(f"{Colors.GREEN}  • {line.lstrip('-*• ').strip()}{Colors.RESET}")
            continue

        # Numbered lists
        if re.match(r'^\s*\d+[\.)]\s+', line):
            colored_lines.append(f"{Colors.CYAN}  {line}{Colors.RESET}")
            continue

        # Default white, add indentation
        colored_lines.append(f"{Colors.WHITE}  {line}{Colors.RESET}")

    return '\n'.join(colored_lines)


def print_welcome():
    """Print welcome banner."""
    print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 80}")
    print("📊 Paper2PosterAgent - Academic Poster Generation System")
    print(f"{'=' * 80}{Colors.RESET}")
    print()
    print(f"{Colors.WHITE}Transform research papers into professional academic posters{Colors.RESET}")
    print(f"{Colors.WHITE}Supports: PDF → Markdown → Image Captions → HTML Poster{Colors.RESET}")
    print()


def print_examples():
    """Print usage examples."""
    print(f"{Colors.CYAN}📝 Example Commands:{Colors.RESET}")
    print(f"{Colors.WHITE}  • 'Generate poster from /path/to/paper.pdf'")
    print(f"  • 'Convert paper.pdf to poster with logos: logo1.png, logo2.png'")
    print(f"  • 'Create poster from research.pdf and include QR code'")
    print(f"  • 'Help me make a poster from my paper'")
    print(f"{Colors.RESET}")


def check_paper2md_service():
    """Check if MinerU paper2md service is available."""
    api_url = os.getenv("PAPER2MD_API_URL", "http://127.0.0.1:8000/file_parse")

    # Extract base URL (remove path)
    base_url = api_url.rsplit('/', 1)[0] if '/' in api_url.replace('http://', '').replace('https://', '') else api_url

    print(f"{Colors.BLUE}🔍 Checking MinerU service availability...{Colors.RESET}")
    print(f"{Colors.WHITE}   API URL: {api_url}{Colors.RESET}")

    try:
        # Try to connect to the service with a short timeout
        response = requests.get(base_url, timeout=3)
        print(f"{Colors.GREEN}✓ MinerU service is running and accessible{Colors.RESET}")
        return True
    except requests.exceptions.ConnectionError:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ ERROR: Cannot connect to MinerU service!{Colors.RESET}")
        print(f"\n{Colors.YELLOW}The Paper2Poster agent requires MinerU service to be running.{Colors.RESET}")
        print(f"{Colors.WHITE}Please start the service with:{Colors.RESET}")
        print(f"{Colors.CYAN}  cd MinerU && mineru-api --host 0.0.0.0 --port 8000{Colors.RESET}")
        print(f"\n{Colors.WHITE}Or update PAPER2MD_API_URL in .env if using a different service.{Colors.RESET}\n")
        return False
    except requests.exceptions.Timeout:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ ERROR: MinerU service timeout!{Colors.RESET}")
        print(f"{Colors.YELLOW}The service is not responding. Please check if it's running properly.{Colors.RESET}\n")
        return False
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ ERROR: Failed to check MinerU service: {e}{Colors.RESET}\n")
        return False


def main():
    """Start the Paper2PosterAgent with YAML-based agent configuration."""
    print_welcome()

    try:
        # Check for API key
        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("LLM_API_KEY")
        if not api_key or api_key == "your_api_key_here":
            print(f"\n{Colors.RED}{Colors.BOLD}❌ ERROR: API key not configured!{Colors.RESET}")
            print(f"\n{Colors.YELLOW}Please set your API key in one of these ways:{Colors.RESET}")
            print(f"{Colors.WHITE}  1. Edit .env and set LLM_API_KEY")
            print("  2. Export environment variable: export LLM_API_KEY=your_key")
            print(f"  3. Add api_key to config.yaml under llm_config{Colors.RESET}")
            print()
            return 1

        # Check MinerU paper2md service availability
        if not check_paper2md_service():
            return 1

        print()

        # Print examples
        print_examples()

        # Setup prompt_toolkit
        history = InMemoryHistory()
        prompt_style = Style.from_dict({
            'prompt': '#ff00ff bold',  # Magenta color
        })

        # Interactive mode
        print(f"{Colors.CYAN}💬 Enter your poster generation task (or 'exit' to quit){Colors.RESET}")
        print(f"{Colors.CYAN}💡 Each task is an independent conversation, no history context retained{Colors.RESET}")
        print(f"{Colors.CYAN}{'-' * 80}{Colors.RESET}")

        # Get script directory for loading config
        script_dir = Path(__file__).parent

        while True:
            try:
                print()
                user_message = prompt(
                    [('class:prompt', '📝 Your task: ')],
                    history=history,
                    style=prompt_style,
                    enable_history_search=True,
                    vi_mode=False,
                ).strip()

                if user_message.lower() in ['exit', 'quit', 'q']:
                    print(f"\n{Colors.CYAN}👋 Goodbye!{Colors.RESET}")
                    break

                if not user_message:
                    continue
            except (KeyboardInterrupt, EOFError):
                print(f"\n{Colors.CYAN}👋 Goodbye!{Colors.RESET}")
                break

            # Reload Agent for each task to ensure independent conversation context
            print(f"{Colors.BLUE}⚙️  Initializing independent conversation...{Colors.RESET}")
            poster_agent = load_agent_config(str(script_dir / "config.yaml"))

            print(f"\n{Colors.MAGENTA}{Colors.BOLD}╭{'─' * 78}╮{Colors.RESET}")
            print(f"{Colors.MAGENTA}{Colors.BOLD}│ 🤖 Paper2PosterAgent Response{' ' * 48}│{Colors.RESET}")
            print(f"{Colors.MAGENTA}{Colors.BOLD}╰{'─' * 78}╯{Colors.RESET}")
            print()

            response = poster_agent.run(
                user_message,
                context={
                    "date": get_date(),
                    "username": os.getenv("USER", "user"),
                    "working_directory": os.getcwd(),
                    "env_content": {
                        "date": get_date(),
                        "username": os.getenv("USER", "user"),
                        "working_directory": os.getcwd(),
                    },
                },
            )
            # Use colored output
            colored_response = colorize_response(response)
            print(colored_response)
            print(f"\n{Colors.CYAN}{'═' * 80}{Colors.RESET}")

            if poster_agent.langfuse_trace_id:
                print(f"\n{Colors.BLUE}📊 Langfuse trace ID: {Colors.YELLOW}{poster_agent.langfuse_trace_id}{Colors.RESET}")
                try:
                    trace_url = langfuse.get_client().get_trace_url(
                        trace_id=poster_agent.langfuse_trace_id
                    )
                    print(f"{Colors.BLUE}🔗 Langfuse trace URL: {Colors.CYAN}{trace_url}{Colors.RESET}")
                except Exception:
                    pass

    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}👋 Paper2PosterAgent interrupted by user{Colors.RESET}")
        return 0
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
