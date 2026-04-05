from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

model = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
)

# 1. 定义输入模式 - 只包含用户输入​
class InputState(TypedDict):
    topic: str # 用户输入的主题​

# 2. 定义输出模式 - 只包含最终结果​
class OutputState(TypedDict):
    final_content: str # 最终的内容​

# 3. 定义完整状态模式（内部使用）​
class OverallState(InputState, OutputState):
    outline: str # 第一步：生成的大纲​
    draft: str # 第二步：生成的初稿​
    polished_draft: str # 第三步：润色后的稿件​

# 第一步：生成大纲​
PROMPT_1 = (
    "根据主题生成文章大纲。\n"
    "主题：{topic}\n"
    "要求："
    "1.只需两个最核心标题"
    "2.不用进行说明，只返回最终大纲"
)
def generate_outline(state: InputState):
    print("*" * 50)
    print(f"内容大纲生成中...\n")
    prompt = PROMPT_1.format(topic=state['topic'])
    outline = model.invoke([HumanMessage(content=prompt)]).content
    print(f"大纲已生成：\n{outline}\n")
    return {
        "outline": outline,
        "topic": state["topic"]
    }

# 第二步：基于大纲生成初稿​
PROMPT_2 = (
    "根据以下内容生成文章完整初稿。\n"
    "主题：{topic}\n"
    "大纲: "
    "{outline}\n"
    "要求："
    "1.每个标题下，最多使用三句话的内容即可"
    "2.不用进行说明，只返回最终结果"
)
def generate_draft(state: OverallState):
    print("*" * 50)
    print(f"生成初稿中...\n")
    prompt = PROMPT_2.format(topic=state['topic'],outline=state['outline'])
    draft = model.invoke([HumanMessage(content=prompt)]).content
    print(f"初稿已生成：\n{draft}\n")
    return {"draft": draft}

# 第三步：润色稿件​
PROMPT_3 = (
    "根据文章初稿进行润色。\n"
    "主题：{topic}\n"
    "初稿: "
    "{draft}\n"
    "要求："
    "1.润色后，文章不能太长"
)

def polish_content(state: OverallState):
    print("*" * 50)
    print(f"文章润色中...\n")
    prompt = PROMPT_3.format(topic=state['topic'],draft=state['draft'])
    polished = model.invoke([HumanMessage(content=prompt)]).content
    print(f"润色完成，内容如下：\n{polished}\n")
    return {"polished_draft": polished}

# 第四步：生成最终稿​
PROMPT_4 = (
    "根据润色版文章，生成文章终稿。\n"
    "主题：{topic}\n"
    "大纲: "
    "{outline}\n"
    "润色版文章: "
    "{polished_draft}\n"
)

def finalize_content(state: OverallState):
    prompt = PROMPT_4.format(topic=state['topic'],outline=state['outline'],polished_draft=state['polished_draft'])
    final_content = model.invoke([HumanMessage(content=prompt)]).content
    return {"final_content": final_content}

# 构建工作流​
builder = StateGraph(
OverallState,
input_schema=InputState,
output_schema=OutputState
)

# 添加节点​
builder.add_node(generate_outline) # 节点1：生成大纲​
builder.add_node(generate_draft) # 节点2：生成初稿​
builder.add_node(polish_content) # 节点3：润色稿件​
builder.add_node(finalize_content) # 节点4：生成最终稿​

# 连接节点（直线流程）​
builder.add_edge(START, "generate_outline") # 开始 → 生成大纲​
builder.add_edge("generate_outline", "generate_draft") # 大纲 → 生成初稿​
builder.add_edge("generate_draft", "polish_content") # 初稿 → 润色​
builder.add_edge("polish_content", "finalize_content") # 润色 → 最终稿​
builder.add_edge("finalize_content", END) # 最终稿 → 结束​

# 编译工作流​
chain = builder.compile()

# 使用工作流​
result = chain.invoke({"topic": "人工智能的未来发展"})
print("=" * 50)
print("最终创作结果:")
print("=" * 50)
print(result["final_content"])
print("=" * 50)