from langchain_core.prompts import FewShotChatMessagePromptTemplate, ChatMessagePromptTemplate,ChatPromptTemplate
from langchain_openai import ChatOpenAI

# 少样本提示词模板
# 借助少样本提示词模板来为llm提过案例
# 少样本提示示例
example = [
    {
        "text":"2 @ 3 =?", 
        "output":"5",
    },

    {
        "text":"4 @ 5 = ?",
        "output":"9",    
    }
]

# 聊天消息模板，将示例转化为聊天消息
few_shot_chat_message = ChatPromptTemplate(
    [
        ("user", "{text}"),
        ("ai", "{output}"),
    ]
)

# 少样本提示词模板
# 根据示例，以及聊天消息模版，将示例转换为llm看的聊天消息
few_shot_prompt_template = FewShotChatMessagePromptTemplate(
    examples=example,
    example_prompt=few_shot_chat_message,
)

# 对于FewShotChatMessagePromptTemplate来说，它可以直接将案例结合模板，转化为消息
# messages=[
#   HumanMessage(content='2 @ 3 =?', additional_kwargs={}, response_metadata={}), 
#   AIMessage(content='5', additional_kwargs={}, response_metadata={}, tool_calls=[], invalid_tool_calls=[]), 
#   HumanMessage(content='4 @ 5 = ?', additional_kwargs={}, response_metadata={}), 
#   AIMessage(content='9', additional_kwargs={}, response_metadata={}, tool_calls=[], invalid_tool_calls=[])]
print(few_shot_prompt_template.invoke({}).to_messages)

# 聊天消息模板，最终发给llm的模板
chat_message_prompt_template = ChatPromptTemplate(
    [
        ("system", "计算特殊操作符{option}"),
        # 添加示例
        few_shot_prompt_template,
        ("user", "{text}"),
    ]
)
# messages=[
#   SystemMessage(content='计算特殊操作符@', additional_kwargs={}, response_metadata={}), 
#   HumanMessage(content='2 @ 3 =?', additional_kwargs={}, response_metadata={}), 
#   AIMessage(content='5', additional_kwargs={}, response_metadata={}, tool_calls=[], invalid_tool_calls=[]), 
#   HumanMessage(content='4 @ 5 = ?', additional_kwargs={}, response_metadata={}), 
#   AIMessage(content='9', additional_kwargs={}, response_metadata={}, tool_calls=[], invalid_tool_calls=[]), 
#   HumanMessage(content='6 @ 4=?', additional_kwargs={}, response_metadata={})
#]
# print(chat_message_prompt_template.invoke(
#     {
#         "option":"@",
#         "text":"6 @ 4=?",
#     }
# ))

model = ChatOpenAI(
    model="deepseek-chat",
    base_url="https://api.deepseek.com/v1",
)

# ChatMessagePromptTemplate = 单条消息，ChatPromptTemplate = 多条消息的组合
chain = chat_message_prompt_template | model
# chain.invoke({ "option":"@", "text":"6@4 = ?"}).pretty_print()