import os
import subprocess
from typing import Annotated, TypedDict, List

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

# -------------------------------------------------
# 1. Define Tools
# -------------------------------------------------
# @tool
# def execute_terminal(command: str):
#     """Executes a shell command and returns the output."""
#     try:
#         result = subprocess.run(
#             command,
#             shell=True,
#             capture_output=True,
#             text=True,
#             timeout=30
#         )
#         return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
#     except Exception as e:
#         return f"Error: {str(e)}"

@tool
async def execute_terminal(command: str):
    """
    Executes a shell command and streams stdout line-by-line to the UI.
    """
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        msg = line.decode().strip()
        await broadcast_log(msg)

    await process.wait()
    return "Command finished"



@tool
def manage_file(path: str, content: str = None, action: str = "write"):
    """Manages files. Action can be 'write' or 'read'."""
    if action == "write":
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return f"Successfully wrote to {path}"

    elif action == "read":
        with open(path, "r") as f:
            return f.read()


tools = [execute_terminal, manage_file]
tool_node = ToolNode(tools)

# -------------------------------------------------
# 2. State Definition
# -------------------------------------------------
class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


# -------------------------------------------------
# 3. Azure OpenAI Configuration
# -------------------------------------------------
AZURE_ENDPOINT = os.getenv(
    "AZURE_OPENAI_ENDPOINT",
    "https://iamneo-qb.openai.azure.com/"
)

AZURE_API_KEY = os.getenv(
    "AZURE_OPENAI_API_KEY",
    "BseWgixIxbzsRMTI9XcdwIS39aVLQT791lDu1gi3rBBFngSSOH7vJQQJ99BIACYeBjFXJ3w3AAABACOGv3VO"
)

AZURE_DEPLOYMENT = os.getenv(
    "AZURE_OPENAI_DEPLOYMENT",
    "gpt-5-mini"
)

AZURE_API_VERSION = "2024-12-01-preview"


# -------------------------------------------------
# 4. Create Azure LLM (Tool-Enabled)
# -------------------------------------------------
llm = AzureChatOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_API_KEY,
    azure_deployment=AZURE_DEPLOYMENT,
    api_version=AZURE_API_VERSION,
    # temperature=0
).bind_tools(tools)


def call_model(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


# -------------------------------------------------
# 5. Build LangGraph Workflow
# -------------------------------------------------
workflow = StateGraph(State)

workflow.add_node("agent", call_model)
workflow.add_node("action", tool_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges(
    "agent",
    tools_condition,
    {
        "tools": "action",
        END: END
    }
)
workflow.add_edge("action", "agent")

app = workflow.compile()
# agent_app = workflow.compile()

# -------------------------------------------------
# 6. Local Test
# -------------------------------------------------
if __name__ == "__main__":
    test_input = {
        "messages": [
            HumanMessage(
                content=(
                    "Create a directory called 'project_beta', "
                    "add a python file 'app.py' inside it that write a code for printing prime no., and then run it."
                )
            )
        ]
    }

    for output in app.stream(test_input):
        print(output)
