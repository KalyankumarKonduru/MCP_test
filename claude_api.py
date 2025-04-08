from flask import Flask, request, jsonify
import asyncio
from pr_analyzer import PRAnalyzer

app = Flask(__name__)

# Initialize your MCP tools container.
# This loads all tools (including automate_gui) from pr_analyzer.py.
analyzer = PRAnalyzer()

@app.route('/execute', methods=['POST'])
def execute():
    """
    Expects a JSON payload with:
      - "action": a string that identifies the GUI automation action,
      - "parameters": (optional) a dictionary of parameters.
    
    Supported actions (as defined in automate_gui):
      - "type": Simulate typing text. Requires "text"; optional "interval".
      - "click": Simulate a mouse click. Requires "x" and "y" coordinates.
      - "hotkey": Simulate pressing a hotkey combination. Requires "keys" as a list.
      - "move": Move the mouse pointer. Requires "x" and "y"; optional "duration".
      - "minimize": Minimize the active window.
    """
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No JSON payload provided."}), 400
    if "action" not in data:
        return jsonify({"status": "error", "message": "Missing 'action' parameter."}), 400
    
    action = data["action"]
    parameters = data.get("parameters", {})

    try:
        # Call the asynchronous automate_gui tool using asyncio.run.
        result = asyncio.run(analyzer.automate_gui_func(action, parameters))
        return jsonify({"status": "success", "result": result}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # Runs on port 5002 (you can change the port if needed).
    app.run(host="0.0.0.0", port=5002, debug=True)
