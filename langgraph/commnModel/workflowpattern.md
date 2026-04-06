# LangGraph 常见工作流模式总结

> LangGraph 的工作流模式类似于软件工程中的设计模式——面对 LLM/Agent 编排中反复出现的问题，总结出的可复用解决方案。

## 全局对比

| 模式 | 核心问题 | 下游节点确定时机 | 执行路径数 | 类比设计模式 | 核心 API |
|------|----------|------------------|------------|--------------|----------|
| Prompt Chaining | 步骤有先后依赖 | 编译时 | 1 条 | 责任链 | `add_edge` |
| Parallelization | 子任务互不依赖 | 编译时 | 全部并行 | Fork-Join | `add_edge`（多条） |
| Router | 不同输入走不同路 | 编译时固定候选，运行时选一条 | 只走 1 条 | 策略模式 | `add_conditional_edges` 返回 `str` |
| Orchestrator-Workers | 子任务动态确定 | 运行时 | 动态决定 | 中介者模式 | `add_conditional_edges` 返回 `list[Send]` |
| Evaluator-Optimizer | 输出质量要保证 | 编译时 | 1 条（含回环） | 重试 + 自省 | `add_conditional_edges`（条件回边） |
| Human-in-the-Loop | 关键步骤需人确认 | 编译时 | 1 条（含暂停点） | 模板方法（钩子） | `interrupt()` + `Command(resume=...)` |

---

## 1. Prompt Chaining（提示链）

### 工作模式

任务被拆成多个步骤**严格按顺序执行**，前一步的输出作为后一步的输入。步骤之间可以插入"门控"（Gate）节点，检查上一步结果是否合格，不合格则提前终止或要求重做。

### 架构图

```
[生成大纲] → [门控检查] → [撰写正文] → [门控检查] → [润色输出]
                 ↓                           ↓
              不合格终止                   不合格终止
```

### 适用场景

- 步骤之间有严格的先后依赖关系
- 每一步的质量直接影响下一步
- 例：先生成大纲 → 检查大纲合理性 → 根据大纲写正文 → 检查正文质量 → 润色输出

### 代码骨架

```python
graph.add_edge(START, "generate_outline")
graph.add_edge("generate_outline", "gate_check_1")
graph.add_conditional_edges("gate_check_1", quality_check)  # 通过 → 下一步 / 不通过 → END
graph.add_edge("gate_check_1", "write_body")
graph.add_edge("write_body", "gate_check_2")
graph.add_edge("gate_check_2", "polish_output")
graph.add_edge("polish_output", END)
```

---

## 2. Parallelization（并行化 / Fan-out Fan-in）

### 工作模式

把一个任务**拆分成多个互不依赖的子任务**，交给不同的节点**同时并行处理**，最后将所有结果汇总到一个节点。下游的并行分支在编译时就固定了。

- **Fan-out（扇出）**：一个节点的输出分发给多个下游节点（一变多）
- **Fan-in（扇入）**：多个节点的输出汇聚到一个节点（多变一）

### 架构图

```
                ┌→ [安全审查 Agent] ──┐
                │                      │
[代码提交] ────┼→ [风格审查 Agent] ──┼→ [汇总报告] → [输出]
                │                      │
                └→ [性能审查 Agent] ──┘
           fan-out                 fan-in
```

### 适用场景

- 子任务之间没有依赖关系，可以同时执行
- 最终需要将多个结果合并
- 例：多个 Agent 并行审查同一段代码，最后汇总报告

### 代码骨架

```python
# Fan-out：一个上游连接多个下游
graph.add_edge("input", "security_agent")
graph.add_edge("input", "style_agent")
graph.add_edge("input", "perf_agent")

# Fan-in：多个上游汇聚到同一个下游
graph.add_edge("security_agent", "merge")
graph.add_edge("style_agent", "merge")
graph.add_edge("perf_agent", "merge")

# 配合 Annotated reducer 自动合并结果
class State(TypedDict):
    results: Annotated[list, operator.add]  # 各 agent 的结果会自动拼接
```

---

## 3. Router（路由）

### 工作模式

根据输入内容**动态选择唯一一条路径**执行，其他路径完全不执行。通常用一个 LLM 或分类器来做路由决策。路径之间是**互斥**的。

### 架构图

```
                          ┌→ [售前处理] ──┐
                          │                │
[用户输入] → [路由分类器] ┼→ [售后处理] ──┼→ [输出]
                          │  （只走一条）   │
                          └→ [技术处理] ──┘
```

### 适用场景

- 不同类型的输入需要完全不同的处理方式
- 例：客服系统根据问题类型路由到售前/售后/技术

### 代码骨架

```python
def router(state):
    if state["type"] == "pre_sale":
        return "pre_sale_handler"     # 返回字符串 → 只走一条
    elif state["type"] == "after_sale":
        return "after_sale_handler"
    return "technical_handler"

graph.add_conditional_edges("classifier", router)
```

### 与并行化的关键区别

| 维度 | 并行化 | 路由 |
|------|--------|------|
| 执行几条路 | **全部**并行执行 | **只走一条** |
| 路由函数返回值 | 不需要（编译时写死） | 返回 `str`（节点名） |
| 目的 | 分工协作 | 分类分流 |

---

## 4. Orchestrator-Workers（编排-工作者）

### 工作模式

由一个中心编排器（Orchestrator）**运行时动态决定**需要哪些子任务、需要多少个 worker，通过 `Send` API 动态分发任务。所有 worker 执行完后，汇总者合并结果。

### 架构图

```
                         ┌→ [Worker 实例1] ──┐
                         │                    │
[编排者] → dispatch() ──┼→ [Worker 实例2] ──┼→ [汇总者] → [输出]
  (拆分子任务)            │                    │
                         └→ [Worker 实例N] ──┘
                       数量由编排者运行时决定
```

### 适用场景

- 子任务的数量和内容无法提前确定
- 需要根据输入动态拆解任务
- 例：LLM 分析一个主题后决定需要写 3 个章节还是 5 个章节

### 核心 API：Send

```python
from langgraph.types import Send

def dispatch(state):
    # 返回 Send 列表，每个 Send 创建一个独立的 worker 实例
    return [
        Send("worker", {"task": task})  # 第一个参数：目标节点名
        for task in state["tasks"]       # 第二个参数：该实例的独立输入
    ]

graph.add_conditional_edges("orchestrator", dispatch)
```

**Send 的特点**：
- 每个 Send 为同一个 worker 节点创建一个**独立的执行实例**
- 第二个参数直接作为 worker 的输入，**不经过主状态**
- 所有实例**并行执行**
- 执行完后，返回值按主状态的 reducer 规则合并

### 与并行化的关键区别

| 维度 | 并行化 | 编排-工作者 |
|------|--------|-------------|
| 下游节点确定时机 | **编译时**固定 | **运行时**动态决定 |
| 分支数量 | 固定（写了几个 `add_edge` 就是几条） | 动态（`Send` 列表的长度由 LLM 决定） |
| 每条路的数据 | 共享同一份 state | 每个 worker 收到**独立数据** |
| 核心 API | `add_edge` | `Send` |

---

## 5. Evaluator-Optimizer Loop（评估-优化循环）

### 工作模式

生成结果后不直接输出，而是让一个评估器检查质量。不达标则把**反馈信息**送回生成器重新生成，直到通过评估或达到最大重试次数。

### 架构图

```
                                    合格
[生成器 Generator] → [评估器 Evaluator] ──→ [通过输出]
       ↑                    │
       └────────────────────┘
         不合格，附带反馈重试
```

### 适用场景

- 对输出质量有明确的评判标准
- 例：生成代码 → 跑测试 → 测试不过就带着错误信息重新生成

### 代码骨架

```python
def should_retry(state):
    if state["score"] >= 0.8:
        return "output"         # 合格，输出
    if state["retry_count"] >= 3:
        return "output"         # 达到最大重试次数，强制输出
    return "generator"          # 不合格，带反馈重新生成

graph.add_conditional_edges("evaluator", should_retry)
```

### 注意事项

- 必须设置**最大重试次数**，防止无限循环
- 反馈信息要具体，告诉生成器哪里不好、怎么改，而不是简单说"不合格"

---

## 6. Human-in-the-Loop（人机交互）

### 工作模式

在关键节点**暂停图的执行**，将控制权交给人类审核。人类确认后通过 `Command(resume=...)` 恢复执行。**必须配合 checkpointer 使用**，因为暂停时需要持久化图的状态。

### 架构图

```
                                           批准
[AI 生成草稿] → [interrupt() 暂停] ────────────→ [执行发送]
                        │
                        └── 拒绝，附带修改意见 ──→ [回到生成节点]
```

### 适用场景

- 涉及敏感操作（发送邮件、删除数据、资金操作）
- 需要人类判断 AI 无法自主决定的问题
- 例：AI 草拟邮件 → 人类审核 → 批准发送或打回修改

### 核心机制

`interrupt()` 的"暂停恢复"本质上是**存档读档**：

1. **第一次 invoke**：图执行到 `interrupt()` → checkpointer 保存完整状态 → `invoke` 返回
2. **第二次 invoke**：传入 `Command(resume=...)` → checkpointer 根据 `thread_id` 恢复状态 → 从断点继续执行

```python
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

# 人类审核节点
def human_review(state):
    decision = interrupt({"message": "请审核", "draft": state["draft"]})
    if decision == "approve":
        return {"approved": True}
    return {"draft": decision, "approved": False}

# 必须配置 checkpointer
checkpointer = InMemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# 两次 invoke 用同一个 thread_id
config = {"configurable": {"thread_id": "session-001"}}
graph.invoke({"topic": "退款"}, config)               # 第一次：执行到 interrupt 暂停
graph.invoke(Command(resume="approve"), config)         # 第二次：恢复执行
```

### 关键概念

- **`thread_id`**：不是操作系统线程，只是一个字符串标识符（类似 session ID），用于在 checkpointer 中定位存档
- **`InMemorySaver`**：开发环境用的内存 checkpointer，生产环境应替换为 `SqliteSaver` 或 `PostgresSaver`
- **`Command(resume=...)`**：`resume` 的值会作为 `interrupt()` 的返回值注入回节点函数

---

## 模式组合

这些模式在实际项目中很少单独使用，通常是**嵌套组合**的。例如：

```
GitHub Code Review Bot = Router（判断语言）
                       + Parallelization（并行多个审查 Agent）
                       + Evaluator-Optimizer（检查审查结果质量）
                       + Human-in-the-Loop（关键问题需人工确认）
```

选择模式的决策树：

```
任务能拆成独立子任务吗？
├── 能 → 子任务在编译时就能确定吗？
│       ├── 能 → Parallelization（并行化）
│       └── 不能 → Orchestrator-Workers（编排-工作者）
│
└── 不能 → 任务需要根据输入走不同路径吗？
            ├── 是 → Router（路由）
            └── 否 → 需要保证输出质量吗？
                    ├── 是 → Evaluator-Optimizer（评估-优化循环）
                    └── 否 → Prompt Chaining（提示链）

任何模式都可以叠加 Human-in-the-Loop（在关键节点加 interrupt）
```