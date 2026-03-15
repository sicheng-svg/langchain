"""
实验二：速度解耦 - Consumer 端（慢速处理）
"""
import json
import time
import signal
import sys
from common import get_channel

connection, channel = get_channel()
channel.queue_declare(queue='demo2_speed_decouple', durable=True)

# ★ prefetch_count=3：同时最多处理 3 条未 ACK 的消息
# 即使 Queue 里有 20 条，Broker 也只会先推 3 条过来
channel.basic_qos(prefetch_count=3)

print("=" * 50)
print(" 实验二：速度解耦 - Consumer（慢速处理）")
print("=" * 50)
print()
print("  prefetch_count = 3（Broker 最多同时推 3 条未 ACK 的消息）")
print("  每条消息模拟 1 秒处理时间")
print("  等待 Producer 发送消息... (Ctrl+C 退出)")
print()

count = 0

def on_message(ch, method, properties, body):
    global count
    count += 1
    data = json.loads(body)
    task_id = data['task_id']

    # 进度条
    bar = '█' * count + '░' * (20 - count)
    print(f"  [{bar}] {count}/20  处理任务 #{task_id}...", end='', flush=True)

    # 模拟耗时业务处理
    time.sleep(1)

    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(f" ✓ ACK")

    if count >= 20:
        print()
        print("✓ 全部 20 条消息处理完毕。")
        print("  结论：Producer 瞬间发完就走了，Consumer 按自己的速度慢慢消化。")
        print("  Queue 就是削峰填谷的缓冲区。")
        ch.stop_consuming()

channel.basic_consume(queue='demo2_speed_decouple', on_message_callback=on_message)

signal.signal(signal.SIGINT, lambda s, f: (channel.stop_consuming(), sys.exit(0)))
channel.start_consuming()
connection.close()