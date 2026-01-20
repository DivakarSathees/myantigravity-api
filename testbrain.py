# import os
# import subprocess
# from typing import Annotated, TypedDict, List
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_core.messages import BaseMessage, HumanMessage
# from langchain_core.tools import tool
# from langgraph.graph import StateGraph, START, END
# from langgraph.graph.message import add_messages
# from langgraph.prebuilt import ToolNode, tools_condition

# # --- 1. Define Tools (No change here, tools remain the same) ---
# @tool
# def execute_terminal(command: str):
#     """Executes a shell command and returns the output. Use for npm install, run, etc."""
#     try:
#         # Security Note: This is powerful; use in a dedicated 'test' folder
#         result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
#         return f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
#     except Exception as e:
#         return f"Error: {str(e)}"

# @tool
# def manage_file(path: str, content: str = None, action: str = "write"):
#     """Manages files. Action can be 'write' (requires content) or 'read'."""
#     if action == "write":
#         os.makedirs(os.path.dirname(path), exist_ok=True)
#         with open(path, "w") as f:
#             f.write(content)
#         return f"Successfully wrote to {path}"
#     elif action == "read":
#         with open(path, "r") as f:
#             return f.read()

# tools = [execute_terminal, manage_file]
# tool_node = ToolNode(tools)

# # --- 2. Build the Graph with Gemini ---
# class State(TypedDict):
#     messages: Annotated[List[BaseMessage], add_messages]

# # Use Gemini 2.0 Flash (Free Tier)
# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",
#     temperature=0,
#     max_tokens=None,
#     timeout=None,
#     max_retries=2,
# ).bind_tools(tools)

# def call_model(state: State):
#     return {"messages": [llm.invoke(state["messages"])]}

# # Build workflow
# workflow = StateGraph(State)
# workflow.add_node("agent", call_model)
# workflow.add_node("action", tool_node)

# workflow.add_edge(START, "agent")
# workflow.add_conditional_edges("agent", tools_condition, {"tools": "action", END: END})
# workflow.add_edge("action", "agent")

# app = workflow.compile()

# # --- 3. Test it locally ---
# if __name__ == "__main__":
#     test_input = {"messages": [HumanMessage(content="Create a directory called 'project_beta', add a python file 'app.py' inside it that prints 'Antigravity Start', and then run it.")]}
#     for output in app.stream(test_input):
#         print(output)
