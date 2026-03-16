from langchain.chat_models import init_chat_model

# init_chat_model 是langchain提供的上层函数，在其他三方库的基础上进行封装，提供了一套通用的创建接口
deepseek_model = init_chat_model(
    model="deepseek-chat",
    model_provider="openai",
    base_url="https://api.deepseek.com/v1",
)
print(f"deepseek_model: {deepseek_model.invoke('10个字介绍一下猫?').content}")

# 可配置的model
# 所以使用init_chat_mode，必须指定model和供应商。
# 如果将某个字段设置为了configurable，不管有没有默认值，他都使用你invoke时提供的。如果你在invoke没提供时，就使用默认值
# 所以放进configurable参数的字段，就表示他可能在运行时动态改变
# 可以使用config_prefix参数，指定在configurable字段前的前缀，默认为configurable
# 这样在多模型场景下，就可以区分不同模型的可配置字段了
config_model = init_chat_model(
    model = "deepseek-chat",
    model_provider="openai",
    base_url="https://api.deepseek.com/v1",
    configurable_fields = ("temperature",),
)

print(f"config_model: {config_model.invoke(
    input = "10个字介绍一下猫?", 
    config = {"configurable":{"temperature": 2}}
).content}")