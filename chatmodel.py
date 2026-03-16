from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser

# temperature 采样温度，控制生成文本的随机程度，值越大生成的文本越随机，值越小生成的文本越确定。
# 0 完全确定，适用于需要准确答案的场景，如数学题、编程题等。
# 0.1-0.5 适用于大多数场景，生成的文本既有创造性又不失准确性。
# 0.5-1.0 适用于需要更多创造性的场景，如写作、对话等，但可能会生成一些不相关或不准确的内容。
# 1.0以上内容高度随机，适用于需要极高创造性的场景，但可能会生成大量不相关或不准确的内容。
model = ChatOpenAI(
    model = "deepseek-chat",
    base_url = "https://api.deepseek.com/v1",
    # temperature = 2
    # max_tokens = 10, # 限制单次生成的最大 token 数量，适用于需要控制输出长度的场景，如摘要、标题等。
    # timeout = 5, # 请求超时时间，单位为秒，适用于需要控制响应时间的场景，如实时对话、在线服务等。
    # max_retries = 2, # 最大重试次数，适用于网络不稳定或服务可能暂时不可用的场景，如在线服务、API 调用等。默认为2
    # streaming = False, # 是否启用流式输出，适用于需要实时获取生成结果的场景，如对话、写作等。默认为False
)

message = [
    SystemMessage(content="将内容进行补全，100个字以内。"),
    HumanMessage(content="一只小猫正在___?"),
]

parser = StrOutputParser()

chain = model | parser
print(chain.invoke(message))