# PR Reviewer Setup Guide

This guide provides step-by-step instructions to set up the PR Reviewer project, which includes integrations with GitHub and Notion.

## Prerequisites
- `curl` (for MacOS/Linux)
- Python 3.x installed on your system

## Setup Instructions

### Step 1: Install `uv`

**MacOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh

### Step 2: Create and Set Up the Project
**MacOS/Linux:**

# Create a new directory for the project
uv init pr_reviewer
cd pr_reviewer

# Create and activate a virtual environment
uv venv
source .venv/bin/activate

# Install core dependencies
uv add "mcp[cli]" requests python-dotenv notion-client
