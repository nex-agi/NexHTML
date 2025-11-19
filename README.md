# NexHTML - NexAU-based HTML Agent

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/framework-NexAU-orange.svg)](https://github.com/nex-agi/NexAU)

**Intelligent AI Agent Collection Based on NexAU Framework, Specializing in HTML Generation, Academic Poster Creation, and More**

[English](README.md) | [中文](README_CN.md)

[Quick Start](#quick-start) • [Agent Overview](docs/AGENTS.md) • [Configuration](#configuration) • [Project Structure](docs/PROJECT_STRUCTURE.md)

</div>

---

## 📋 Table of Contents

- [Introduction](#introduction)
- [Case Studies](#case-studies)
- [Features](#features)
- [Quick Start](#quick-start)
- [Agent Overview](docs/AGENTS.md)
- [Configuration](#configuration)
- [Project Structure](docs/PROJECT_STRUCTURE.md)

---

## 🎯 Introduction

NexHTML is an AI Agent development platform built on the [Nexau Framework](https://github.com/nex-agi/NexAU), integrating multiple specialized AI Agents designed to solve automation needs in real-world scenarios.

---

## ✨ Features

### 🌐 WebDevAgent - HTML Code Generation System

Professional HTML code generation and optimization AI system for creating high-quality frontend pages.

**Core Features:**
- 🖼️ **Smart Image Search** - Integrated Unsplash API with automatic image search and annotation
- 🎨 **Visual Enhancement** - AI-driven design suggestions and code optimization
- 📝 **Auto Annotation** - VLM-powered descriptive text generation for images
- 🔄 **Iterative Optimization** - Multi-round conversational code improvement

**Use Cases:**
- Landing Page Rapid Prototyping
- Marketing Page Generation
- Course Materials and Presentation Pages

### 📊 Paper2PosterAgent - Academic Poster Generation System

Automatically converts academic papers (PDF) into visually stunning academic posters in HTML.

**Core Features:**
- 📄 **PDF Parsing** - MinerU-based conversion from PDF to structured Markdown with image extraction
- 🖼️ **Smart Image Annotation** - VLM automatically generates titles and descriptions for paper figures
- 🏛️ **Logo Management** - Auto-extract institutional information and match university/organization logos
- 📱 **QR Code Integration** - Extract arXiv links and generate access QR codes
- 📐 **Layout Optimization** - AI-driven multi-column layout balancing and height detection
- 🎨 **Poster Rendering** - Generate professional HTML academic posters with preview screenshots

**Use Cases:**
- Conference Poster Generation
- Academic Presentation Materials
- Research Showcase and Exhibition

---

## 📸 Case Studies

### WebDev Case 1

<div align="center">
<img src="docs/imgs/webdev_case1.jpeg" alt="WebDev Case 1" width="450">
</div>

**Prompt**: [View Complete Prompt →](docs/prompts/webdev_case1_prompt.md)

### WebDev Case 2

<div align="center">
<img src="docs/imgs/webdev_case2.jpeg" alt="WebDev Case 2 - Paris Luxury Hotel" width="450">
</div>

**Prompt**: [View Complete PRD Document →](docs/prompts/webdev_case2_prompt.md)

### Paper2Poster Case 1

<div align="center">
<table>
<tr>
<td width="50%">
<img src="docs/imgs/paper2poster_en.png" alt="Paper2Poster - English Version" width="100%">
<p align="center"><strong>English Academic Poster</strong></p>
</td>
<td width="50%">
<img src="docs/imgs/paper2poster_ch.png" alt="Paper2Poster - Chinese Version" width="100%">
<p align="center"><strong>Chinese Academic Poster</strong></p>
</td>
</tr>
</table>
</div>

---

## 🚀 Quick Start

### 1. Requirements

- **Python**: 3.13+
- **System**: macOS / Linux / Windows
- **Tools**: Git, uv (recommended) or pip

### 2. Clone Project

```bash
# Clone main project
git clone https://github.com/nex-agi/NexHTML.git
cd NexHTML

# Initialize submodules
git submodule update --init --recursive
```

### 3. Install Dependencies

#### Using uv (Recommended)

```bash
# One-command installation (installs everything including MinerU and Nexau)
uv pip install -e .
```

#### Using pip

```bash
# One-command installation
pip install -e .
```

### 4. Configure Environment Variables

Copy and edit `.env` file:

```bash
cp .env.example .env
vim .env
```

**Required Configuration:**

```bash
# Core LLM Configuration
LLM_MODEL=your_model_name
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_api_key_here
```

See [Configuration](#configuration) section for detailed configuration.

### 5. Launch Agent

#### Launch WebDevAgent

**Prerequisites:**

Before launching WebDevAgent, you need to:

1. **Apply for Unsplash API Key** - Visit [Unsplash Developers](https://unsplash.com/developers) to register and obtain your API key for image search functionality
2. **Configure VLM for Image Captioning** - Set up a Vision Language Model to generate image descriptions
3. **Update `.env` file** with your credentials:
   ```bash
   UNSPLASH_ACCESS_KEYS=your_unsplash_key
   IMAGE_CAPTIONER_MODEL=your_vlm_model
   IMAGE_CAPTIONER_BASE_URL=your_vlm_url
   IMAGE_CAPTIONER_API_KEY=your_vlm_key
   ```

**Launch Command:**

```bash
uv run python src/WebDevAgent/start.py
```

**Example Dialog:**
```
📝 Your task: Generate a tech-style product landing page
🤖 WebDevAgent: Generating for you...
```

#### Launch Paper2PosterAgent

```bash
# First start MinerU service (PDF parsing)
# In another terminal:
uv run mineru-api

# Start Agent
uv run src/Paper2PosterAgent/start.py
```

**Example Dialog:**
```
📝 Your task: Convert paper.pdf to academic poster
🤖 Paper2PosterAgent:
1️⃣ Parsing PDF...
2️⃣ Generating image annotations...
3️⃣ Extracting arXiv link...
4️⃣ Generating poster HTML...
✅ Poster generated: poster.html
```

---

## 🎯 Agent Overview

For detailed information about each Agent (configuration, tools, workflows), please see **[Agent Overview Documentation →](docs/AGENTS.md)**

---

## ⚙️ Configuration

### Configuration File Structure

```
.env                          # Environment variables config (core)
├── Core LLM Configuration    # Shared by all Agents
├── Monitoring & Observability # Langfuse monitoring
├── WebDevAgent               # WebDevAgent specific config
└── Paper2PosterAgent         # Paper2PosterAgent specific config
```

### Core Configuration Items

#### 1. LLM Configuration (Required)


#### 2. Langfuse Monitoring (Optional)

```bash
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_HOST=http://your-langfuse-host:port
```

#### 3. WebDevAgent Configuration

```bash
# Unsplash image search (supports multiple API keys, comma-separated)
UNSPLASH_ACCESS_KEYS=key1,key2,key3

# Image annotation VLM
IMAGE_CAPTIONER_MODEL=vlm_model_name
IMAGE_CAPTIONER_BASE_URL=vlm_base_url
IMAGE_CAPTIONER_API_KEY=sk-xxx
```

#### 4. Paper2PosterAgent Configuration

```bash
# MinerU PDF parsing service
PAPER2MD_API_URL=http://127.0.0.1:8000/file_parse

# VLM Vision Language Model
VLM_MODEL=vlm_model_name
VLM_BASE_URL=vlm_base_url
VLM_API_KEY=sk-xxx
VLM_TIMEOUT=1000
VLM_MAX_TOKENS=6000
VLM_TEMPERATURE=0.9

# arXiv paper judgment
ARXIV_JUDGE_MODEL=vlm_model_name
ARXIV_JUDGE_BASE_URL=vlm_base_url
ARXIV_JUDGE_API_KEY=sk-xxx
ARXIV_JUDGE_MAX_TOKENS=8000
ARXIV_JUDGE_TIMEOUT=1000

```

### Configuration Priority

1. Environment variables in `.env` file
2. System environment variables
3. Default values in code

---

## 📁 Project Structure

For detailed project structure and directory organization, please see **[Project Structure Documentation →](docs/PROJECT_STRUCTURE.md)**

---

## 🙏 Acknowledgments

We extend our gratitude to [NexAU Framework](https://github.com/ex-agi/NexAU), [MinerU](https://github.com/opendatalab/MinerU), [Paper2Poster](https://github.com/Paper2Poster/Paper2Poster), [Unsplash](https://unsplash.com/), [Langfuse](https://langfuse.com/), and other projects for providing their codebases and service support.

---

<div align="center">

**⭐ If this project helps you, please give it a Star! ⭐**

</div>
