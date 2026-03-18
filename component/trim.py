# 使用RunnableWithMessageHistory 会导致上下文膨胀，但是可以通过裁剪解决
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage,AIMessage,trim_messages

model = ChatOpenAI(
    model = "deepseek-chat",
    base_url = "https://api.deepseek.com/v1",
)


messages = [
    SystemMessage(content="you're a good assistant"),
    HumanMessage(content="hi! I'm bob"),
    AIMessage(content="hi!"),
    HumanMessage(content="I like vanilla ice cream"),
    AIMessage(content="nice"),
    HumanMessage(content="whats 2 + 2"),
    AIMessage(content="4"),
    HumanMessage(content="thanks"),
    AIMessage(content="no problem!"),
    HumanMessage(content="having fun?"),
    AIMessage(content="yes!"),
    HumanMessage(content="What's my name?"),
]

trimer = trim_messages(
    max_tokens=11,      #输入的最大token数，如果toekn_counter传入的计算方式是len，则max_token表示最大的消息数
    strategy="last",    #保留靠后消息
    token_counter=len,#传入一个函数或者语言模型，用来计算token
    include_system=True,#是否保存systemMessage
    allow_partial=False, #是否允许拆分消息
    start_on="human",#以human消息开始
)
# input_tokens': 64, 'output_tokens': 16, 'total_tokens': 80,
print(model.invoke(messages))

# 注意这里传入的顺序，需要先对消息进行裁剪，再将裁剪的结果作为输入
# input_tokens': 53, 'output_tokens': 44, 'total_tokens': 97
chain = trimer | model
print(chain.invoke(messages))