from langchain_openai import ChatOpenAI
from langsmith import Client
# 从langchain hub中，导入已有的提示词模板
client = Client()
prompt = client.pull_prompt("hardkothari/prompt-maker")

model = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1"
)

chain = prompt | model

while True:
    task = input("\n请输入你的任务")
    if task == "quit":
        break
    lazy_prompt = input("\n请输入你的提示词")
    for chunk in chain.stream({"task":task,"lazy_prompt":lazy_prompt}):
        print(chunk.content, end="", flush=True)
