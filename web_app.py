from flask import Flask, render_template, request, redirect
import pyautogui
import time
import webbrowser
import asyncio
import subprocess
import platform  # Added to detect the operating system

# Import pygetwindow for Windows, and pyobjc for macOS
if platform.system() == "Windows":
    from pygetwindow import getWindowsWithTitle as find_windows
elif platform.system() == "Darwin":  # macOS
    from AppKit import NSWorkspace
    from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID

    def find_windows(title):
        options = kCGWindowListOptionOnScreenOnly
        window_list = CGWindowListCopyWindowInfo(options, kCGNullWindowID)
        matching_windows = []
        for window in window_list:
            window_name = window.get('kCGWindowName', '')
            if window_name and title.lower() in window_name.lower():
                matching_windows.append(window_name)
        return matching_windows
else:
    def find_windows(title):
        raise NotImplementedError("Window management not supported on this platform")

from pr_analyzer import PRAnalyzer

app = Flask(__name__)
# Instantiate your MCP tools from pr_analyzer.py (without starting the MCP server)
analyzer = PRAnalyzer()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    prompt = request.form.get('prompt')
    if not prompt:
        return redirect('/')
    
    # --- Step 1: Minimize the current browser window ---
    if platform.system() == "Darwin":  # macOS
        pyautogui.hotkey('command', 'm')
    else:  # Windows
        pyautogui.hotkey('alt', 'space')
        pyautogui.press('n')  # Minimize on Windows
    time.sleep(1)
    
    # --- Step 2: Bring Claude Desktop to focus ---
    claude_windows = find_windows("claude")
    if claude_windows:
        # On Windows, claude_windows contains pygetwindow objects that can be activated
        # On macOS, claude_windows contains window names (strings), so we use pyautogui to activate
        if platform.system() == "Windows":
            claude_win = claude_windows[0]
            claude_win.activate()
        else:  # macOS
            # Use pyautogui to bring Claude to the foreground
            # Simulate Command + Tab to switch to Claude (assumes Claude is recently used)
            pyautogui.hotkey('command', 'tab')  # This might need adjustment
            time.sleep(1)
    else:
        # If Claude isn't found, attempt to launch it
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["open", "-a", "Claude"])
        else:  # Windows
            # Adjust this path based on where Claude is installed on Windows
            subprocess.run(["start", "Claude"], shell=True)
        time.sleep(5)  # Wait for Claude to launch
        claude_windows = find_windows("claude")
        if claude_windows:
            if platform.system() == "Windows":
                claude_win = claude_windows[0]
                claude_win.activate()
            else:  # macOS
                pyautogui.hotkey('command', 'tab')
                time.sleep(1)
        else:
            print("Claude Desktop not found. Please ensure it is installed.")
    
    # --- Step 3: Type the prompt in Claude Desktop ---
    pyautogui.typewrite(prompt, interval=0.05)
    pyautogui.press('enter')
    
    # --- Step 4: Wait for Claude Desktop to process the request ---
    time.sleep(20)  # Adjust this delay as necessary
    
    # --- Step 5: Use MCP Notion tool to create a page ---
    title = "Processed Prompt Result"
    content = "Result from Claude Desktop for prompt: " + prompt
    try:
        result = asyncio.run(analyzer.create_notion_page_func(title, content))
        print("Notion tool result:", result)
    except Exception as e:
        print("Error creating Notion page:", e)
    
    # --- Step 6: Open Notion in the browser ---
    notion_url = "https://www.notion.so"
    webbrowser.open(notion_url)
    
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)