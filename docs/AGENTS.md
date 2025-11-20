# Agent Overview

This document provides detailed information about the AI Agents available in NexHTML.

---

## 🌐 WebDevAgent

**Role**: HTML Code Generation Expert

**Workflow**:
```
User Request → Image Search → AI Annotation → Generate HTML → User Feedback → Iterative Optimization
```

**Configuration**: `src/WebDevAgent/config.yaml`

**System Prompt**: `src/WebDevAgent/system-prompt.md`

**Core Tools**:
- `WebImageSearch` - Unsplash image search (supports multiple API key load balancing)
- `ImageCaptioner` - VLM-based image annotation
- File operation tools (Read, Write, Edit, Grep, Glob)
- TodoWrite - Task management

---

## 📊 Paper2PosterAgent

**Role**: Academic Poster Generation Expert

**Complete Workflow**:
```
PDF Input
  ↓
PDF → Markdown (MinerU)
  ↓
Image Annotation (VLM)
  ↓
Institution Logo Extraction
  ↓
arXiv Link → QR Code
  ↓
Layout Analysis & Optimization
  ↓
HTML Poster Generation
  ↓
Screenshot Preview
```

**Configuration**: `src/Paper2PosterAgent/config.yaml`

**System Prompt**: `src/Paper2PosterAgent/system-prompt.md`

**Core Tools**:
| Tool Name | Bound Function | Config File |
|-----------|----------------|-------------|
| PDF2Markdown | `pdf_to_markdown_tool` | `tools/paper2md.yaml` |
| ImageCaption | `image_caption_tool` | `tools/image_caption.yaml` |
| LogoManager | `logo_manager_tool` | `tools/logo_manager.yaml` |
| GenerateQRCode | `gen_qr_code_tool` | `tools/gen_qr_code.yaml` |
| HeightDetect | `height_detect_tool` | `tools/height_detect.yaml` |
| LayoutBalance | `layout_balance_tool` | `tools/layout_balance.yaml` |
| PosterGeneration | `poster_tool` | `tools/poster.yaml` |
| Screenshot | `screenshot_tool` | `tools/screenshot.yaml` |

---

## 📈 DatavisSearchAgent

**Role**: Data Visualization & Analysis Expert

**Complete Workflow**:
```
User Request
  ↓
Session Directory Creation (tmp/datavis_search/{timestamp}_{lang}_{topic}/)
  ↓
Data Collection Phase
  ├─ Multi-source Web Search
  ├─ Kaggle Dataset Download (optional)
  └─ Data Download & Structuring
  ↓
Python Analysis Phase
  ├─ Stateful Python Execution
  ├─ Data Exploration (pandas/numpy)
  └─ Chart Planning
  ↓
Dashboard Generation Phase
  ├─ Plotly.js Chart Creation
  ├─ PapaParse CSV Integration
  └─ HTML Dashboard Assembly
  ↓
HTTP Service Display
  └─ Non-blocking Server Launch (port 8765)
```

**Configuration**: `src/DatavisSearchAgent/config.yaml`

**System Prompt**: `src/DatavisSearchAgent/system-prompt.md`

**Core Tools**:
| Tool Name | Bound Function | Config File |
|-----------|----------------|-------------|
| HTTPServer | `http_server` | `tools/http_server.yaml` |
| InteractivePythonExecutor | `interactive_python_executor` | `tools/interactive_python_executor.yaml` |
| KaggleDownload | `kaggle_download` | `tools/kaggle_download.yaml` |
| WebSearch | `web_search` | Built-in |
| WebRead | `web_read` | Built-in |
| Read / Write / LS / Bash | File & System Operations | Built-in |
| TodoWrite | Task Management | Built-in |

**Key Features**:
- **Stateful Python Execution**: Variables persist across multiple tool calls for iterative data exploration
- **UV Package Management**: All Python dependencies managed through UV for reproducibility
- **Automatic Port Selection**: HTTP server automatically finds available ports to avoid conflicts
- **Session Isolation**: Each task creates an isolated working directory with timestamp and topic naming
- **Multi-format Data Support**: CSV, XLSX, JSON with automatic parsing and structuring

---

[← Back to Main README](../README.md)
