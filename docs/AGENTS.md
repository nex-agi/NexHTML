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

[← Back to Main README](../README.md)
