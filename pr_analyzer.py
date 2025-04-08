import sys
import os
import traceback
import re
import subprocess
import time
from typing import Any, Dict
from mcp.server.fastmcp import FastMCP
from github_integration import fetch_pr_changes
from notion_client import Client
from dotenv import load_dotenv
import pyautogui
import requests

class PRAnalyzer:
    def __init__(self):
        # Debug: Print working directory and list files
        cwd = os.getcwd()
        print("Current working directory:", cwd, file=sys.stderr)
        print("Files in directory:", os.listdir(cwd), file=sys.stderr)
        
        # Locate .env file.
        dotenv_path = os.path.join(cwd, '.env')
        print("Looking for .env file at:", dotenv_path, file=sys.stderr)
        
        try:
            with open(dotenv_path, "r") as f:
                env_content = f.read()
                print("Contents of .env file:\n", env_content, file=sys.stderr)
        except Exception as e:
            print("Error reading .env file:", e, file=sys.stderr)
        
        # Load environment variables.
        load_dotenv(dotenv_path=dotenv_path, override=True)
        
        print("Loaded GITHUB_TOKEN:", os.getenv("GITHUB_TOKEN"), file=sys.stderr)
        print("Loaded NOTION_API_KEY:", os.getenv("NOTION_API_KEY"), file=sys.stderr)
        print("Loaded NOTION_PAGE_ID:", os.getenv("NOTION_PAGE_ID"), file=sys.stderr)
        
        # Initialize MCP Server.
        self.mcp = FastMCP("github_pr_analysis")
        print("MCP Server initialized", file=sys.stderr)
        print("GITHUB_TOKEN:", os.getenv("GITHUB_TOKEN"), file=sys.stderr)
        
        # Initialize Notion client.
        self._init_notion()
        
        # Register all MCP tools.
        self._register_tools()
    
    def _init_notion(self):
        """Initialize the Notion client with API key and page ID."""
        try:
            self.notion_api_key = os.getenv("NOTION_API_KEY")
            self.notion_page_id = os.getenv("NOTION_PAGE_ID")
            if not self.notion_api_key or not self.notion_page_id:
                raise ValueError("Missing Notion API key or page ID in environment variables")
            self.notion = Client(auth=self.notion_api_key)
            print("Notion client initialized successfully", file=sys.stderr)
            print("Using Notion page ID:", self.notion_page_id, file=sys.stderr)
        except Exception as e:
            print("Error initializing Notion client:", str(e), file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)
    
    def _register_tools(self):
        """Register MCP tools for PR analysis, Notion, NASA, GUI automation, etc."""
        @self.mcp.tool()
        async def fetch_pr(repo_owner: str, repo_name: str, pr_number: int) -> Dict[str, Any]:
            """Fetch changes from a GitHub pull request."""
            print(f"Fetching PR #{pr_number} from {repo_owner}/{repo_name}", file=sys.stderr)
            try:
                pr_info = fetch_pr_changes(repo_owner, repo_name, pr_number)
                if pr_info is None:
                    print("No changes returned from fetch_pr_changes", file=sys.stderr)
                    return {}
                print("Successfully fetched PR information", file=sys.stderr)
                return pr_info
            except Exception as e:
                print("Error fetching PR:", str(e), file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                return {}
        
        @self.mcp.tool()
        async def create_notion_page(title: str, content: str) -> str:
            """Create a Notion page with PR analysis, splitting long content into multiple blocks."""
            print(f"Creating Notion page: {title}", file=sys.stderr)
            try:
                max_length = 2000
                content_chunks = [content[i:i+max_length] for i in range(0, len(content), max_length)]
                children = []
                for chunk in content_chunks:
                    children.append({
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": chunk}
                            }]
                        }
                    })
                self.notion.pages.create(
                    parent={"type": "page_id", "page_id": self.notion_page_id},
                    properties={"title": {"title": [{"text": {"content": title}}]}},
                    children=children
                )
                print(f"Notion page '{title}' created successfully!", file=sys.stderr)
                return f"Notion page '{title}' created successfully!"
            except Exception as e:
                error_msg = f"Error creating Notion page: {str(e)}"
                print(error_msg, file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                return error_msg

        @self.mcp.tool()
        async def get_nasa_apod(date: str = None) -> dict:
            """
            Fetch NASA's Astronomy Picture of the Day (APOD).
            Optionally accepts a date (YYYY-MM-DD); if not provided, returns today's APOD.
            """
            api_key = os.getenv("NASA_API_KEY")
            if not api_key:
                return {"error": "NASA_API_KEY not set in environment variables."}
            url = "https://api.nasa.gov/planetary/apod"
            params = {"api_key": api_key}
            if date:
                params["date"] = date
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                return {"error": str(e)}
        
        @self.mcp.tool()
        async def automate_gui(action: str, parameters: dict) -> dict:
            """
            Automate desktop GUI actions using pyautogui.
            
            Supported actions:
              - "type": Simulate typing text. Requires "text"; optional "interval" (default 0.05).
              - "click": Simulate a mouse click. Requires "x" and "y" coordinates.
              - "hotkey": Simulate a hotkey combination. Requires "keys" as a list.
              - "move": Move the mouse pointer. Requires "x" and "y"; optional "duration" (default 0.25).
              - "minimize": Minimize the active window (macOS, using Command+M).
              - "open_terminal": Open the macOS Terminal and optionally type commands.
              - "open_vscode_terminal": Toggle the integrated terminal in Visual Studio Code.
            """
            try:
                act = action.lower()
                
                if act == "type":
                    text = parameters.get("text", "")
                    interval = float(parameters.get("interval", 0.05))
                    pyautogui.typewrite(text, interval=interval)
                    return {"status": "success", "message": f"Typed: {text}"}
                
                elif act == "click":
                    x = parameters.get("x")
                    y = parameters.get("y")
                    if x is None or y is None:
                        return {"status": "error", "message": "x and y coordinates required"}
                    pyautogui.click(x, y)
                    return {"status": "success", "message": f"Clicked at ({x}, {y})"}
                
                elif act == "hotkey":
                    keys = parameters.get("keys")
                    if not keys or not isinstance(keys, list):
                        return {"status": "error", "message": "keys must be provided as a list"}
                    pyautogui.hotkey(*keys)
                    return {"status": "success", "message": f"Pressed hotkey: {keys}"}
                
                elif act == "move":
                    x = parameters.get("x")
                    y = parameters.get("y")
                    duration = float(parameters.get("duration", 0.25))
                    if x is None or y is None:
                        return {"status": "error", "message": "x and y coordinates required"}
                    pyautogui.moveTo(x, y, duration=duration)
                    return {"status": "success", "message": f"Moved mouse to ({x}, {y})"}
                
                elif act == "minimize":
                    pyautogui.hotkey("command", "m")
                    return {"status": "success", "message": "Minimized active window"}
                
                elif act == "open_terminal":
                    # Open macOS Terminal.
                    subprocess.Popen(["open", "-a", "Terminal"])
                    time.sleep(2)  # Wait for Terminal to launch.
                    # Optionally, type commands.
                    commands = parameters.get("commands", [])
                    for cmd in commands:
                        pyautogui.typewrite(cmd, interval=0.05)
                        pyautogui.press("enter")
                    return {
                        "status": "success",
                        "message": "Opened Terminal and executed commands.",
                        "commands_run": commands
                    }
                
                elif act == "open_vscode_terminal":
                    # In Visual Studio Code, the default shortcut to toggle the integrated terminal is typically Ctrl+`
                    # (on macOS, use "ctrl" and "`").
                    # Make sure VS Code is active before calling this.
                    pyautogui.hotkey("ctrl", "`")
                    time.sleep(1)  # Wait for the terminal to appear.
                    # Optionally, type commands in the integrated terminal.
                    commands = parameters.get("commands", [])
                    for cmd in commands:
                        pyautogui.typewrite(cmd, interval=0.05)
                        pyautogui.press("enter")
                    return {
                        "status": "success",
                        "message": "Opened integrated terminal in VS Code and executed commands.",
                        "commands_run": commands
                    }
                
                else:
                    return {"status": "error", "message": f"Unsupported action: {action}"}
            
            except Exception as e:
                return {"status": "error", "message": str(e)}
        
        @self.mcp.tool()
        async def process_desktop_context(context: str) -> dict:
            """
            Process a desktop command from chat context and execute a chain of actions.
            For example, if the context is:
            "open Portfolio folder in VS Code and run the code"
            This tool will:
              1. Open the Portfolio folder (assumed to be at ~/Desktop/Portfolio).
              2. Open Visual Studio Code with that folder.
              3. Optionally run code analysis (using flake8) on that folder.
              4. Return the results.
            """
            results = {}
            actions = []
            context_lower = context.lower()

            # Open the Portfolio folder on Desktop.
            if "open portfolio folder" in context_lower:
                folder_path = os.path.expanduser("~/Desktop/Portfolio")
                try:
                    subprocess.run(["open", folder_path], check=True)
                    actions.append("Opened Portfolio folder")
                    results["open_folder"] = f"Opened folder: {folder_path}"
                except Exception as e:
                    results["open_folder"] = f"Error opening folder: {str(e)}"
            
            # Open VS Code with the folder.
            if "vs code" in context_lower or "vscode" in context_lower:
                folder_path = os.path.expanduser("~/Desktop/Portfolio")
                try:
                    subprocess.Popen(["open", "-a", "Visual Studio Code 2", folder_path])
                    actions.append("Opened VS Code with Portfolio folder")
                    results["vscode"] = f"VS Code opened with folder: {folder_path}"
                except Exception as e:
                    results["vscode"] = f"Error opening VS Code: {str(e)}"
            
            # Analyze code if instructed.
            if "analyze the code" in context_lower or "list out potential problems" in context_lower:
                folder_path = os.path.expanduser("~/Desktop/Portfolio")
                try:
                    analysis = subprocess.run(["flake8", folder_path],
                                              capture_output=True, text=True, check=True)
                    actions.append("Analyzed code using flake8")
                    analysis_output = analysis.stdout.strip() or "No issues found."
                    results["analysis"] = analysis_output
                except subprocess.CalledProcessError as e:
                    results["analysis"] = f"Analysis errors: {e.output}"
                except Exception as e:
                    results["analysis"] = f"Error analyzing code: {str(e)}"
            
            if not actions:
                return {"status": "error", "message": "No recognized actions in context."}
            
            return {"status": "success", "actions": actions, "results": results}
        
        # Attach tools to instance for external usage.
        self.create_notion_page_func = create_notion_page
        self.get_nasa_apod_func = get_nasa_apod
        self.automate_gui_func = automate_gui
        self.process_desktop_context_func = process_desktop_context

    def run(self):
        """Start the MCP server."""
        try:
            print("Running MCP Server for GitHub PR Analysis...", file=sys.stderr)
            self.mcp.run(transport="stdio")
        except Exception as e:
            print("Fatal Error in MCP Server:", str(e), file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    analyzer = PRAnalyzer()
    analyzer.run()
