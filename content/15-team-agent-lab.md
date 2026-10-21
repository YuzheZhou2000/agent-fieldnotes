---
{
  "slug": "team-agent-lab",
  "title": "Team Agent 实战：从术语、控制权到本地协作工程",
  "topic": "运行时与状态",
  "summary": "用可运行的 Python 发布评审工程学习分工、并行、证据交接、复核返工与批准；默认 mock 验证编排，可选本地模型真正参与计划和内容处理。",
  "order": 15,
  "updated": "2026-10-21",
  "tags": ["Team Agent", "本地实战", "编排", "并行", "Python"],
  "minutes": 35,
  "collapsibleToc": true
}
---

## 本篇的终点是一份可检查的本地产物

读完以后，你应能画出控制权和证据流，解释每个角色收到什么，亲手运行一个 planner、两位 worker、reviewer 与 synthesizer 的协作闭环，并根据日志判断：是真的并行、只是换角色串行，还是失败后错误地继续汇总。

这不是另一份产品名单。研究收益和拓扑取舍见[团队协作综述](agent-teams.html)，相似产品名字的区别见[Team agent 选型](team-agent-products.html)。本文新增仓库内完整工程 **Team Agent Lab 0.1.0**：Python 3.9+ 标准库，无需密钥、第三方依赖或付费调用；可选接入你自己启动的本地兼容端点。

样例任务是评审一个**完全虚构的 Helios 发布包**。实现文档承认跨进程去重未实现，测试报告承认写成功后回执丢失的恢复未测，政策允许隔离生产写能力的只读 shadow。最终产物是带证据 ID 的评审单；不会部署服务、执行 shell、读取用户目录或发送真实工单。

## 先拆开两个轴，再讨论是不是团队

“用了固定工作流，所以不算多 Agent”与“写了四个职位，所以已经有四个智能体”都过于简化。**执行单元是否由模型驱动**，和**控制流由谁决定**是两个独立的设计问题。

| 执行单元 | 控制流 | 能说明什么 |
|---|---|---|
| 普通函数或 mock 规则 | 代码固定 | 可以验证编排与状态合同，没有 LLM 协作证据 |
| 有不同指令、输入与职责的模型单元 | 代码规定阶段 | 可以是受控多 Agent 工作流，仍需验证分工收益 |
| 模型单元 | 模型决定路由、分解或重规划 | 自主性更大，也增加误调度、循环与预算治理成本 |

Anthropic 的基础文章区分预定义 workflow 与模型动态控制的 agent；OpenAI SDK 官方同时允许代码编排与 LLM 编排，并明确两者可组合。命名口径不同，判断时应说明控制权，而非试图给所有系统盖同一枚标签。<sup><a href="#cite-1">[1]</a></sup><sup><a href="#cite-4">[4]</a></sup>

本工程默认叫**多智能体编排机制模拟器**：mock 完全是人工规则，不能代表模型推理。local 模式会把 planner 的资料分配、worker 的分析、reviewer 的反馈和最终文本交给真实模型生成；代码仍固定两个 worker 槽位、允许资料、阶段转移和预算。它是有界的模型工作流，不是开放式自治团队，也不要求不同角色使用不同模型或独立操作系统进程。

## 当前官方机制：哪些相似，哪些不能互换

以下于 **2026-10-21** 复核。滚动文档描述当前接口，不把核查日当作功能发布日期；没有运行 Claude Teams、OpenAI SDK 或 xAI 托管团队。

### Claude Code Agent Teams 是具体的会话协调功能

当前文档仍标实验性、默认关闭。lead 协调独立 Claude Code 实例，成员各有上下文；具备相应 Task tools 时通过共享任务表协调，也有消息和依赖认领机制。启用 experimental flag 后，`-p` 非交互模式和 Agent SDK 会话仍不会生成 teammates。<sup><a href="#cite-2">[2]</a></sup>

**“能互聊”不是唯一分界线**：具名 subagents 在配备 `SendMessage` 时也能通信。Teams 的区别还包括独立实例、共享任务与生命周期协调；不能从聊天面板或角色名字推断已经建立某种团队。另要分开计划批准与动作权限：当前文档描述，某些 spawn-time plan 请求可自动批准，并不等于 lead 已审阅计划。产品的恢复和 shutdown 限制必须按当前文档检查。<sup><a href="#cite-2">[2]</a></sup><sup><a href="#cite-3">[3]</a></sup>

### OpenAI SDK 的控制权转移与托管层是不同原语

在本次读取的固定文档快照中，`Agent.as_tool()` 让 specialist 做一个有界子任务并把结果返回 manager；handoff 则切换当前 turn 的活动 Agent，由目标 specialist 接着负责。message 只传递信息，不必转移控制权。SDK local context 是 Python 应用状态，**不会自动发送给模型**；nested agent-as-tool 也不默认复制隔离的应用状态。<sup><a href="#cite-4">[4]</a></sup>

同时，当前 Models 文档还有实验性 hosted multi-agent：子 Agent 在 OpenAI 服务端创建，应用不调度这些子 Agent；它与客户端 handoff / agents-as-tools 不同，该实验模式拒绝 SDK handoffs。因此不能把 SDK 概括成“只有客户端编排”。本 demo 不依赖这项托管 beta。最新稳定发行核查为 **v0.24.0，2026-10-15**，发行版本与主线文档快照分别记录。<sup><a href="#cite-5">[5]</a></sup><sup><a href="#cite-6">[6]</a></sup>

### xAI 的服务端团队不能用本地兼容端点复刻

xAI Multi Agent 文档标注 **2026-10-10 更新**：所述 beta 提供 4 / 16 agent 配置，普通输出主要暴露 leader；客户端自定义函数工具当前不支持，文档列出内置工具与远程 MCP；需使用相应 SDK / Responses 路径，不能当普通 Chat Completions 接口。这里描述的是服务端能力边界，不是它的内部调度源码，也不是本 demo 的本地模型协议。<sup><a href="#cite-7">[7]</a></sup>

面向人类组织的 AI teammate 又是另一层产品定位：共享工作台里的一位助手，未必采用后台多 Agent。学习时先问“哪个执行者、哪份状态、谁决定下一步、谁批准动作”，再比较产品。

## 术语落到代码，避免只记职位名

以下是本工程的术语口径；不同 SDK 对 run / turn 的边界可能不同。代码位于 `demos/team-agent-lab/`。

| 名词 | 准确定义与区别 | 本工程对应 |
|---|---|---|
| Agent / 智能体；Role / 角色 | 前者是有指令、输入、能力与执行状态的单元；后者描述职责，写一个职位名不自动创建执行者 | local 的模型请求单元；mock 是替身；stage 指令在 `backends.SCHEMAS` |
| Task / 子任务 | 目标、所需证据和验收合同，不等于某个角色 | planner 返回独立 `task_id`、`worker_id`、资料与 focus，`contracts.plan` 校验 |
| Run / 运行 | 一次完整任务执行，涵盖计划到终止 | `lab.run`；保存时生成 `run_id` |
| Turn / 回合；Attempt / 尝试 | 本例逻辑回合是一项模型请求；传输重试是同一逻辑 call 的新 attempt | `Context.call` 的 `call_id` 与递增 attempt，重试也占预算 |
| Orchestrator / 编排器；Supervisor / 主管 | 前者安排顺序与依赖，后者负责检查、返工与终止；可以由同一个控制器承担 | `lab.pipeline` 的代码控制面；planner 模型只提出受限计划 |
| Worker / 工作者 | 接受限定子任务，返回可检查产物，不直接拥有发布权 | implementation / validation 两个槽位，`lab.workers` |
| Delegation / 委派 | 委托子任务，调用者保留整体控制，结果返回调用者 | 本例 supervisor → worker → return |
| Handoff / 移交 | 把当前活动执行责任切换给另一个 Agent，不只是拿回一段结果 | 本例未实现；对照 SDK handoff，不能把 `gather` 当移交 |
| Message / 消息 | 带发送者、接收者和内容的信息，不自动授予权限或移交控制 | reviewer → worker 的结构化 feedback；没有自由聊天总线 |
| Routing / 路由 | 从允许目标里选择接收者或资源 | 模型选择资料与 focus，代码验证目标与资料白名单 |
| Workflow / 工作流；DAG / 有向无环图 | 描述预设的执行与依赖；动态规划另决定新任务或依赖 | 主干是固定 DAG，review 有界回边使完整流程不再是纯 DAG；不动态创建任意节点 |
| Fan-out / 扇出；Fan-in / 扇入 | 分派独立工作，再汇聚结果 | 两个 worker；parallel 用 `asyncio.gather`，sequential 顺序 await |
| Barrier / 屏障；Join / 汇合 | 到齐且满足条件后才放行依赖 | 全成功 join 后才接收 worker 产物；任一失败不进入复核 / 汇总 |
| Shared state / 共享状态；Blackboard / 黑板 | 多执行者引用的应用数据；黑板强调共同产物区和更新规则 | `artifacts` 由主管单写，带输入哈希、schema 和修订号；不自动等于模型共享记忆 |
| Mailbox / 邮箱 | 面向接收者的消息交付与保留机制 | 只有内存中的定向反馈，没有持久 mailbox 或送达保证 |
| Tool / 工具；Skill / 技能 | 工具是可执行能力接口；技能通常是任务知识、步骤与约束，不等于工具函数 | `contracts.evidence` 仅按 ID 读自带资料；未实现 Skill 加载器 |
| Checkpoint / 检查点 | 可用于恢复的持久执行状态，需要版本与重放合同 | 本例只有结束后审计快照，不能称为已实现恢复检查点 |
| Retry / 重试；Idempotency / 幂等 | 再次尝试与重复操作不增加业务副作用是两件事 | 有界只读 / 内容请求重试；不保证模型只计算一次或第三方 exactly-once |
| Termination / 终止 | 成功、失败、取消、deadline、预算停止要分开 | `lab.run` 保存原因；失败没有候选，不继续解锁下游 |
| Human approval / 人审批准 | 人对具体对象与内容授权，不是模型投票 | `lab.approve` 比对候选 SHA，才创建本地 `report.json` |
| Trace / 执行轨迹 | 可关联的调用、消息、状态和产物记录，用于诊断 | `events.jsonl` + `inputs.json` + 产物哈希；不是私有完整思维链 |

## 结构图：控制流和证据流分开看

<figure class="team-flow" aria-label="本地发布评审工作流与有界反馈">
<div class="team-flow-box"><strong>Planner 提案 → 代码合同检查</strong><p>限定两个槽位；选择资料与 focus，不能生成任意工具或角色。</p></div>
<div class="team-flow-arrow" aria-hidden="true">↓ fan-out</div>
<div class="team-flow-split"><div class="team-flow-box"><strong>Implementation worker</strong><p>实现文档 + 政策 → 引文与解释</p></div><div class="team-flow-box"><strong>Validation worker</strong><p>测试报告 + 政策 → 引文与解释</p></div></div>
<div class="team-flow-arrow" aria-hidden="true">↓ 全成功 join</div>
<div class="team-flow-box"><strong>Reviewer 对照原始证据复核</strong><p>不通过 → 发具体反馈 → 只重跑目标 worker → 再复核；有轮次和预算上限。</p></div>
<div class="team-flow-arrow" aria-hidden="true">↓ 复核通过</div>
<div class="team-flow-box"><strong>Synthesizer → 程序 grader → 候选哈希</strong><p>模型同意仍不授权发布。人核对哈希后，才产生本地 report.json。</p></div>
<figcaption>主干与能力范围由代码固定；local 模式中的计划内容、解释和反馈由模型生成。mock 模式相同位置使用规则替身。</figcaption>
</figure>

通信路径不是任务图的同义词。两个 worker 的读任务独立，适合并行；reviewer 需要两份结果和原始资料。只有主管更新共享产物，避免 worker 同时修改“最终答案”。反馈消息指出证据冲突，但消息本身不等于修订已经完成。

## 决策归属：哪些交给模型，哪些不交

| 决策 | 提案者 | 最终约束 |
|---|---|---|
| 子任务资料与 focus | mock 规则 / local planner 模型 | 恰好两个注册 worker，必须含各自最低资料范围 |
| 证据提取与解释 | worker | 只能引用实际可见证据，原文必须精确匹配 |
| 是否需要返工、返给谁 | reviewer | 注册目标、有效证据、修订上限；不能自己扩展角色 |
| 并发、join、重试和总 deadline | 代码 | 不靠提示词提醒来维持计数与依赖 |
| 最终可接受结论 | synthesizer 提案 | 固定样例 grader 验证已知门槛，不冒充通用事实判断 |
| 本地发布 | 人提交具体候选哈希 | 代码比对内容、输入版本并拒绝覆盖不同结果 |

工具权限不是 reviewer 的一段自然语言判断。planner 就算输出 `../../private` 或 `shell`，`contracts.evidence` 也不会读取该路径。reviewer 可能漏掉错误；真正的读取范围和发布门由程序限制。这个边界比“再加一个安全角色”更具体。

## Walkthrough：从 clone 到候选报告

完整源码和更细的运行说明位于[本地工程 README](../demos/team-agent-lab/README.md)，也可在 [GitHub 阅读工程](https://github.com/YuzheZhou2000/agent-fieldnotes/tree/main/demos/team-agent-lab)。

```sh
git clone https://github.com/YuzheZhou2000/agent-fieldnotes.git
cd agent-fieldnotes/demos/team-agent-lab
python3 run.py run --mode parallel
python3 -m unittest discover -s tests -v
```

无需 pip 包；可用 `python3 -m venv --without-pip .venv` 创建干净环境。脚本只访问自带的 `fixtures/packet.json` 和本目录下生成的 `runs/`，不是任意文件代理。不要在第一步就换成真实客户数据。

### 1. 计划：提出资料分配，再通过代码检查

`lab.pipeline` 向 plan stage 发送目标和允许文档 ID；planner 不先看到全部文档正文，也看不到程序内部的最终 grader。返回的两项任务具有不同 `task_id`，分配给 implementation / validation。代码检查槽位、ID 唯一性、focus 长度和必需来源，再接受 plan 产物。

mock 分配实现与政策给 implementation，测试与政策给 validation。local 可以补充第三份允许资料或改变 focus，但不能越出白名单。这个限制让计划可检查，也限制了自主性：本例不是模型随意创建整个任务 DAG。

### 2. 工作者：实际输入要能展示

`lab.workers` 通过 `contracts.evidence` 读取批准范围内的材料，将精确证据行和子任务交给 worker。模型返回 `assessment` 和带 `evidence_id / quote / note` 的 finding；程序检查引用属于实际输入、引文逐字一致、没有重复或超限。

`quote` 匹配只能证明引用存在，不能证明 `note` 的推论正确。对语义的复核在下一层；固定样例 grader 还有最后一道已知门槛检查。不要把 schema 校验包装成普遍的事实验证。

每轮 `inputs.json` 保存实际 payload。主管的完整 Python `Context` 不会自动传给任何模型；worker 看不到另一位 worker 的所有隐含状态。需要共享的证据，必须在下次输入或反馈里显式提供。

### 3. Join：worker 完成不等于任务完成

parallel 同时创建两项 asyncio task，并等待 `gather`。只有两份结果都成功且合同有效，主管才接受 worker 产物并解锁 reviewer。任一失败时取消其余等待、收齐取消结果，不把半份材料悄悄当作完整交付。这里的“并行”是 I/O 请求可以重叠，不是声称 Python 同时执行 CPU 推理。

sequential 使用同样的角色与合同，只把 worker 改为逐个 await。这样可以把调度差异与角色提示的差异分开，不用两个完全不同的系统做速度对照。

### 4. 复核与综合：先检查矛盾，再交候选

reviewer 获得 worker 产物和原始证据，返回批准或有明确 worker 目标、问题和证据 ID 的反馈。主管可以重跑受影响 worker，但默认最多一轮修订，之后必须再次复核。通过后才调用 synthesizer；还要经过独立的程序 grader，才写出候选。

正常 mock 路径为 5 次调用：plan + 两个 worker + review + synthesize。它输出已知的 `shadow_only` 结论，`validated: true` 只表示符合这个人工样例。default mock 没有任何模型能力测量。

### 5. 人审：批准一个具体哈希

运行正常结束时状态为 `awaiting_approval`，不是已发布。输出给出 `run_id` 和 `candidate_sha256`。先查看 `runs/<run_id>/candidate.json`、输入及轨迹，再把本轮实际值填入：

```sh
python3 run.py approve RUN_ID --hash CANDIDATE_SHA256
```

只有这一步才创建本地 `report.json`；不联网，不部署。相同哈希重复批准是幂等的，不会重复覆盖；候选被改动或输入版本不匹配则拒绝。本地 CLI 用户仍能直接修改自己文件，因此这是教学授权边界，不是防恶意本机用户的安全服务。

## 日志实验：让一份结论与它自己的证据冲突

```sh
python3 run.py run --fault conflict
```

这不是简单拼接两份摘要。mock 首次让 validation 报 `ready`，但它引用的 `T2` 明确说恢复测试没有做，`P1` 要求这项门槛。reviewer 因此返回具体反馈；主管只重跑 validation，再次检查，再汇总。一次已执行的该场景产生 **7** 次调用。

可从实际 `events.jsonl` 按 event 筛出下面的关键顺序；省略本机计时、ID 后缀和哈希：

```text
artifact_accepted  plan
call_started       implementation / attempt 1
call_started       validation / attempt 1
join_passed        implementation, validation
artifact_accepted  review / approved=false
revision_requested validation
message_delivered  reviewer → validation / evidence T2, P1
artifact_accepted  validation / revision 2
join_passed        validation
artifact_accepted  review / approved=true
artifact_accepted  candidate
run_ended          awaiting_approval
```

这是便于阅读的事件摘记，`approved` 需在 `artifacts.json` 对应产物查看，不是每条 event 的直接字段。对照 `inputs.json`：第一次 validation 的 feedback 为空，第二次包含 reviewer 的具体消息；它不是偷偷获得了共享内存。回边改变的是该 worker 的一次新逻辑调用，传输层重试则仍属于同一 call ID。

真实模型可能看不出矛盾，也可能修订出新的错误；不能把 mock 在此处按规则修好，写成“模型团队已验证可自我纠错”。Anthropic 2026-08-13 的多 Agent 风险研究也讨论局部行为如何叠加成系统性问题；这进一步要求保留原始证据与独立门槛，而不是把同伴赞同当真理。<sup><a href="#cite-9">[9]</a></sup>

## 对照实验：单 Agent、顺序团队与并行团队

```sh
python3 run.py run --mode compare --max-calls 8 --latency-ms 40
python3 run.py run --mode single --single-turns 1
```

`single` 默认是一位 generalist 连续 5 轮读取全部证据及前一候选，最后执行相同 grader；不是只让单 Agent 草草答一次。额外的 1-turn 命令提供最小基线。顺序与并行团队使用相同五阶段合同，仅 worker 调度不同。

仓库[模拟记录](../demos/team-agent-lab/examples/verified-mock-summary.json)保存了一次本机实际运行。三组默认都生成相同候选、各预留 5 次调用，最高在途调用数为 **1 / 1 / 2**。每次人为加入 40ms sleep，因此并行路径可能更短；这只验证调度与关键路径，不是模型速度 benchmark，也没有 token / 费用测量。

公平比较至少要列出：输入、工具、总尝试上限、每次输出上限、实际用量、验收器和允许修订次数。相同调用次数仍不等于相同 tokens、FLOPs 或费用；generalist 多轮重复原文，团队又有计划和消息开销。若真实本地模型一次只能处理一个请求，客户端并发也可能只换来服务端排队。

Anthropic 的 2025-06-13 工程文章描述 orchestrator–worker 研究系统以及并行压缩信息的作用，但其收益与成本属于当时系统和任务。本文不借用发布稿中的提升数字给 demo 背书。团队只有在任务可拆、独立证据可并行获取、交接损耗可控且验收可靠时，才有值得测量的机会；小而依赖紧密的任务可能由单 Agent 更省。<sup><a href="#cite-8">[8]</a></sup>

## 故障与边界：让控制器证明它真的会停

| 练习命令后缀 | 观察什么 | 预期边界 |
|---|---|---|
| `--fault transient` | 同 call ID 的新 attempt，总尝试通常为 6 | 只读 / 内容请求可重试，仍占预算 |
| `--fault timeout --timeout 0.05` | 超时取消等待后有限重试 | 不证明真实服务端停止计算 |
| `--fault transient --retries 0` | worker 失败 | 不解锁 reviewer / synthesizer |
| `--fault malformed` | schema 或引用校验失败 | 不把结构错误无界重试成成功 |
| `--fault conflict --max-revisions 0` | 复核指出冲突但没有返工额度 | 没有候选，保留失败原因 |
| `--fault review_reject` | 默认修订一次后仍拒绝 | 有界结束，不循环到“模型同意”为止 |
| `--max-calls 4` | 下一次派发前预算不足 | 不能先调用再补记超支 |
| `--cancel-after-ms 60 --latency-ms 40` | 两位 worker 在途时请求取消 | 停止后续派发并等待子任务退出，不生成候选 |
| `--deadline 0.02 --latency-ms 40` | 总运行期限届满 | 与成功、复核拒绝、取消分开记录 |

每条后缀接在 `python3 run.py run` 后。故障注入仅限 mock；它们验证本地控制逻辑，不验证真实模型或外部副作用。模型调用预算包括重试和取消的已派发尝试；没有返回 usage 的消耗保持未知。

本例只读与生成内容的重试不能照搬到发邮件、付款或修改生产数据库。模型生成可能被重复执行，业务写入还需要端到端幂等与结果核对。进一步读[执行循环](agent-loop.html)和[服务化、运行账本与故障处置](agent-operations.html)。

## 可选接入本地模型：真实驱动，但不隐式放权

先由你自行启动支持非流式 JSON Chat Completions 的本地模型服务，再运行：

```sh
python3 run.py run --backend local \
  --base-url http://127.0.0.1:8000/v1 \
  --model YOUR_LOCAL_MODEL \
  --mode parallel --timeout 30 --deadline 120 \
  --max-calls 8 --max-output-tokens 1024
```

模型名需替换为该服务已存在的名称。本工程不下载模型、不设置持久密钥、不读取 API key，也不发送远程 tracing。只允许带端口的 HTTP loopback，拒绝远程地址、URL 凭据和重定向，忽略环境代理。回环连接不自动证明服务内部使用本地推理，应自行确认不是云代理。

适配器请求包含 `response_format: {"type":"json_object"}`。本地服务或模型不支持时应失败；输出截断、非法 JSON、越界资料或引用不匹配也会失败。不会用 mock 结果掩盖真实模型错误。每个模型输出会实际影响后续资料、解释、反馈或候选，仍受到代码权限和合同约束。

客户端超时会关闭等待与连接，但不承诺服务端停止生成；真实模型应另测服务端队列、取消、显存与吞吐。此处不接入三家付费 API，也不把本地协议兼容性等同于它们的托管团队功能。

## 已验证与未验证的范围

本工程于 2026-10-21 完成 mock 端到端和 16 项 Python 测试，覆盖正常路径、并发重叠、定向修订、无效输入、预算、超时、取消、引用和哈希批准。回环 HTTP stub 还检查了实际 plan / 内容输出传递、用量字段、分块响应、重定向拒绝和响应大小限制；**stub 不是模型**。

没有启动真实本地 LLM，没有执行 Claude Teams、OpenAI Agents SDK 或 xAI 多 Agent 请求，没有付费调用，也没有复跑论文或生产性能测试。真实模型能否正确理解、分工与修订仍未验证。程序 grader 只认识这个小样例，不能保证所有自然语言解释真实。

工程没有持久 mailbox、自由同伴协商、跨进程隔离、生产队列或自动 checkpoint 恢复。结束后保存的审计文件不是崩溃恢复实现。以后扩展这些能力，先定义版本、消息、状态和验收合同，再增加框架，而不是先堆角色。

## 下一步怎样继续学

先让自己能解释一条 trace 的每次派发和输入，再替换一项机制做对照：改变资料分配，加入冲突证据，限制修订，或者让同一 generalist 使用不同回合预算。每次只改变一项，并记录实际用量和失败，不把模拟加速当团队质量结论。

随后把同一个小任务移植到 SDK 的 agents-as-tools 或受控图框架，检查控制权、应用 context 和取消语义是否仍符合原合同。需要学习真正的 handoff 时另设“活动 Agent 切换”任务，别用改一个类名冒充移交。全站路线见[学习地图](../learn.html#collaboration)。

<footer><div class="sources">
<h2 id="sources">来源与证据说明</h2>
<ol>
<li id="cite-1"><a href="https://www.anthropic.com/research/building-effective-agents">Anthropic · Building effective agents</a><span class="source-meta">2024-12-19 发布 · 2026-10-21 复核 workflow / agent 的控制流区别；属于基础工程材料，未将其称作当日新研究</span></li>
<li id="cite-2"><a href="https://code.claude.com/docs/en/agent-teams">Claude Code · Agent Teams</a><span class="source-meta">滚动官方文档，无独立发布日期 · 2026-10-21 核查实验开关、独立实例、Task tools、消息、交互模式与计划批准条件；另查当日 v2.1.306 发行记录，文档语义不冒充对该二进制的实测</span></li>
<li id="cite-3"><a href="https://code.claude.com/docs/en/sub-agents">Claude Code · Subagents</a><span class="source-meta">滚动官方文档，无独立发布日期 · 2026-10-21 核查具名通信、SendMessage、显式输入和恢复说明 · 未启动产品会话</span></li>
<li id="cite-4"><a href="https://github.com/openai/openai-agents-python/blob/64cd5dfc5a1579870dcbed0ea42b27aa84033fee/docs/multi_agent.md">OpenAI Agents SDK · Agent orchestration 固定快照</a><span class="source-meta">主线快照 64cd5dfc，2026-10-19 · 2026-10-21 阅读代码 / LLM 编排、as_tool 和 handoff，并读取同快照 <a href="https://github.com/openai/openai-agents-python/blob/64cd5dfc5a1579870dcbed0ea42b27aa84033fee/docs/handoffs.md">handoffs</a>、<a href="https://github.com/openai/openai-agents-python/blob/64cd5dfc5a1579870dcbed0ea42b27aa84033fee/docs/context.md">context</a> · 未执行 SDK</span></li>
<li id="cite-5"><a href="https://openai.github.io/openai-agents-python/models/#hosted-multi-agent-experimental">OpenAI Agents SDK · Hosted multi-agent</a><span class="source-meta">滚动官方文档，无独立发布日期 · 2026-10-21 阅读服务端编排、客户端工具及拒绝 SDK handoffs 的实验边界 · 未调用 beta</span></li>
<li id="cite-6"><a href="https://github.com/openai/openai-agents-python/releases/tag/v0.24.0">OpenAI Agents Python · v0.24.0</a><span class="source-meta">2026-10-15 02:20:12 UTC 发布，发行目标 17d994bd3045dae71acda676a4ef4762ed8ecd94 · 2026-10-21 核查最新稳定发行；与主线文档快照分开，不是本 demo 的依赖</span></li>
<li id="cite-7"><a href="https://docs.x.ai/developers/model-capabilities/text/multi-agent">xAI · Multi Agent</a><span class="source-meta">页面标注 2026-10-10 更新 · 2026-10-21 阅读 4 / 16 配置、leader 输出、自定义客户端工具限制及 Responses 路径 · 未访问内部实现或调用模型</span></li>
<li id="cite-8"><a href="https://www.anthropic.com/research/multi-agent-research-system">Anthropic · How we built our multi-agent research system</a><span class="source-meta">2025-06-13 发布 · 2026-10-21 阅读 orchestrator–worker、并行压缩与评测工程范围 · 不外推厂商收益数字，未复跑</span></li>
<li id="cite-9"><a href="https://www.anthropic.com/research/multiagent-systems">Anthropic · Patterns and problems in emerging multiagent systems</a><span class="source-meta">2026-08-13 发布 · 2026-10-21 阅读开篇、协调及系统性失败的讨论范围 · 研究案例，非本地 demo 的模型测试</span></li>
</ol>
</div></footer>
