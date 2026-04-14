import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from typing import Annotated
from typing_extensions import TypedDict
from app.tools import tools
from app.prompts import SYSTEM_PROMPT
from app.rag import build_index

load_dotenv()

build_index()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.3,
)

llm_with_tools = llm.bind_tools(tools)


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def chat_node(state: AgentState) -> dict:
    today = datetime.today().strftime("%A, %B %d %Y")
    system = SystemMessage(content=f"{SYSTEM_PROMPT}\n\nToday's date is {today}.")
    response = llm_with_tools.invoke([system] + state["messages"])
    return {"messages": [response]}


tool_node = ToolNode(tools)

def should_use_tool(state: AgentState) -> str:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tool"
    return "end"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("chat", chat_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("chat")
    graph.add_conditional_edges(
        "chat",
        should_use_tool,
        {
            "tool": "tools",
            "end":  END,
        }
    )

    graph.add_edge("tools", "chat")

    return graph.compile()


_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def chat(message: str, history: list) -> tuple[str, list]:
    graph = get_graph()
    history = history + [HumanMessage(content=message)]
    result = graph.invoke({"messages": history})
    updated_messages = result["messages"]
    reply = ""
    for msg in reversed(updated_messages):
        if isinstance(msg, AIMessage) and msg.content:
            content = msg.content
            if isinstance(content, list):
                reply = " ".join(
                    block["text"] for block in content
                    if isinstance(block, dict) and "text" in block
                )
            else:
                reply = content
            break

    return reply, updated_messages


