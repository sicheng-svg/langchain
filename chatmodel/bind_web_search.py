from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_tavily import TavilySearch

model = ChatOpenAI(
    model = "deepseek-chat",
    base_url = "https://api.deepseek.com/v1",
)

# 定义工具，使用三方提供的
tool = TavilySearch(
    tavily_api_key = "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",
    max_results = 3,
)
# 绑定工具
modelWithTool = model.bind_tools(tools=[tool])

# 调用模型
message = [
    HumanMessage("西安今天的天气怎么样？")
]
aiMsg = modelWithTool.invoke(message)
message.append(aiMsg)
while aiMsg.tool_calls:
    for tool_call in aiMsg.tool_calls:
        tool_msg = tool.invoke(tool_call)
        message.append(tool_msg)
    
    # 多轮交互，模型会根据工具的结果继续回答问题，直到不再调用工具为止
    aiMsg = modelWithTool.invoke(message)
    message.append(aiMsg)

# 最后返回模型的回答
print(aiMsg.content)