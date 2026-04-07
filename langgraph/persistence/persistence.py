# 支持搜索的ai系统
import operator
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph
from langgraph.constants import START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, AnyMessage, SystemMessage
from langchain_tavily import TavilySearch

# 模型定义
model = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
)
# 定义工具，使用三方提供的
tool = TavilySearch(
    tavily_api_key = "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",
    max_results = 3,
)
tools = [tool]
tools_map = {t.name: t for t in tools}

# 绑定工具
modelWithTool = model.bind_tools(tools=[tool])

# 1. 定义状态
class SearchState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: Annotated[int, operator.add]

# 2. 定义节点（函数）
def llm_node(state: SearchState):
    """ 调用llm，其自主决定是否需要调用工具"""
    message = state["messages"]
    aiMsg = modelWithTool.invoke([SystemMessage(content="你是一个善于使用工具进行网络搜索的ai助理")] + message)
    return {
        "messages": [aiMsg],
        "llm_calls": 1,
    }

def tool_node(state: SearchState):
    """ 调用工具"""
    last_msg = state["messages"][-1]
    toolMsg = []
    for tool_call in last_msg.tool_calls:
        target_tool = tools_map[tool_call["name"]]
        tool_message = target_tool.invoke(tool_call["args"])
        toolMsg.append(ToolMessage(
            content=tool_message,
            tool_call_id=tool_call["id"],
        ))
    return {
        "messages": toolMsg,
    }


# 3. 定义图（节点和边）
search = StateGraph(SearchState)

# 4. 添加节点
search.add_node("llm", llm_node)
search.add_node("tool", tool_node)

# 5. 添加边（包括条件边）
search.add_edge(START, "llm") # 固定边，开始到第一次调用llm

def router(state: SearchState) -> str:
    """ 路由函数，根据当前状态决定下一步走llm还是tool"""
    # 如果tool_calls不为空，则说明需要调用工具
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tool"
    return END

search.add_conditional_edges(
    "llm",
    router,
    ["tool", END]
) #条件边， 判断是否需要调用工具，如果需要则路由到toll，反之直接结束

search.add_edge("tool", "llm") # 固定边，工具调用完后继续调用llm


# 定义内存持久化存储
# checkpointer = InMemorySaver()

# 定义PostgreSql持久化存储库
DB_URI = "postgresql://postgres:Xsc.200411@127.0.0.1:5432/postgres"
with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
# 6. 编译图
    checkpointer.setup()
    system = search.compile(checkpointer=checkpointer)
    config = {"configurable":{"thread_id":"7954384893"}}

    # 第一次执行
    # result = system.invoke({"messages":[HumanMessage(content="西安今天的天气怎么样？")]}, config=config)
    # result["messages"][-1].pretty_print()

    # 第二次执行
    result = system.invoke({"messages":[HumanMessage(content="你记得我们聊了什么么？")]}, config=config)
    result["messages"][-1].pretty_print()

# 7. 执行图
# while True:
#     query = input("##: ")
#     if query in ["exit", "quit"]:
#         break
#     message = {
#         "messages": [HumanMessage(query)],
#         "llm_calls": 0,
#     }
#     result = system.invoke(message)
#     msg = result["messages"]
#     calls = result["llm_calls"]
#     print(f"调用了{calls}次llm")
#     for i in range(len(msg)):
#         msg[i].pretty_print()

