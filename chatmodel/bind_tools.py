from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

@tool
def add(a: int, b: int) -> int:
    """两数相加"""
    return a + b
@tool
def sub(a: int, b: int) -> int:
    """两数相减"""
    return a - b

#定义模型
model = ChatOpenAI(
    model = "deepseek-chat",
    base_url = "https://api.deepseek.com/v1",
)

message = [
    HumanMessage(content="2+3等于多少? 3-2等于多少?"),
]
print(f"first message: {message}")

# 绑定工具
# 绑定工具时，会给我们返回一个新的model实例，原model并没有绑定到工具，但是还可以以正常使用
# 绑定工具时，使用tools_choicec参数来指定模型选择工具的方式，默认是auto，设置为any则表示默认会任意选择一个工具来执行。
# 即使该问题不适合使用工具，模型也会选择一个工具来执行，这可能会导致一些不相关的结果。
modelWithTool = model.bind_tools(tools=[add, sub])

# 调用模型，这只是调用了模型，模型选择了工具来处理这个问题
# 但是并没有给我们返回调用工具的结果
# AIMessage
aiMsg = modelWithTool.invoke(message)
message.append(aiMsg)
print(f"second message: {message}")

# 这个消息的类型是ToolMessage
# print(aiMsg.tool_calls[0]) # 模型选择了工具来处理这个问题，tool_calls里记录了模型选择的工具和工具的输入参数
while aiMsg.tool_calls:
    for tool_call in aiMsg.tool_calls:
        selected_tool = {"add": add, "sub": sub}[tool_call["name"]]
        tool_msg = selected_tool.invoke(tool_call)
        message.append(tool_msg)
        print(f"tool message: {message}")
    
    # 把工具结果发回模型，让它继续
    aiMsg = modelWithTool.invoke(message)
    message.append(aiMsg)
    print(f"third message: {message}")


# 为了让模型调用工具后，将结果以及我们的问题一起返回，我们需要将这些过程中的message都记录下来，最整体发送给model
print(message)
print(model.invoke(message).content)
