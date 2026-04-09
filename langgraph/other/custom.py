from dataclasses import dataclass
from langgraph.graph import MessagesState, StateGraph
from langgraph.constants import START, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain.tools import tool, ToolRuntime
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.config import get_stream_writer

class State(MessagesState):
    user_name: str

@dataclass
class Context:
    user_id: str


@tool
def search(runtime: ToolRuntime[Context]):
    """天气查询工具"""
    # 获取写入器
    user_id = runtime.context.user_id
    user_name = runtime.state["user_name"]

    writer = get_stream_writer()
    writer({
        "node":"search",
        "status":"begin",
        "user_id":user_id,
        "user_name":user_name
    })

    # 模拟搜索过程​
    search_steps = [
        {"name": "搜索1", "time": 1, "result": "晴天，"},
        {"name": "搜索2", "time": 2, "result": "15-20度"},
    ]
    all_result = "查询天气："
    import time
    for i, step in enumerate(search_steps, 1):
        writer({
            "node": "search_tool",
            "status": "searching",
            "step": step['name'],
            "all_step": len(search_steps),
            "cur_step": i,
            "user_id": user_id,
            "user_name": user_name
        })
    # 模拟处理时间​
    time.sleep(step['time'])
    all_result += step['result']

    writer({
        "node":"search",
        "status":"end",
        "user_id":user_id,
        "user_name":user_name,
        "all_result":all_result,
    })
    return f"user_name{user_name}, user_id{user_id} 查询天气，晴天、15度"

model_with_tool = init_chat_model(model="qwen3:4b", model_provider="ollama").bind_tools([search])

def llm_call(state: State):
    """llm调用节点，判断是否需要调用工具"""
    writer = get_stream_writer()
    writer({
        "node":"llm_call",
        "status":"begin"
    })
    writer({
        "node":"llm_call",
        "status":"running"
    })
    writer({
        "node":"llm_call",
        "status":"end"
    })
    return {"messages":[model_with_tool.invoke([HumanMessage(content="你支持使用绑定的工具工具搜索天气")] + state["messages"])]}

builder = StateGraph(State, context_schema=Context)
builder.add_node(llm_call)
# 将工具包装成一个节点
builder.add_node("tool_call", ToolNode([search]))

builder.add_edge(START, "llm_call")
builder.add_conditional_edges("llm_call", tools_condition, {"tools": "tool_call", "__end__":END})
builder.add_edge("tool_call", "llm_call")

graph = builder.compile()

first = graph.stream({"messages":[HumanMessage(content="西安今天天气怎么样？")], "user_name":"Soren"}, context={"user_id":"1234"}, stream_mode=["custom", "values"])
for chunk in first:
    if chunk[0] == "custom":
        info = chunk[-1]
        if info["node"] == "search":
            if info["status"] == "begin":
                print("开始搜索")
            elif info["status"] == "end":
                print("搜索结束")
            else:
                print(f"[{info["cur_step"]}/{info["all_step"]}] 正在处理。。。")
        elif info["node"] == "llm_call":
            pass
    if chunk[0] == "values":
        info = chunk[-1]
        if isinstance(info["messages"][-1], AIMessage) and not info["messages"][-1].tool_calls:
            print("执行结束")
            print(info["messages"][-1].content)