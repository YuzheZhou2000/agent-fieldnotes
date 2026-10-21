---
{
  "slug": "agent-teams",
  "title": "Agent Teams：协作拓扑、状态边界与等预算评测",
  "topic": "评测与交付",
  "summary": "从最新协作研究到可落地任务图，拆解角色、通信、共享记忆、调度与失败恢复，检验团队何时值得其成本。",
  "order": 9,
  "updated": "2026-10-13",
  "tags": ["Agent Teams", "多 Agent", "协作拓扑", "等预算"],
  "minutes": 35
}
---

## 团队购买的是哪一种能力

Agent Teams 把计算、上下文、信息和验证责任分给多个执行者。它可能同时调查不同假设，让专家使用不同工具，或把不应共享的状态分开；也可能复制相同错误，增加通信和返工，使同一个问题更贵、更慢。系统设计要回答的不是“开几个角色”，而是 **哪条任务依赖可以并行，哪份信息必须交接，谁有权修改权威状态，怎样证明最终交付正确**。

本篇使用 **2026-10-13** 核查的一手论文、官方文档与代码快照；近期材料包括 9 月 CoMemBench 和 10 月 7 日更新的 Loop-Back Authority。所有实验数字为作者报告，本文未复跑模型、训练编排器或部署团队。架构、合同与伪代码均为工程建议，读者可以据此设计对照实验。

一个实用起点是：先建立强单 Agent，再加入小规模、边界清楚的并行工作；只有交互本身产生可测收益，才扩大自主协作范围。下面分别讨论这个判断的研究证据和实现条件。

**动手入口（2026-10-21 新增）**：[Team Agent 本地实战](team-agent-lab.html)把术语、控制权和证据交接落到完整 Python 工程，包含默认 mock、可选本地模型、顺序 / 并行对照、复核返工与哈希批准。本篇旧研究的核查范围仍为 2026-10-13，不因添加教程链接而改写来源日期。

## 先分清四种执行方式

| 方式 | 谁决定下一步 | 参与者怎样交互 | 应比较的基线 |
|---|---|---|---|
| 单 Agent 加工具 | 一个模型循环 | 工具返回观察，主循环维护目标 | 更好的工具、上下文和更充分推理 |
| 固定工作流 | 程序预定义节点与转移 | 按合同传递产物，可含多个角色提示 | 同一模型串行执行相同工作流 |
| 并行子任务 | 主执行者拆分并汇总 | 工作者主要交付结果，可有受限消息 | 多采样加选择、独立 fan-out / fan-in |
| 协作式多 Agent | 多个执行者影响路由、计划或对方行动 | 交换证据、质疑、协商依赖，可能动态重分工 | 相同预算的单 Agent、工作流与小团队 |

这是一组本文的工程分类，不是统一行业标准。判别依据是决策权、状态和交互，不能仅数模型调用、提示词中的职位名称或聊天窗口。单 Agent 可以并行调用多个只读工具；一个多角色流水线也可能没有自主团队协作。

另一个容易混淆的概念是 **面向人类团队的 AI teammate / Team agent**：它描述服务对象或产品定位，可能只是共享工作台中的一个助手。这个名称不能证明后台采用多 Agent 系统；具体产品应另外核查其工作流、权限与代码，不能按名称归类。三种候选的核查见 [Team agent 选型对照](team-agent-products.html)。

### Claude Code 的 Agent Teams 是一个具体功能

2026-10-13 的官方滚动文档仍将 Teams 标为实验性、默认关闭：lead 协调独立 Claude Code 会话，成员有独立上下文、直接消息和依赖任务板，认领任务使用文件锁。功能只在交互模式启动 teammates，`-p` 和 Agent SDK 会话不因启用变量而获得相同 Teams 机制。<sup><a href="#cite-9">[9]</a></sup>

**不要沿用“subagents 绝不能直接通信”的旧二分法。** 当前具名 subagents 配备 `SendMessage` 时也能通信；启用 Teams 后，某些具名委派会成为 teammates。任务板、生命周期与控制权仍需分别核查。<sup><a href="#cite-10">[10]</a></sup>

Teams 文档还明确一个会话只有一个 team，不支持嵌套 team；任务记录落盘不意味着 `/resume` 或 `/rewind` 恢复 in-process teammates；状态滞后可能阻塞依赖，shutdown 要等待当前请求或工具结束。当前 teammate 的 plan approval 由 lead session 自动批准，**不代表 lead 已实质审查**；动作权限检查是另一路。这些是此刻的产品语义，不能外推到所有 MAS。<sup><a href="#cite-9">[9]</a></sup>

## 研究证据：协作收益依赖基线与任务

### 分解收益不一定来自多个执行者

OneFlow 的《Rethinking the Value of Multi-Agent Workflow》v1（2026-01-18）在七类基准中比较多 Agent 工作流与单模型多轮执行同一工作流。它说明任务分解本身可能有价值，而同质角色未必需要独立执行者。论文的闭源 API 成本部分采用理想 KV-cache 成本估计，另有开源模型的实际测量；不能把理论缓存节约直接写成任意 API 的账单优惠。<sup><a href="#cite-4">[4]</a></sup>

因此，团队至少应赢过“拥有相同分解、工具和验收机会的单 Agent”。否则收益可能来自更好的流程，而不是协作。

### 等预算也需要定义单位

Tran 与 Kiela 的 v2（2026-04-11）在 FRAMES、MuSiQue 多跳推理上比较三个模型家族：多数所测预算条件下，单 Agent 最佳或与多 Agent 统计不可区分。控制变量是 **requested thinking-token budget**；论文专门指出 API 报告、可见推理长度和请求上限存在差异。这不等于实际 FLOPs、美元或端到端资源完全相等，也不能直接外推到有隔离环境和副作用的代码协作。<sup><a href="#cite-3">[3]</a></sup>

评测报告应并列列出 requested 与 actual usage。推理 token 不可观测时保留未知，不用可见文本长度冒充完整计算量。

### 拓扑与任务结构需要匹配

Scaling Agent Systems v3（2026-04-08）包含 **260 种配置、6 个基准、5 种架构、3 个模型家族**。作者将单 Agent 与 Independent、Centralized、Decentralized、Hybrid 对照，并匹配最大总迭代预算；实际 token 和费用仍是不同测量面。Finance Agent 中，集中式平均成功率 0.631、单 Agent 0.349，即 **+28.2 个百分点 / +80.8% 相对变化**；PlanCraft 的多 Agent 变体则出现约 39%–70% 的相对下降。<sup><a href="#cite-1">[1]</a></sup>

跨六个基准的预测模型交叉验证 R² 为 0.373；SWE-bench 与 Terminal-Bench 扩展各只用 20 个任务，单格置信区间较宽。这些结果支持任务—架构匹配，不能给出跨领域通用选择器。“约 45% 饱和阈值”以及错误放大倍数即使出现在正文，也是该实验的经验描述，不是系统设计定律。<sup><a href="#cite-1">[1]</a></sup>

本次代码快照为作者仓库 `8673d6a8d5a764a07b08e4283492380d80257223`，提交于 2026-10-12。README 指向 v2.2.3；CHANGELOG 说明 v2.2.x 修正分析集合等问题，论文引用的 v2.1.3 与当前分析脚本不能混写成同一复现环境。本文读取源码与变更记录，未执行实验。<sup><a href="#cite-2">[2]</a></sup>

### 管理者需要可验证的反馈

Loop-Back Authority v2（2026-10-07）将 43 个笔记本产品各做一对报告，共 86 次运行；角色、模型分配和数据配对，比较可强制返工的层级机制与只能前向调度、评论的扁平机制。**扁平组仍有 Manager，并不是无中心自治网络。** 作者报告扁平组 Utility 较高（d=0.42，p=0.009）；层级组消耗多 51.5% tokens，耗时多 34.3%。<sup><a href="#cite-5">[5]</a></sup>

限制同样重要：这是一个产品报告领域；两组的经理读取范围和最大执行步数也不同，返工不是随机分配；质量主要由 LLM judges 评分，少量人类偏好检查没有形成稳健显著结果。它提示“强制修改但缺乏可靠验收”可能有代价，不能推出层级编排普遍无效或扁平 Teams 一定优胜。<sup><a href="#cite-5">[5]</a></sup>

## 两张图：任务依赖与通信拓扑

**任务图**描述哪个产物必须先完成，**通信图**描述谁可以向谁发什么消息。两者无需相同：三项调查可并行完成，但共同写入一个补丁仍需串行提交；两个工作者可以互相询问，却不能绕过发布者修改目标分支。

| 编排方式 | 合适条件 | 主要成本与失败面 | 推荐限制 |
|---|---|---|---|
| 集中式 coordinator | 汇总目标明确，需要统一验收和副作用所有者 | 主节点上下文、判断与队列成为瓶颈 | 只汇总证据和决策，产物放外部存储 |
| 分层协调 | 子领域有相对独立目标与资源 | 多层摘要损失，错误归因与取消传播更难 | 限制深度，每层绑定验收合同与预算 |
| 去中心化同伴 | 信息分散，需要动态质疑或局部协商 | 冲突、重复探索、共识漂移与消息风暴 | 限定路由、轮次和决策领域，保留仲裁点 |
| 混合式 | 并行探索有价值，写入和验收仍需集中控制 | 同时承担同伴通信与汇总成本 | 调查可互动，权威状态由指定 owner 更新 |

这是工程选型表，收益要实测。集中式系统可以允许同伴消息，分层不等于更大团队，去中心化也不等于任意共享权限。角色称为“经理”或“专家”不会自动产生仲裁能力；决定权要来自任务合同和可检查证据。

### 消息越多，独立性可能越少

一次全互联交换最多有 `n × (n - 1)` 条有向消息；星形汇报与回复约为线性数量。这只是拓扑容量，真实成本还依赖轮数、消息长度和消息是否再次进入模型。相同模型、相同来源、相同提示的多次判断往往相关，不能套用独立投票的成功概率。

工程上可先独立调查，再公开争议和证据，最后定向复核。反复广播未经验证的结论，会把独立探索变成共同锚定。消息类型应区别 `observation`、`claim`、`question`、`proposal`、`decision` 和 `authorization`；一般成员只能提出前几种，授权必须来自受信任来源和控制面。

## 角色、任务合同与动态调度

角色说明“擅长什么”，任务合同说明“这次负责什么”。一个通用 reviewer 可能没有完成某个安全边界的检查；一个研究者也可能在任务改变后继续沿旧假设探索。建议合同至少包含以下字段：

| 字段 | 要解决的歧义 |
|---|---|
| `goal_version`、`task_id`、`attempt` | 当前是哪版用户目标、哪次执行 |
| 依赖及输入产物版本 | 能开始了吗，是否读取了已作废证据 |
| 输出 schema、证据地址与不确定项 | 什么算交付，别人怎样核验 |
| 允许的工具、资源、数据消费者 | 能做什么，能把信息交给谁 |
| 预算、截止时间、最大重试与停止条件 | 探索到什么程度应结束 |
| 认领 owner、租约与 fencing token | 失联后谁接手，怎样拒绝旧执行者写回 |
| grader 与终态 | 是 proposed、verified，还是仅“自称完成” |

**工程建议**：协调器只把依赖满足、输入有效且预算可用的任务放入 ready 队列。认领使用原子更新；租约过期后重派，旧 worker 的写回必须被版本或 fencing 检查拒绝。文件锁能避免同一时刻重复认领，却不替代语义验收、陈旧结果处理和外部动作幂等。

动态分工应同时限制活跃人数、待执行任务数、总推理预算、工具并发和协调轮数。长尾任务可以加一个受限只读替补，但替补与原 worker 的最终结果只接受一次；涉及外部写入时不能盲目复制执行。

MAS-Orchestra（2026 年 ICML，预印本 v5 为 2026-05-21）把协作编排作为训练时的函数调用 RL 问题，使用受控任务难度轴学习系统结构。这是“编排策略也可以训练”的研究方向；额外训练和调用投入需要计入基线，强子 Agent 下的增益也可能缩小。它不证明任意生产任务都适合在线学习协调，更不意味着污染测试等同通用提示注入防御。<sup><a href="#cite-8">[8]</a></sup>

## 共享状态不等于共享整段上下文

至少分开四种状态：权威任务与授权、成员局部工作集、经过验证的共享产物、跨任务长期经验。把它们混成一段 group chat，难以区分新目标、旧猜测、私有观察和已经批准的动作。

CoMemBench v2（2026-09-29）构造 800 个可执行组合工作流、4 个领域，通过 chain、split–join、reuse、overlap、bounded revision 测试交接和隔离。关键问题是：同一个 artifact 对某消费者必需，对另一消费者不适用，更新后又可能失效。它分别度量完成、验证节点进度、必要交接和隔离挑战。<sup><a href="#cite-7">[7]</a></sup>

在固定 executor / worker 的记忆消融中，Repository Code 从 Local-only 到 Full Context，流程成功率由 0% 到 16%，隔离挑战分数从 89.4% 到 71.9%。Local-only **仍保留声明的必要交接**；ICS 的分母是 clean target 成功的匹配样本，不能解释为无条件安全率。更多共享提高可用信息，也可能扩大污染面。<sup><a href="#cite-7">[7]</a></sup>

### 让 artifact 带着有效性合同

以下为建议 schema，不是 CoMemBench 或框架的官方格式；示例中的引用与哈希是占位值，未执行：

```json
{
  "artifact_id": "security-review-01",
  "producer_task": "review-auth",
  "attempt": 2,
  "goal_version": 3,
  "entity": "repository/auth-module",
  "base_commit": "<fixed-commit-sha>",
  "evidence_refs": ["<immutable-log-ref>"],
  "allowed_consumers": ["integrator", "verifier"],
  "verification": "proposed",
  "supersedes": "security-review-00",
  "invalid_if": ["goal_changed", "base_commit_changed"],
  "unknowns": ["integration behavior not exercised"]
}
```

合并结果时应验证来源、实体、输入版本与验收状态，保留冲突和失效记录。旧 artifact 到达得晚，不应覆盖新版；reviewer 的结论可以成为证据候选，不能自带“已验证”的权威性。摘要要指向原始出处，避免一条弱推测被多次转述后变成团队事实。

若并行节点向共享列表追加结果，按 artifact ID 去重并定义排序。简单 list append 不具备幂等性；last-write-wins 也不保证语义正确。可交换的独立观察适合集合合并，补丁、授权和目标版本适合单 owner 或事务性更新。长期记忆的训练与路由另见[记忆策略专题](agent-memory.html)，这里聚焦跨成员交接。

## 框架原语分别提供了什么

| 实现入口 | 控制与状态原语 | 应由应用补足 |
|---|---|---|
| Claude Code Teams | 独立会话、lead、消息、依赖任务板 | 当前恢复限制、文件所有权、业务验收与真实授权 |
| OpenAI Agents SDK | `as_tool()` 保留 manager 控制；handoff 改变当前 turn 的活跃 Agent；代码可并行运行 | 全局任务图、租约、共享产物有效性和副作用所有权 |
| LangGraph | state、nodes、edges、reducers；`Send` 动态 fan-out；checkpointer 保存执行状态 | reducer 的冲突/去重语义、外部事务和业务 grader |

这三种入口不是同一种产品，也不能从“支持多 Agent”推断相同恢复保证。SDK 编排文档强调代码与模型路由可组合；本文核查的 OpenAI 文档快照为 `f53c62451c7f34c15f0c87fa745e05404025420f`（2026-10-13）。<sup><a href="#cite-11">[11]</a></sup><sup><a href="#cite-13">[13]</a></sup>

OpenAI SDK 的应用 context 不会自动发给模型，nested agents-as-tools 默认共享底层应用状态，并没有复制出隔离状态；工具可见性过滤也不能替代对模型所选参数和资源的授权。独立模型上下文、进程隔离和应用状态隔离是三个不同属性。<sup><a href="#cite-12">[12]</a></sup>

LangGraph 的 `Send` 允许按子任务传入不同状态，reducer 决定更新怎样合并；持久 checkpoint 保存图进度。它们能表达任务结构，但正确的合并规则和业务一致性仍需程序定义。<sup><a href="#cite-13">[13]</a></sup><sup><a href="#cite-14">[14]</a></sup>

### 从真实实现读到配置差异

作者 agent-scaling 快照中的 `multiagent_decentralized.py` 实现前一轮同伴答案交换与最终共识选择；类构造默认值与规范运行的 Hydra YAML 不同。集中式实现调用 lead 编排，并在需要时由一个环境路径提交结果。源码导读要同时读构造、实际配置、共享环境和提交路径，不能只复制类名或默认 Agent 数量。<sup><a href="#cite-2">[2]</a></sup>

这些公开实现是实验基础，不是已经审计的生产团队。本文没有运行它们，下面另给一个便于实施和验收的架构设计。

## 架构示例：仓库变更助手

场景是假设用户要求修复某仓库中的缺陷。输入为明确授权范围和固定 base commit；产物是补丁、测试证据与可检查提交。**以下是设计建议，未生产验证，不代表已建立这样的服务。**

<svg viewBox="0 0 760 330" role="img" aria-labelledby="teams-diagram-title teams-diagram-desc" style="width:100%;height:auto;display:block;margin:24px 0">
<title id="teams-diagram-title">同伴调查与单一集成者的仓库变更架构</title>
<desc id="teams-diagram-desc">任务合同与调度器并行派发三个只读调查，结果进入带版本产物存储，再由隔离构建者、集成者和独立验收组成交付链。外部发布只有一个执行者。</desc>
<path class="edge" d="M380 54V77H130V100M380 77V100M380 77H630V100M130 150V184H380V206M380 150V206M630 150V184H380M470 231H545M615 256V282H380"/>
<rect class="accent-node" x="265" y="10" width="230" height="44" rx="7"/>
<rect class="node" x="40" y="100" width="180" height="50" rx="7"/>
<rect class="node" x="290" y="100" width="180" height="50" rx="7"/>
<rect class="node" x="540" y="100" width="180" height="50" rx="7"/>
<rect class="accent-node" x="265" y="206" width="205" height="50" rx="7"/>
<rect class="node" x="545" y="206" width="175" height="50" rx="7"/>
<rect class="node" x="265" y="282" width="230" height="40" rx="7"/>
<g style="font-family:var(--sans);font-size:13px;fill:var(--slate);text-anchor:middle">
<text x="380" y="37">任务合同 / 调度 / 版本产物库</text>
<text x="130" y="129">复现与根因调查</text>
<text x="380" y="129">安全与范围检查</text>
<text x="630" y="129">测试与边界分析</text>
<text x="367" y="228">隔离构建 → 单一集成者</text>
<text x="367" y="245" style="font-size:10px">补丁与证据绑定 hash</text>
<text x="632" y="235">独立 verifier</text>
<text x="380" y="307">授权核验 → 唯一发布 executor</text>
</g>
</svg>

1. **固化目标**：planner 只读仓库，保存目标版本、base commit、允许路径、验收要求，形成依赖图。
2. **并行调查**：根因、安全、测试工作者读取同一版本，返回证据地址、冲突和不确定项。只有问题相关的成员互相通信。
3. **隔离构建**：builder 在专用 worktree 做修改；需要多 builder 时按模块 owner 划分，统一接口合同。共享工作区不交给所有成员同时写。
4. **单一集成**：integrator 检查 base 是否前进、文件是否冲突、依赖是否兼容，再形成一个候选补丁。陈旧补丁重新验证，不能强行套用。
5. **独立验收**：verifier 使用候选补丁和原任务重放复现、回归及边界测试，检查测试没有被跳过或改成自证。失败返回具体证据与有限修复任务。
6. **发布**：executor 核验授权与被验收的 patch hash；授权已覆盖该动作时按原范围执行，新增范围则生成可审查请求。最终查远端状态和部署结果。

“独立 verifier”不只是另一个同模型角色。关键是从原始任务和外部证据验收，保留未通过项；它不应只能看到 builder 的成功摘要。代码交付中的缓存与测试取舍可对照[代码 Agent 交付](coding-agents.html)。

### 协调器把建议转换成受限行动

以下是 **Python 风格伪代码，未执行，函数均为应用需要实现的合同**。它只描述调度过程；真实持久化、事务、权限代理与进程终止仍需实现。

```python
async def run_task(task, store, workers, budget):
    # 原子认领返回租约及 fencing token；没有认领就不执行。
    lease = store.claim_ready(task.id, task.goal_version)
    if lease is None:
        return
    reservation = None
    try:
        inputs = store.valid_inputs(task.dependencies, task.goal_version)
        reservation = budget.reserve(task.max_cost, task.deadline)
        result = await workers.run(
            contract=task,
            inputs=inputs,
            fence=lease.fence,
            deadline=task.deadline,
        )
        # worker 只交候选，验收/版本/租约检查由控制面执行。
        verdict = verify_contract(task, inputs, result)
        store.accept_if_current(
            task.id, lease.fence, task.goal_version,
            result.artifact_hash, verdict,
        )
    except BudgetExhausted:
        store.block_for_budget(task.id, lease.fence)
    except InvalidInputs:
        store.block_for_replanning(task.id, lease.fence)
    except UnknownExternalOutcome as error:
        store.record_unknown(task.id, lease.fence, error.operation_id)
        # 查询真实状态后再决定重试，不能当作已失败。
        store.enqueue_reconciliation(error.operation_id)
    except RetryableReadError as error:
        store.retry_with_limit(task.id, task.attempt, error)
    finally:
        # 结算全部实际消耗，释放尚未用完的预留。
        if reservation is not None:
            budget.settle(reservation, workers.usage(task.id, lease.fence))
        store.release_if_owner(task.id, lease.fence)
```

调度器还需要取消与租约回收路径，并保证产物接收和依赖解锁在一致的事务边界内。预算预留、失败结算和幂等记录不应由自然语言提醒来维持。

## 失败、恢复与取消应是什么语义

MAST v3（2025-10-26，历史基础材料）从 7 个框架的 1600+ 标注轨迹建立 14 类失败模式，归为系统设计、Agent 失配和任务验证。它提供诊断语言，不是当下生产事故比例。下面是面向本架构的工程映射，并非逐项复写 MAST 分类。<sup><a href="#cite-6">[6]</a></sup>

| 失败 | 观察证据 | 合适处理 |
|---|---|---|
| 重复认领或过期 worker 写回 | 租约、attempt、fencing 与版本不匹配 | 控制面拒绝旧提交，保留原尝试记录 |
| 依赖已经交付却一直 blocked | artifact 存在，任务状态未更新 | 原子对齐验收与依赖，核查后修复状态 |
| 接受了错误实体或旧证据 | entity、goal / base 版本、来源不匹配 | 撤销下游结果，只重跑受影响子图 |
| 循环争论、无依据返工 | 消息增长，验收证据没有增加 | 轮数和成本上限，升级到具体检查或人工决策 |
| 工具失联，结果未知 | 请求已发出，响应未落盘 | reconciliation 查询外部状态，禁止盲重放 |
| 提前宣布完成 | 必需节点或 grader 未达终态 | 由控制面判断完成，模型文字只作候选 |

checkpoint 记录系统知道的状态，无法自动确定未确认的外部动作。LangGraph 文档说明 interrupt 恢复会重跑所在节点，因此 interrupt 之前的副作用应幂等或拆到独立步骤。持久图状态不是外部邮件、提交或支付的 exactly-once 保证。<sup><a href="#cite-14">[14]</a></sup><sup><a href="#cite-15">[15]</a></sup>

取消协议至少区分：不再派发、通知 worker、停止或等待在途工具、拒绝迟到写回、保存已发生副作用、清理执行资源。用户看到“已取消”之前，要知道哪些行动已不可逆。租约收回和取消模型采样不会自动撤销已经到达外部服务的请求。详细状态分层见[长任务状态](claude.html)。

## 权限与注入风险会沿协作路径传播

工程上应将同伴消息当有来源的输入，而不是新的用户授权。调查者转述“用户批准发布”，不能替代受信任授权记录；低权限成员也不能借高权限成员转发来执行越权动作。当前 Claude 文档明确将其他 Agent 的消息与人的指令区分。<sup><a href="#cite-9">[9]</a></sup><sup><a href="#cite-10">[10]</a></sup>

典型传播路径是网页或代码注释 → worker 摘要 → 共享记忆 → lead 计划 → 有权限的工具。每次压缩或交接都应保留来源和信任级别，避免低信任指令被“洗成”团队决策。来源标签本身不构成防御，还需在真正执行操作的工具或代理侧校验目标、参数与授权。

建议的防御性评测在隔离、模拟环境中配对：正常任务；同伴消息夹带越权请求；过期或错误实体 artifact；带可疑指令的共享记录；被拒行动转交其他成员；取消后迟到动作。分别记录正常任务成功与违规实际生效，不把一律拒绝算成可用系统。长轨迹攻击研究另见[AgentLAB 评测导读](agent-evaluation.html)。本文没有运行攻击或生产安全审计。

## 延迟、token 与成本怎样核算

**工程成本模型**：团队完成时间取决于任务 DAG 的关键路径、调度与排队、交接、返工和最终验收。只看并行 worker 的最大耗时，会漏掉 planner 与 integrator 的串行部分；只看首 token 更无法衡量交付。

在工作可完美分割的理想模型中，并行比例为 p、工作者数为 n 时，加速上界为 `1 / ((1 - p) + p / n)`；真实协作还要加通信、同步和失败开销。这是分析用上界，不是本篇测得的 Agent 加速比。

成本账本应包含每个成员的 uncached / cached input、output、可获取的 reasoning usage，模型与 effort，工具、环境空闲、重试、观测和持久化。输入上下文被复制、消息广播、模型切换和缓存失效都可能增加费用。更短的上下文也可能丢掉证据，必须与 outcome 一起测。

| 优化候选 | 可能购买的收益 | 应做的对照 |
|---|---|---|
| 增加只读调查 worker | 降低独立问题的关键路径 | 同预算工具并行、多采样与重复探索率 |
| 使用异质专家 | 不同工具、知识或错误分布的互补 | 同质同人数、最强单成员、模型路由成本 |
| 摘要与 artifact 引用 | 减少通信 token | 缺失约束、回查次数、错误实体交接 |
| 动态提前停止或追加预算 | 避免无收益探索，处理长尾 | 完成率、预算越界、p95 与错误早停 |
| 更严格的验证 | 更少无效交付 | 漏报、误报、验收成本与每成功任务费用 |

更多人数、更多讨论与更高模型单价不是质量指标；关注相同约束下的质量—费用—时延 Pareto 前沿。

## 一个可以复现和证伪的评测计划

以下为未执行的实验设计。任务来自真实失败，并按可分解程度、依赖深度、共享写入、工具复杂度和隔离需求分层。固定任务集、模型版本、工具 schema、资源、初始记忆、grader 与授权范围；对在线记忆额外固定顺序或单独报告。

### 四个必需基线

1. **强单 Agent**：同等级模型、相同工具与可用证据，充分调优上下文、推理和验收。
2. **单 Agent 多采样加选择**：用相同总预算生成候选，计入选择者或验证器费用；选择器不能偷看 gold answer。
3. **固定工作流**：复用相同分解和产物合同，串行 / 并行代码路由，隔离“流程设计”的收益。
4. **小团队**：相同总预算与 deadline，在可并行节点尝试少量成员；再比较增加通信、人数或异质性的增量。

模型混用时另报“所有预算给最强单成员”的基线。把工具、最终 grader 或重试机会只给 Teams 的比较没有隔离协作因素。

### 消融比人数曲线更有用

- 关闭同伴通信，保留相同 worker 和输出合同，测纯并行收益。
- 保留通信但关闭额外共享记忆，必要交接仍存在，测记忆暴露的贡献。
- 以确定性路由替换 LLM planner，保持任务合同和可用角色，测动态调度。
- 保留 reviewer 但移除外部证据，只让其看摘要，与完整验收比较。
- 移除强制返工或缩短返工上限，保留相同 grader，测经理权力的增量。
- 同质 / 异质、不同拓扑、不同人数分别变化；不要同时更换模型、预算和验收规则。

### outcome、可靠性与诊断同时报告

| 指标 | 分母或测量终点 |
|---|---|
| 端到端成功率 | 全部被接受任务；infra failure 与 unknown 单列 |
| 重复运行一致性 | 按任务分组，多 trial；注明 pass@k 与 pass^k 含义 |
| 交接有效率 | 所需 consumer 获得当前、正确且被验证的 artifact |
| 隔离挑战 | 正常 / 污染配对，说明条件筛选和样本数 |
| 冲突、重做与重复副作用 | 以任务或实际操作为分母，不只统计消息 |
| p50 / p95 完成时延 | 从接受目标到产物验收，计入排队、返工与失败 |
| 每成功任务费用 | 总消耗除成功任务数；同时保存失败花费 |

用配对任务差异和置信区间评估收益，区分不同任务层，不对很小的样本做普适宣称。独立 judge 应盲于架构，并抽样人工检查；模型评审的偏好和相关性仍可能影响结论。资源保证值、kill 上限与并发也需记录，详见[完整评测合同](agent-evaluation.html)。

可观测性应串起 `run → task → attempt → member → model/tool/message → artifact → verdict`，记录 causal parent、goal version、等待时间、预算预留与结算、取消及外部操作 ID。否则一个 blocked 节点很难区分为工具故障、成员忘记更新状态或依赖已失效。日志访问按角色限制，敏感输入、凭据和长轨迹不用默认全量暴露给团队。

## 选型：从最小协作开始

| 当前任务特征 | 优先尝试 | 升级条件 |
|---|---|---|
| 明确串行、共享同一文件、基线已经稳定 | 强单 Agent 加工具 | 有独立失败面且实测收益超过成本 |
| 多个独立来源或检查维度 | 受限 fan-out / fan-in | 直接交互确实减少遗漏或返工 |
| 工作流程稳定，恢复和可审计性重要 | 显式持久任务图 | 动态 planner 在同预算消融中更好 |
| 信息分布异质，需要互相质疑 | 小规模同伴调查加集中验收 | 证据交接、隔离与停止条件均可测 |
| 多模块可独立实现 | 隔离工作区与单一集成者 | 合并成本没有吞掉并行收益 |
| 高影响外部动作 | 唯一 executor、范围授权、状态查询 | 任意新自治都先经过副作用与取消评测 |

把问题组织成团队，不需要先仿照公司建一套职位。先增加一条有理由的协作边，再测它是否帮助正确交付。保留失败轨迹和被证伪的假设，往往比积累更多角色模板更有工程价值。

## 更新记录与证据边界

- 2026-10-13：新增 Agent Teams 专题，覆盖协作模式、拓扑、状态、调度、恢复、权限、可观测性与等预算评测。
- 使用 Scaling v3、等 thinking-budget v2、OneFlow v1、Loop-Back Authority v2、MAST v3、CoMemBench v2 和 MAS-Orchestra v5；不把不同版本数字混为同一实验。
- Claude、SDK、LangGraph 为官方滚动文档快照；未给独立发布日期的页面仅写核查日，不当作新功能发布日。
- 公开源码阅读范围为指定模块和配置说明，未编译、训练或完整运行；架构、schema 与伪代码为设计建议。
- 本文聚焦内部 Agent 协作；面向人类团队产品的名称不能直接证明其内部拓扑。

<footer><div class="sources">
<h2 id="sources">来源与证据说明</h2>
<ol>
<li id="cite-1"><a href="https://arxiv.org/html/2512.08296v3">Kim 等 · Towards a Science of Scaling Agent Systems，v3</a><span class="source-meta">2025-12-09 首发，2026-04-08 v3 · 2026-10-13 核查方法、预算、跨任务结果、回归和样本限制 · 未复跑</span></li>
<li id="cite-2"><a href="https://github.com/ybkim95/agent-scaling/tree/8673d6a8d5a764a07b08e4283492380d80257223">Agent Scaling · 作者代码固定快照</a><span class="source-meta">提交日期 2026-10-12 · 2026-10-13 读取 README、CHANGELOG、REPRODUCTION、centralized/decentralized 与 lead 模块 · 当前 v2.2.x 分析修正需与论文配置区分</span></li>
<li id="cite-3"><a href="https://arxiv.org/html/2604.02460v2">Tran、Kiela · Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets，v2</a><span class="source-meta">2026-04-02 首发，2026-04-11 v2 · 2026-10-13 核查方法、requested budget、API 记账差异与任务限制 · 未复跑</span></li>
<li id="cite-4"><a href="https://arxiv.org/html/2601.12307v1">Xu 等 · Rethinking the Value of Multi-Agent Workflow: A Strong Single Agent Baseline，v1</a><span class="source-meta">2026-01-18 · 2026-10-13 核查单模型执行、工作流基线与理论 / 实测缓存成本区别 · 未复跑</span></li>
<li id="cite-5"><a href="https://arxiv.org/html/2609.14767v2">Agachan 等 · Loop-Back Authority in LLM Agent Teams，v2</a><span class="source-meta">2026-09-13 首发，2026-10-07 v2 · 2026-10-13 核查配对设置、Utility、开销和 judge / 人类检查限制 · 近期预印本，未复跑</span></li>
<li id="cite-6"><a href="https://arxiv.org/html/2503.13657v3">Cemri 等 · Why Do Multi-Agent LLM Systems Fail?，v3 / MAST</a><span class="source-meta">2025-03-17 首发，2025-10-26 v3 · 2026-10-13 核查失败分类与验证讨论 · 历史基础材料，不作当前事故分布</span></li>
<li id="cite-7"><a href="https://arxiv.org/html/2609.32192v2">Zhao 等 · CoMemBench，v2</a><span class="source-meta">2026-09-26 首发，2026-09-29 v2 · 2026-10-13 核查拓扑、Local-only / Full Context 消融与 ICS 条件分母 · 近期预印本，未复跑</span></li>
<li id="cite-8"><a href="https://proceedings.mlr.press/v306/ke26c.html">Ke 等 · MAS-Orchestra，ICML 2026</a><span class="source-meta">2026 年正式论文；预印本 2026-01-21 首发、2026-05-21 v5 · 2026-10-13 核查正式摘要与 v5 编排 / 基线限制 · 未训练或复跑</span></li>
<li id="cite-9"><a href="https://code.claude.com/docs/en/agent-teams">Claude Code · Orchestrate teams of sessions</a><span class="source-meta">滚动官方文档，无独立发布日期 · 2026-10-13 核查交互模式、任务板、权限、计划批准与恢复限制 · 未实测 Teams</span></li>
<li id="cite-10"><a href="https://code.claude.com/docs/en/sub-agents">Claude Code · Create custom subagents</a><span class="source-meta">滚动官方文档，无独立发布日期 · 2026-10-13 核查具名成员通信及与 Teams 的区别 · 未实测</span></li>
<li id="cite-11"><a href="https://github.com/openai/openai-agents-python/blob/f53c62451c7f34c15f0c87fa745e05404025420f/docs/multi_agent.md">OpenAI Agents SDK · 编排文档固定快照</a><span class="source-meta">提交日期 2026-10-13 · 同日核查 as_tool、handoff 与代码并行的控制权 · 未执行模型请求</span></li>
<li id="cite-12"><a href="https://github.com/openai/openai-agents-python/blob/f53c62451c7f34c15f0c87fa745e05404025420f/docs/context.md">OpenAI Agents SDK · Context 文档固定快照</a><span class="source-meta">提交日期 2026-10-13 · 同日核查共享应用状态、模型上下文与参数授权区别 · 未执行</span></li>
<li id="cite-13"><a href="https://docs.langchain.com/oss/python/langgraph/graph-api">LangGraph · Graph API</a><span class="source-meta">滚动官方文档，无独立发布日期 · 2026-10-13 核查 Send、state 与 reducers · 未运行框架</span></li>
<li id="cite-14"><a href="https://docs.langchain.com/oss/python/langgraph/checkpointers">LangGraph · Checkpointers</a><span class="source-meta">滚动官方文档，无独立发布日期 · 2026-10-13 核查 checkpoint、pending writes 和重放语义</span></li>
<li id="cite-15"><a href="https://docs.langchain.com/oss/python/langgraph/interrupts">LangGraph · Interrupts</a><span class="source-meta">滚动官方文档，无独立发布日期 · 2026-10-13 核查节点重跑与副作用幂等要求 · 未故障注入</span></li>
</ol>
</div></footer>
