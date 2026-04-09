from dataclasses import dataclass
from langgraph.graph import MessagesState, StateGraph
from langgraph.constants import START, END
from langchain_core.messages import HumanMessage
from langchain.tools import tool, ToolRuntime
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode, tools_condition

class State(MessagesState):
    user_name: str

@dataclass
class Context:
    user_id: str


@tool
def search(runtime: ToolRuntime[Context]):
    """天气查询工具"""
    user_id = runtime.context.user_id
    user_name = runtime.state["user_name"]
    return f"user_name{user_name}, user_id{user_id} 查询天气，晴天、15度"

model_with_tool = init_chat_model(model="qwen3:4b", model_provider="ollama").bind_tools([search])

def llm_call(state: State):
    """llm调用节点，判断是否需要调用工具"""
    return {"messages":[model_with_tool.invoke([HumanMessage(content="你支持使用绑定的工具工具搜索天气")] + state["messages"])]}

builder = StateGraph(State, context_schema=Context)
builder.add_node(llm_call)
# 将工具包装成一个节点
builder.add_node("tool_call", ToolNode([search]))

builder.add_edge(START, "llm_call")
builder.add_conditional_edges("llm_call", tools_condition, {"tools": "tool_call", "__end__":END})
builder.add_edge("tool_call", "llm_call")

graph = builder.compile()

first = graph.stream({"messages":[HumanMessage(content="西安今天天气怎么样？")], "user_name":"Soren"}, context={"user_id":"1234"})
for chunk in first:
    for node, update in chunk.items():
        update["messages"][-1].pretty_print()