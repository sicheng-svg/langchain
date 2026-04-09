from langgraph.graph import StateGraph, START
# 定义状态结构​
class State(dict):
    topic: str
    joke: str
# 创建节点函数​
def refine_topic(state):
    return {"topic": state["topic"] + "和猫"}
def generate_joke(state):
    return {"joke": f"这是一个关于{state['topic']}的笑话"}
# 构建图​
graph = (
    StateGraph(State)
    .add_node(refine_topic)
    .add_node(generate_joke)
    .add_edge(START, "refine_topic")
    .add_edge("refine_topic", "generate_joke")
    .compile()
)
# 流式输出状态更新​
# updates 会输出节点，以及该节点中更新的值
# {'refine_topic': {'topic': '冰激凌和猫'}}
# {'generate_joke': {'joke': '这是一个关于冰激凌和猫的笑话'}}
for chunk in graph.stream(
    {"topic": "冰激凌"},
    stream_mode="updates" # 只看更新部分​
):
    # print(chunk)
    pass
for chunk in graph.stream(
    {"topic": "冰激凌"},
    stream_mode="values" # 每一步的完整状态​
):
    print(chunk)

# 可以在stream流式输出时指定输出模式
# values：节点执行完后将全量的state都输出
# updates: 只输出节点更新的state
# messages： 输出llm生成的token
# custom： 支持我们自定义输出，需要通过写入器写入
# debug: 会输出更详细的内容
# first = graph.stream({"messages":[HumanMessage(content="西安今天天气怎么样？")], "user_name":"Soren"}, context={"user_id":"1234"}, stream_mode="updates")
# for chunk in first:
#     for node, update in chunk.items():
#         update["messages"][-1].pretty_print()