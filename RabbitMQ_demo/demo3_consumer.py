"""
实验三：逻辑解耦 - Consumer 端
用法：python demo3_consumer.py <sms|email|points>
"""
import json
import time
import signal
import sys
from common import get_channel

# 三种服务的模拟行为
SERVICES = {
    'sms': {
        'queue': 'fanout_sms_queue',
        'name': '短信服务',
        'action': lambda d: f"→ 向 {d['phone']} 发送验证码短信",
        'delay': 0.3,
    },
    'email': {
        'queue': 'fanout_email_queue',
        'name': '邮件服务',
        'action': lambda d: f"→ 向 {d['name']} 发送欢迎邮件",
        'delay': 0.8,
    },
    'points': {
        'queue': 'fanout_points_queue',
        'name': '积分服务',
        'action': lambda d: f"→ 为 {d['name']} 赠送 100 新人积分",
        'delay': 0.2,
    },
}

if len(sys.argv) < 2 or sys.argv[1] not in SERVICES:
    print("用法: python demo3_consumer.py <sms|email|points>")
    sys.exit(1)

svc_key = sys.argv[1]
svc = SERVICES[svc_key]

connection, channel = get_channel()

# 声明同一个 Fanout Exchange（幂等操作）
channel.exchange_declare(exchange='user_register_fanout', exchange_type='fanout', durable=True)

# ★ 每个服务声明自己的队列，并绑定到同一个 Fanout Exchange
# 这就是逻辑解耦的关键：
#   - 短信服务绑定 fanout_sms_queue
#   - 邮件服务绑定 fanout_email_queue
#   - 积分服务绑定 fanout_points_queue
# 三个队列都绑到 user_register_fanout，所以每条消息三个队列都会收到一份副本
channel.queue_declare(queue=svc['queue'], durable=True)
channel.queue_bind(queue=svc['queue'], exchange='user_register_fanout')

print("=" * 50)
print(f" 实验三：逻辑解耦 - {svc['name']}")
print("=" * 50)
print()
print(f"  监听队列: {svc['queue']}")
print(f"  等待注册事件... (Ctrl+C 退出)")
print()

def on_message(ch, method, properties, body):
    event = json.loads(body)
    user = event['data']
    action = svc['action'](user)

    print(f"  [收到] 用户 {user['name']}({user['user_id']}) 注册")
    print(f"         {action}")

    time.sleep(svc['delay'])  # 模拟业务处理

    ch.basic_ack(delivery_tag=method.delivery_tag)
    print(f"         ✓ 处理完成")
    print()

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=svc['queue'], on_message_callback=on_message)

signal.signal(signal.SIGINT, lambda s, f: (channel.stop_consuming(), sys.exit(0)))
channel.start_consuming()
connection.close()