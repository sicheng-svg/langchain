from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate,ChatPromptTemplate,FewShotChatMessagePromptTemplate
from langchain_openai import ChatOpenAI

# examples = [
#     {"text": "2 @ 3 =?", "output": "5"},
#     {"text": "4 @ 5 =?", "output": "9"},
# ]
# 
# # example_prompt 是普通的 PromptTemplate
# # 文本提示词模板，输出的结果是一段文本
# example_prompt = PromptTemplate(
#     input_variables=["text", "output"],
#     template="输入: {text}\n输出: {output}"
# )
# 
# # 使用FewShotPromptTemplate 没有输入invoke时，会报错
# few_shot = FewShotPromptTemplate(
#     examples=examples,
#     example_prompt=example_prompt,
#     prefix="你是一个计算特殊操作符的助手",
#     suffix="输入: {text}\n输出:",
#     input_variables=["text"],
# )
# 
# print(few_shot.invoke({"text": "6 @ 4 =?"}))
# 

# 创建示例集
# 创建示例集
examples = [
{
    "question": "李白和杜甫，谁更长寿？",
    "answer": """
    是否需要后续问题：是的。
    后续问题：李白享年多少岁？
    中间答案：李白享年61岁。
    后续问题：杜甫享年多少岁？
    中间答案：杜甫享年58岁。
    所以最终答案是：李白
    """
},
{
    "question": "腾讯的创始人什么时候出生？",
    "answer": """
    是否需要后续问题：是的。
    后续问题：腾讯的创始人是谁？
    中间答案：腾讯由马化腾创立。
    后续问题：马化腾什么时候出生？
    中间答案：马化腾出生于1971年10月29日。
    所以最终答案是：1971年10月29日
    """,
},
{
    "question": "电影《红高粱》和《霸王别姬》的导演来自同一个国家吗？",
    "answer": """
    是否需要后续问题：是的。
    后续问题：《红高粱》的导演是谁？
    中间答案：《红高粱》的导演是张艺谋。
    后续问题：张艺来自哪里？
    中间答案：中国。
    后续问题：《霸王别姬》的导演是谁？
    中间答案：《霸王别姬》的导演是陈凯歌。
    后续问题：陈凯歌来自哪里？
    中间答案：中国。
    所以最终答案是：是
""",
},
]

# 一下基于的模板都是纯字符串的
# 创建字符串模板
# prompt_template = PromptTemplate.from_template(
#     "Question:{question}\n{answer}"
# )
# 
# # 定义少样本提示词模板，文本格式，在之前，常用于补偿llm
# few_shot_template = FewShotPromptTemplate(
#     examples=examples,
#     example_prompt=prompt_template,
#     suffix="Question: {input}",
#     input_variables=["input"],
# )
# 
# prompt = few_shot_template.invoke({"input":"《夏洛特烦恼》《你好李焕英》这两部电影的导演是同一个国家的么?"})
# print(prompt)
# 
# model = ChatOpenAI(
#     model="deepseek-chat",
#     base_url="https://api.deepseek.com/v1",
#     max_tokens="2048"
# )
# 
# chain = few_shot_template | model
# chain.invoke({"input":"《夏洛特烦恼》《你好李焕英》这两部电影的导演是同一个国家的么?"}).pretty_print()


# 基于消息的少样本提示词模版
# 1.首先得有一个chatprompt template，规定示例的消息格式
example_template = ChatPromptTemplate.from_messages(
    [
        ("user","{question}"),
        ("ai","{answer}"),
    ]
)

# 2.定义少样本提示词模板，将示例按照模板进行转换
fewshot_template = FewShotChatMessagePromptTemplate(
    examples=examples,
    example_prompt=example_template,
)

# 3.定义ChatPromptTempalte 作为发给llm的最终模板
chat_template = ChatPromptTemplate.from_messages(
    [
        ("system", "请按照示例的推理链，进行回答"),
        fewshot_template, # 将示例插入到最终的message中
        ("user", "{input}")
    ]
)

model = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
    max_tokens=2048
)

chain = chat_template | model
chain.invoke(
    {
        "input":"《夏洛特烦恼》《你好李焕英》这两部电影的导演是同一个国家的么?", 
    }
).pretty_print()