from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableSequence

# 1. 接入大模型
# 默认从环境变量 OPENAI_API_KEY 中获取 API Key
model = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1"
)

# 2. 定义消息
message = [
    SystemMessage(content="你是一个翻译助手，请将用户发送的英文直接翻译为中文，只输出翻译结果，不要回答问题。"),
    HumanMessage(content="i`m gogang to the park tomorrow."),
]

# 3. 调用模型
result = model.invoke(message)
# print(result)

# 4. 定义输出解析器
parser = StrOutputParser()
# print(parser.invoke(result))

# 5. 定义链
# chain = model | parser
# chain = RunnableSequence(first=model, last=parser)
chain = model.pipe(parser)
print(chain.invoke(message))
