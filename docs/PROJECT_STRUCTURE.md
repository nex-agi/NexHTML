# Project Structure

This document describes the directory structure and organization of the NexHTML project.

---

## 📁 Directory Tree

```
NexHTML/
├── .env                          # Environment variables config
├── README.md                     # Project documentation (English)
├── README_CN.md                  # Project documentation (Chinese)
├── pyproject.toml                # Python project config
├── .gitmodules                   # Git submodule config
│
├── nexau/                        # Nexau framework (submodule)
│   └── nexau/archs/
│       ├── config/               # Config loader
│       ├── llm/                  # LLM configuration
│       ├── tool/                 # Tool system
│       └── main_sub/             # Agent core
│
├── MinerU/                       # MinerU PDF parsing engine (submodule)
│
└── src/                          # Agent source directory
    ├── WebDevAgent/              # HTML generation Agent
    │   ├── start.py              # Launch script
    │   ├── config.yaml           # Agent config
    │   ├── system-prompt.md      # System prompt
    │   └── tools/                # Toolset
    │       ├── web_img_search.py # Image search implementation
    │       └── web_img_search.yaml # Tool config
    │
    ├── Paper2PosterAgent/        # Academic poster generation Agent
    │   ├── start.py              # Launch script
    │   ├── config.yaml           # Agent config
    │   ├── system-prompt.md      # System prompt
    │   └── tools/                # Toolset
    │       ├── paper2md_tool.py          # PDF to Markdown
    │       ├── image_caption_tool.py     # Image annotation
    │       ├── logo_manager_tool.py      # Logo management
    │       ├── gen_qr_code_tool.py       # QR code generation
    │       ├── height_detect_tool.py     # Height detection
    │       ├── layout_balance_tool.py    # Layout balancing
    │       ├── poster_tool.py            # Poster generation
    │       ├── screenshot_tool.py        # Screenshot tool
    │       └── *.yaml                    # Tool config files
    │
    └── datavis_agent/            # Data visualization Agent (WIP)
```

---

## 📂 Key Directories

### `/nexau`
The Nexau framework submodule, providing the underlying Agent architecture and capabilities.

### `/MinerU`
MinerU PDF parsing engine submodule, used by Paper2PosterAgent for PDF to Markdown conversion.

### `/src`
Contains all Agent implementations. Each Agent has its own directory with:
- `start.py` - Entry point to launch the agent
- `config.yaml` - Agent-specific configuration
- `system-prompt.md` - System prompt defining agent behavior
- `tools/` - Custom tools and their configurations

### `/docs`
Documentation files including case studies, prompts, and this structure guide.

---

[← Back to Main README](../README.md)
