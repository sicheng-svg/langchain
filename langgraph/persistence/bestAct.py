import uuid
from typing import Optional
from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    HumanMessage, AIMessage, SystemMessage,
    trim_messages, filter_messages, merge_message_runs, RemoveMessage
)
from langgraph.graph import StateGraph, MessagesState
from langgraph.constants import START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore
from langgraph.store.base import BaseStore
from typing_extensions import TypedDict, Annotated
import operator

# ============================================================
# 第一层：状态定义
# ============================================================
class State(MessagesState):
    summary: str  # 对话摘要（短期记忆压缩）

model = init_chat_model(
    model="deepseek-chat",
    model_provider="openai",
    base_url="https://api.deepseek.com/v1",
)

# ============================================================
# 第二层：消息预处理管线
# ============================================================
def prepare_messages(state: State) -> list:
    """
    消息预处理管线：merge → filter → trim → 注入摘要
    这个函数不修改 state，只在调用 LLM 前准备消息
    """
    messages = state["messages"]
    
    # Step 1: 合并连续的同类型消息
    # 场景：用户连发多条消息、或删除消息后出现连续 AI 回复
    messages = merge_message_runs(messages)
    
    # Step 2: 过滤（可选）
    # 场景：不想让 LLM 看到中间的 tool 调用细节
    # messages = filter_messages(messages, include_types=["human", "ai"])
    
    # Step 3: 裁剪到合适长度
    # 只取最近的消息传给 LLM，完整历史不受影响
    messages = trim_messages(
        messages,
        strategy="last",
        token_counter=len,     # 生产环境建议用 tiktoken 精确计算
        max_tokens=20,         # 最多保留20条消息
        start_on="human",      # 确保从 human 消息开始
        end_on=("human", "tool"),
    )
    
    # Step 4: 注入历史摘要到 system message
    summary = state.get("summary", "")
    if summary:
        system_msg = SystemMessage(
            content=f"你是一个有记忆的助手。\n之前的对话摘要：{summary}"
        )
        messages = [system_msg] + messages
    
    return messages

# ============================================================
# 第三层：节点定义
# ============================================================
def call_llm(state: State):
    """主对话节点"""
    messages = prepare_messages(state)
    result = model.invoke(messages)
    return {"messages": [result]}

def maybe_summarize(state: State):
    """条件总结：只在消息累积到一定量时触发"""
    messages = state["messages"]
    
    # 不到阈值，不总结
    if len(messages) <= 10:
        return None
    
    # 生成摘要
    summary = state.get("summary", "")
    if summary:
        prompt = f"已有摘要：{summary}\n\n请基于以下新对话扩展摘要，保留关键信息："
    else:
        prompt = "请为以下对话创建一个简洁的摘要，保留关键信息："
    
    summary_messages = messages + [HumanMessage(content=prompt)]
    response = model.invoke(summary_messages)
    
    # 删除旧消息，只保留最近 2 条
    delete_msgs = [RemoveMessage(id=m.id) for m in messages[:-2]]
    
    return {
        "summary": response.content,
        "messages": delete_msgs,
    }

# ============================================================
# 第四层：长期记忆提取（Store）
# ============================================================
MEMORY_KEYWORDS = ["我是", "我叫", "我喜欢", "我在", "我的工作",
                   "记住", "别忘了", "我习惯", "我打算", "我计划",
                   "我讨厌", "我偏好", "我负责"]

def extract_long_term_memory(state: State, config, *, store: BaseStore):
    """提取长期记忆：规则预筛 + LLM 精确提取"""
    user_id = config["configurable"].get("user_id", "default")
    ns = ("user_memories", user_id)
    msg = state["messages"][-1].content
    
    # 规则预筛：只有命中关键词才触发 LLM 提取（节省成本）
    if not any(kw in msg for kw in MEMORY_KEYWORDS):
        return {}
    
    # 查已有记忆，避免重复
    existing = store.search(ns)
    existing_text = "\n".join([m.value.get("content", "") for m in existing])
    
    # LLM 精确提取
    extraction = model.invoke(
        f"从以下消息中提取用户的个人信息（偏好、事实、习惯、目标），"
        f"用一句话概括核心信息。\n"
        f"如果信息已存在于已有记忆中，返回'无新信息'。\n\n"
        f"已有记忆：\n{existing_text}\n\n"
        f"用户消息：{msg}"
    )
    
    if "无新信息" not in extraction.content:
        store.put(ns, key=str(uuid.uuid4()), value={
            "content": extraction.content,
            "source_thread": config["configurable"]["thread_id"],
        })
    
    return {}

# ============================================================
# 第五层：组装图
# ============================================================
def route_after_llm(state: State):
    """决定是否需要总结"""
    if len(state["messages"]) > 10:
        return "maybe_summarize"
    return END

builder = StateGraph(State)
builder.add_node("call_llm", call_llm)
builder.add_node("maybe_summarize", maybe_summarize)
builder.add_node("extract_memory", extract_long_term_memory)

# 流程：LLM回复 → 提取长期记忆 → 判断是否总结
builder.add_edge(START, "call_llm")
builder.add_edge("call_llm", "extract_memory")
builder.add_conditional_edges("extract_memory", route_after_llm)
builder.add_edge("maybe_summarize", END)

graph = builder.compile(
    checkpointer=InMemorySaver(),
    store=InMemoryStore(),
)

## 整体架构
# ```
# 用户消息进来
#     ↓
# call_llm 节点：
#     ├── prepare_messages 管线：
#     │   ├── merge  → 合并连续同类型消息
#     │   ├── filter → 过滤不需要的消息类型（可选）
#     │   ├── trim   → 裁剪到上下文窗口内
#     │   └── 注入历史摘要到 system message
#     └── model.invoke(处理后的消息)
#     ↓
# extract_memory 节点：
#     ├── 规则预筛（关键词命中？）
#     │   ├── 未命中 → 跳过
#     │   └── 命中 → LLM 提取 → store.put()
#     ↓
# route_after_llm 判断：
#     ├── 消息 ≤ 10 条 → END
#     └── 消息 > 10 条 → maybe_summarize 节点：
#         ├── LLM 生成摘要 → 存入 state["summary"]
#         └── 删除旧消息，只保留最近 2 条