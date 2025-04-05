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
```

> 🔁 Restart your terminal afterwards to ensure that the `uv` command is available.

---

### Step 2: Create and Set Up the Project

**MacOS/Linux:**
```bash
# Create a new directory for the project
uv init pr_reviewer
cd pr_reviewer

# Create and activate a virtual environment
uv venv
source .venv/bin/activate

# Install core dependencies
uv add "mcp[cli]" requests python-dotenv notion-client
```

---

### Step 3: Create `requirements.txt` and Install from It

Create a file called `requirements.txt` with the following content:

```txt
# Core dependencies for PR Analyzer
requests>=2.31.0          # For GitHub API calls
python-dotenv>=1.0.0      # For environment variables
mcp[cli]>=1.4.0           # For MCP server functionality
notion-client>=2.3.0      # For Notion integration
```

Install the packages:
```bash
uv pip install -r requirements.txt
pip install -r requirements.txt
```

---

### Step 4: Set Up Environment Variables

Create a `.env` file in the root directory and add the following:

```env
GITHUB_TOKEN=your_github_token
NOTION_API_KEY=your_notion_api_key
NOTION_PAGE_ID=your_notion_page_id
```

#### GitHub Token:

1. Go to GitHub → Settings → Developer Settings → Personal Access Tokens.
2. Click **"Generate new token (classic)"**.
3. Enable these scopes:
   - `read:org`
   - `read:repo_hook`
   - `repo`
4. Copy and paste the token into your `.env` file as `GITHUB_TOKEN`.

#### Notion Integration:

1. Go to [Notion Integrations](https://www.notion.so/my-integrations).
2. Click **"New integration"** and set the type to **Internal**.
3. Add it to your workspace.
4. Copy the **Internal Integration Secret** as `NOTION_API_KEY`.
5. Copy the **UUID at the end of the integration URL** as `NOTION_PAGE_ID`.

---

### Step 5: Create the Main Script

Create an empty script file for your server logic:

```bash
touch pr_reviewer
```

Add your application logic inside this file.

---

### Step 6: Run the Application

To run the project, make sure your environment is activated and `.env` is configured:

```bash
python pr_reviewer
```

---
