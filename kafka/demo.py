"""
Kafka Python 示例 — 基于 confluent-kafka-python (底层封装 librdkafka)
安装: pip install confluent-kafka

假设本地已启动 Kafka 集群, bootstrap server 在 localhost:9092
"""

# ============================================================
#  Producer 示例
# ============================================================
from confluent_kafka import Producer
import json

def delivery_callback(err, msg):
    """
    发送结果的回调函数
    对应架构图中最后一步: Callback — 成功返回 offset / 失败重试
    """
    if err is not None:
        print(f"[Producer] 发送失败: {err}")
    else:
        # msg.partition() 和 msg.offset() 告诉你消息落在了哪
        print(f"[Producer] 发送成功 → topic={msg.topic()}, "
              f"partition={msg.partition()}, offset={msg.offset()}")


def run_producer():
    # ① 配置 — bootstrap.servers 就是你之前学的 Metadata 请求的入口
    conf = {
        "bootstrap.servers": "localhost:9092",  # 任意填几个 Broker 地址
        "acks": "all",                          # 等 ISR 全部确认, 最安全
        "linger.ms": 5,                         # 攒 5ms 的 batch 再发送
        "batch.size": 16384,                    # 缓冲区单个 batch 最大 16KB
    }
    producer = Producer(conf)

    # ② 发送消息 — 指定 topic + key + value
    topic = "user-events"

    messages = [
        {"user_id": "player_001", "action": "login",    "level": 15},
        {"user_id": "player_002", "action": "purchase",  "item": "sword"},
        {"user_id": "player_001", "action": "logout",    "duration": 3600},
        {"user_id": "player_003", "action": "login",     "level": 42},
    ]

    for msg in messages:
        # key 决定分区: 同一个 player_id 的消息一定落在同一个 Partition, 保证有序
        # value 是消息体, 这里用 JSON 序列化
        producer.produce(
            topic=topic,
            key=msg["user_id"],                      # ③ Partitioner 会对 key 做 hash
            value=json.dumps(msg),                    # ② 序列化 (这里手动 JSON, 也可以用 Avro/Protobuf)
            callback=delivery_callback,
        )
        # produce() 是异步的, 消息先进入内部缓冲区 (RecordAccumulator)
        # 不会立即发送, 需要 flush 或 poll 来触发真正的网络发送

    # ④ flush 确保缓冲区中所有消息都发出去
    # 等价于: Sender 线程把攒的 batch 全部发完
    producer.flush()
    print("[Producer] 所有消息发送完毕")


# ============================================================
#  Consumer 示例
# ============================================================
from confluent_kafka import Consumer, KafkaError

def run_consumer():
    # ① 配置 — group.id 是必须的, 决定了这个 Consumer 属于哪个 Group
    conf = {
        "bootstrap.servers": "localhost:9092",
        "group.id": "game-analytics-group",     # Consumer Group ID
        "auto.offset.reset": "earliest",        # 没有历史 offset 时从头开始读
        "enable.auto.commit": False,            # 关闭自动提交, 手动控制
    }
    consumer = Consumer(conf)

    # ② subscribe — 声明要消费的 Topic
    # 此时会触发 JoinGroup → Rebalance → 分配 Partition
    consumer.subscribe(["user-events"])
    print("[Consumer] 已订阅 user-events, 等待 Rebalance 分配 Partition...")

    try:
        while True:
            # ③ poll — 主动从 Leader Partition 拉取消息
            # timeout=1.0 表示最多等 1 秒, 没消息就返回 None
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue  # 没拉到消息, 继续轮询

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    # 读到了这个 Partition 的末尾, 正常现象
                    print(f"[Consumer] Partition {msg.partition()} 已读到末尾")
                else:
                    print(f"[Consumer] 错误: {msg.error()}")
                continue

            # ④ 反序列化 — byte[] → Python 对象
            key = msg.key().decode("utf-8") if msg.key() else None
            value = json.loads(msg.value().decode("utf-8"))

            # ⑤ 业务处理
            print(f"[Consumer] 收到消息: partition={msg.partition()}, "
                  f"offset={msg.offset()}, key={key}, value={value}")

            # 这里放你的业务逻辑, 比如:
            # - 写入数据库
            # - 更新玩家在线状态
            # - 触发推送通知

            # ⑥ 手动提交 offset — 处理完再提交, 确保 at-least-once
            # offset 会写入 __consumer_offsets 这个内部 Topic
            consumer.commit(asynchronous=False)

    except KeyboardInterrupt:
        print("[Consumer] 收到中断信号, 正在退出...")
    finally:
        # 退出前通知 Coordinator, 触发 Rebalance 把 Partition 分给其他 Consumer
        consumer.close()


# ============================================================
#  运行
# ============================================================
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "consume":
        run_consumer()
    else:
        run_producer()

    # 使用方式:
    #   python kafka_example_python.py           → 运行 Producer
    #   python kafka_example_python.py consume   → 运行 Consumer