from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

model = ChatOpenAI(model="deepseek-chat", base_url="https://api.deepseek.com/v1")

# 定义输出结构：Pydantic类
class Joke(BaseModel):
    """
    给⽤⼾讲⼀个笑话。
    """ 
    setup: str = Field(description="这个笑话的开头")
    punchline: str = Field(description="这个笑话的妙语")
    rating: Optional[int] = Field(
    default=None, description="从1到10分，给这个笑话评分"
)

# 定义输出解析器
parser = PydanticOutputParser(pydantic_object=Joke)
# print(parser.get_format_instructions())

# 定义提示词模板
prompt = ChatPromptTemplate.from_template(
    template="Answer the user query.\n{format_instructions}\n{query}\n",
    partial_variables={"format_instructions": parser.get_format_instructions()}, # 将格式化说明作为部分变量传入提示词模板，不用每次调用时都传入
)

# 定义链
chain = prompt | model | parser
# 调用链
result = chain.invoke({"query": "讲一个笑话"})
print(result)