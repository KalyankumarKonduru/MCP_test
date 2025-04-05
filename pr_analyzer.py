import sys
import os
import traceback
from typing import Any, Dict
from mcp.server.fastmcp import FastMCP
from github_integration import fetch_pr_changes
from notion_client import Client
from dotenv import load_dotenv

class PRAnalyzer:
    def __init__(self):
        # Debug: Print working directory and list of files
        cwd = os.getcwd()
        print("Current working directory:", cwd, file=sys.stderr)
        print("Files in directory:", os.listdir(cwd), file=sys.stderr)
        
        # Define the .env file path and print it
        dotenv_path = os.path.join(cwd, '.env')
        print("Looking for .env file at:", dotenv_path, file=sys.stderr)
        
        # Debug: Read and print the contents of the .env file
        try:
            with open(dotenv_path, "r") as f:
                env_content = f.read()
                print("Contents of .env file:\n", env_content, file=sys.stderr)
        except Exception as e:
            print("Error reading .env file:", e, file=sys.stderr)
        
        # Load environment variables from the .env file and force override any existing values
        load_dotenv(dotenv_path=dotenv_path, override=True)
        
        # Debug: Print the loaded environment variables
        print("Loaded GITHUB_TOKEN:", os.getenv("GITHUB_TOKEN"), file=sys.stderr)
        print("Loaded NOTION_API_KEY:", os.getenv("NOTION_API_KEY"), file=sys.stderr)
        print("Loaded NOTION_PAGE_ID:", os.getenv("NOTION_PAGE_ID"), file=sys.stderr)
        
        # Initialize MCP Server
        self.mcp = FastMCP("github_pr_analysis")
        print("MCP Server initialized", file=sys.stderr)
        print("GITHUB_TOKEN:", os.getenv("GITHUB_TOKEN"), file=sys.stderr)
        
        # Initialize Notion client
        self._init_notion()
        
        # Register MCP tools
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
        """Register MCP tools for PR analysis."""
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
                # Define maximum length per block and split content if necessary.
                max_length = 2000
                content_chunks = [content[i:i+max_length] for i in range(0, len(content), max_length)]
                
                # Build the children blocks from the chunks.
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
                
                # Create the Notion page with the defined blocks.
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
