from typing import TypedDict
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph
from langgraph.constants import START, END
from langgraph.checkpoint.memory import InMemorySaver

class State(TypedDict):
    topic: str
    joke: str

model = init_chat_model(model="deepseek-chat", model_provider="openai", base_url="https://api.deepseek.com/v1")

def generate_topic(state: State):
    """使用llm生成笑话主题"""
    response = model.invoke("帮我生成一个笑话主题，5个字以内")
    return {"topic": response.content}

def generate_joke(state: State):
    """使用llm，根据已有的topic生成笑话"""
    joke = model.invoke(f"你是一个笑话大师,根据{state['topic']}这个主题生成一段笑话, 10个字左右")
    return {"joke": joke.content}

builder = StateGraph(State)
builder.add_sequence([generate_topic, generate_joke])
builder.add_edge(START, "generate_topic")

graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id":"123"}}
# 执行图
# 第一次执行
first = graph.invoke({}, config)
print(first)

# 获取历史快照checkpoint
# 一共有四个节点 START -> generate_topic -> generate_joke -> END
# 运行一次，会产生四个状态快照，分别是 初始化、START之后、generate_topic之后、generate_joke之后
# 并且这些快照是按照最新到最旧排列的
checkpoints = list(graph.get_state_history(config))
update_topic = checkpoints[1]
print(update_topic.values)

# 更新状态时，会返回一个新的配置runnable，调用时，需要使用这个新配置
new_config = graph.update_state(update_topic.config, values={"topic":"程序员有趣的事"})
final = graph.invoke(None, new_config)
print(final)