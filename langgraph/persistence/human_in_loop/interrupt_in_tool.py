import operator
from typing import TypedDict, Annotated
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_core.messages import AnyMessage, SystemMessage, ToolMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.types import interrupt, Command

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]

@tool
def send_email(to: str, subject: str, body: str):
    """发送电子邮件给收件人"""
    # 在发送前暂停​
    response = interrupt({
        "action": "发送邮件",
        "to": to,
        "subject": subject,
        "body": body,
        "message": "同意发送这封邮件吗？",
    })
    if response.get("action") == "同意":
        final_to = response.get("to", to)
        final_subject = response.get("subject", subject)
        final_body = response.get("body", body)
        # 实际发送邮件（此处为示例，仅打印）​
        email_info = f"收件人：{final_to} 主题：{final_subject} 正文：{final_body}"
        print(f"[发送邮件] {email_info}")
        return email_info
    return "用户取消邮件"

# 使用绑定工具的模型​
model_with_tools = init_chat_model(model="qwen3:4b",model_provider="ollama", temperature=0).bind_tools([send_email])

def llm_call(state: dict):
    """LLM决定是否调用工具"""
    messages = model_with_tools.invoke([SystemMessage(content="你支持调用工具进行邮件发送。")]+ state["messages"])
    # 直接调用工具（为了演示效果）​
    if messages.tool_calls:
        tool_call = messages.tool_calls[0]
        tool_result = send_email.invoke(tool_call["args"])
        return {"messages": [ToolMessage(content=tool_result, tool_call_id=tool_call["id"])]}
    return {"messages": [messages]}

builder = StateGraph(MessagesState)
builder.add_node("llm_call", llm_call)
builder.add_edge(START, "llm_call")
builder.add_edge("llm_call", END)

graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "email-workflow"}}

initial = graph.invoke({"messages": [HumanMessage(content="发送电子邮件至alice@example.com，主题是：请假，内容是：理由如下...")]},config=config)
print(initial["__interrupt__"]) # -> [Interrupt(value={'action': '...', ...})]

# 用批准和可选编辑的参数恢复​
resumed = graph.invoke(
    # Command(resume={"action": "同意", "subject": "病假"}),​
    Command(resume={"action": "不同意"}),
    config=config,
)
print(resumed["messages"][-1]) # -> 工具调用结果​