# Configuration Guide

## Core Configuration (Required)

```bash
# Core LLM Configuration
LLM_MODEL=your_model_name
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your_api_key_here
```

## WebDevAgent Configuration

```bash
# Unsplash image search
UNSPLASH_ACCESS_KEYS=your_key

# Image annotation VLM
IMAGE_CAPTIONER_MODEL=vlm_model_name
IMAGE_CAPTIONER_BASE_URL=vlm_base_url
IMAGE_CAPTIONER_API_KEY=sk-xxx
```

**Get Unsplash API Key:** [https://unsplash.com/developers](https://unsplash.com/developers)

## Paper2PosterAgent Configuration

```bash
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

## Optional: Langfuse Monitoring

```bash
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_HOST=http://your-langfuse-host:port
```
