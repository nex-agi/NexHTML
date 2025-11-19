# NexHTML - NexAU-based HTML Agent

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Framework](https://img.shields.io/badge/framework-NexAU-orange.svg)](https://github.com/nex-agi/NexAU)

**Intelligent AI Agent Collection Based on NexAU Framework, Specializing in HTML Generation, Academic Poster Creation, and More**

[English](README.md) | [中文](README_CN.md)

[Quick Start](#quick-start) • [Agent Overview](docs/AGENTS.md)

</div>

---

## 📋 Table of Contents

- [Introduction](#introduction)
- [Case Studies](#case-studies)
- [Features](#features)
- [Quick Start](#quick-start)
- [Agent Overview](docs/AGENTS.md)

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

#### Launch Paper2PosterAgent

**Prerequisites:**

Before launching Paper2PosterAgent, you need to:

1. **Configure VLM (Vision Language Model)** - Set up a Vision Language Model for image analysis and caption generation
2. **Update `.env` file** with your VLM credentials:
   ```bash
   VLM_MODEL=your_vlm_model
   VLM_BASE_URL=your_vlm_url
   VLM_API_KEY=your_vlm_key
   ```

**Launch Commands:**

```bash
# First start MinerU service (PDF parsing)
# In another terminal:
uv run mineru-api

# Start Agent
uv run src/Paper2PosterAgent/start.py
```

### 6. Optional: Configure Langfuse Monitoring

To enable observability and monitoring with Langfuse, add the following to your `.env` file:

```bash
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_HOST=http://your-langfuse-host:port
```

See **[Configuration Guide →](docs/CONFIGURATION.md)** for more configuration details.

---

## 🎯 Agent Overview

For detailed information about each Agent (configuration, tools, workflows), please see **[Agent Overview Documentation →](docs/AGENTS.md)**

---

## 🙏 Acknowledgments

We extend our gratitude to [NexAU Framework](https://github.com/ex-agi/NexAU), [MinerU](https://github.com/opendatalab/MinerU), [Paper2Poster](https://github.com/Paper2Poster/Paper2Poster), [Unsplash](https://unsplash.com/), [Langfuse](https://langfuse.com/), and other projects for providing their codebases and service support.

---

<div align="center">

**⭐ If this project helps you, please give it a Star! ⭐**

</div>
