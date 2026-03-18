from re import M

from langchain_core.prompts import PromptTemplate, ChatPromptTemplate,MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

# 定义文本提示词模板，输出的是一个纯字符串，给LLM补全模型用的
template1 = PromptTemplate(
    template="please translate this scentence from {A} to {B}",
    input_variables=["A", "B"],
)
print(template1.invoke({
    "A":"English",
    "B":"Chinese",
}))

template2 = PromptTemplate.from_template("please translate this scentence form {a} to {b}")
print(template2.invoke({"a":"Chinese", "b":"English"}))

# 聊天消息提示词
template = ChatPromptTemplate.from_messages([
    ("system", "Translate this sentence from {a} to {b}"),
    MessagesPlaceholder("msgs"), #消息占位符，可以将历史消息插入模版中，实现多轮对话
    ("user", "{sentence}")
])

# history message
history_message = [
    HumanMessage(content="我是小明"),
    AIMessage(content="ok，你叫小明，我记住了"),
]

# 实例化消息模板，得到不含模板参数的消息实例
messageValue = template.invoke(
    {
        "a":"English",
        "b":"Chinese",
        "sentence":"hi, what`s my name?",
        "msgs":history_message,
    },
)
# message = messageValue.to_messages()
# print(messageValue)

model = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1"
)

# model.invoke(message).pretty_print()
chain = template | model
chain.invoke(
    {
        "a":"English",
        "b":"Chinese",
        "sentence":"hi,what`s my name?",
        "msgs":history_message
    }
).pretty_print()