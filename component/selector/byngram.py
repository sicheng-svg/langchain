from langchain_community.example_selectors import NGramOverlapExampleSelector
from langchain_core.prompts import FewShotPromptTemplate, PromptTemplate

# 翻译⽰例
 
examples = [
    {"input": "See Spot run.", "output": "看⻅Spot跑。"},
    {"input": "My dog barks.", "output": "我的狗叫。"},
    {"input": "Spot can run.", "output": "Spot可以跑。"},
]
# 字符串模板
example_prompt = PromptTemplate(
    input_variables=["input", "output"],
    template="Input: {input}\nOutput: {output}",
)

# NGram ⽰例选择器
example_selector = NGramOverlapExampleSelector(
    examples=examples,
    example_prompt=example_prompt,
    threshold=-1.0, # 设置阈值为-1.0，表示选择所有示例
                    # 0.0 只输出重叠分数大于0的示例
                    # 大于等于1.0，所有示例都不输出
)

# ⽤于实例化⽰例的模板
dynamic_prompt = FewShotPromptTemplate(
    example_selector=example_selector,
    example_prompt=example_prompt,
    prefix="给出每个输⼊的中⽂翻译",
    suffix="Input: {sentence}\nOutput:",
    input_variables=["sentence"],
)

# 按照重叠分数排序
print(dynamic_prompt.invoke({"sentence": "Spot can run fast."}).to_messages()[0].content)