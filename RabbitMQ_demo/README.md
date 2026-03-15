# RabbitMQ 三大解耦能力体验 Demo

## 环境准备

```bash
# 1. 启动 RabbitMQ
cd mq-demo
docker compose up -d

# 等待就绪（约 15 秒），看到 started 字样即可
docker logs mq-demo -f

# 2. 安装 Python 依赖
pip install pika
```

管理面板：http://localhost:15672（admin / admin123）

---

## 实验一：时间解耦

**核心体感：Producer 发完就走，Consumer 随时来取，消息不丢。**

```bash
# 终端 1：先运行 Producer（发完 5 条消息后自动退出）
python demo1_producer.py

# 等 10 秒、30 秒、随便等多久...

# 终端 1：再运行 Consumer（立刻收到之前的 5 条消息）
python demo1_consumer.py
```

观察点：Producer 退出后消息安全地在 Queue 中等待，Consumer 后启动也能全部收到。

---

## 实验二：速度解耦

**核心体感：Producer 瞬间灌入 20 条，Consumer 按自己的节奏慢慢消化。**

```bash
# 终端 1：先启动 Consumer（每条消息处理 1 秒）
python demo2_consumer.py

# 终端 2：启动 Producer（瞬间发出 20 条）
python demo2_producer.py
```

观察点：
- 终端 2 的 Producer 不到 0.1 秒就发完退出了
- 终端 1 的 Consumer 花了约 20 秒才处理完，带进度条
- 同时打开管理面板 → Queues → demo2_speed_decouple，看 Ready 列从 20 慢慢降到 0

---

## 实验三：逻辑解耦（Fanout 广播）

**核心体感：一条消息，三个服务同时收到。新增服务不改 Producer 代码。**

```bash
# 终端 1：启动短信服务
python demo3_consumer.py sms

# 终端 2：启动邮件服务
python demo3_consumer.py email

# 终端 3：启动积分服务
python demo3_consumer.py points

# 终端 4：发送注册事件
python demo3_producer.py
```

观察点：
- 终端 4 发了 3 条用户注册事件
- 终端 1/2/3 每个都收到了全部 3 条消息，各自执行不同的业务逻辑
- Producer 完全不知道下游有几个服务

进阶操作：Ctrl+C 关掉积分服务（终端 3），再运行一次 Producer。
短信和邮件服务正常收到消息，积分队列的消息会攒着。
重新启动积分服务后，之前攒的消息会立刻被消费——这同时体现了时间解耦。

---

## 清理

```bash
docker compose down -v
```