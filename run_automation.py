import asyncio
from pr_analyzer import PRAnalyzer

# Instantiate your MCP tool container.
analyzer = PRAnalyzer()

# Example complex desktop instruction.
context = ("open Portfolio folder and run the code using VS Code 2 "
           "and try to analyze the code and list out potential problems")

result = asyncio.run(analyzer.process_desktop_context_func(context))
print("Process desktop context result:", result)
