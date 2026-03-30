from langchain_core.example_selectors import LengthBasedExampleSelector, SemanticSimilarityExampleSelector
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

# 反义词⽰例集合
examples = [
    {"input": "happy", "output": "sad"},
    {"input": "tall", "output": "short"},
    {"input": "energetic", "output": "lethargic"},
    {"input": "sunny", "output": "gloomy"},
    {"input": "windy", "output": "calm"},
]

# 字符串模板
example_prompt = PromptTemplate(
    input_variables=["input", "output"],
    template="Input: {input}\nOutput: {output}",
)

# 长度示例选择器
example_selector = LengthBasedExampleSelector(
    examples=examples,
    example_prompt=example_prompt,
    max_length=3,  # 设置最大长度为50
    # get_text_length 就是用来计算示例文本长度的函数
    # get_text_length=lambda example: len(example["input"]) + len(example["output"]) + len("Input: \nOutput: \n"),  # 计算示例文本长度
)
example_selector = SemanticSimilarityExampleSelector.from_examples(
    examples,# 示例集
    OpenAIEmbeddings(model="deepseek-chat"), # 嵌入模型
    Chroma, # 向量数据库
    k=1, # 选择最相似的1个示例
)

dynamic_prompt = FewShotPromptTemplate(
    example_selector=example_selector,
    example_prompt=example_prompt,
    prefix="你是一个反义词助手.",
    suffix="Input: {input}\nOutput:",
    input_variables=["input"],
)

print(dynamic_prompt.invoke({"input": "happy"}).to_messages()[0].content)