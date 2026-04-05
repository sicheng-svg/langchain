from langchain.chat_models import init_chat_model

model = init_chat_model(
    model="qwen3:4b",
    model_provider="ollama",
)

model.invoke("你好").pretty_print()