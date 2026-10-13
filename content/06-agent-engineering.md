---
{
  "slug": "agent-engineering",
  "title": "Agent 系统设计：八个问题与可验证研究路径",
  "topic": "评测与交付",
  "summary": "用状态、工具、记忆、权限与验收约束组织系统设计，选择最小可证伪实验，再逐项增加复杂度。",
  "order": 6,
  "updated": "2026-10-13",
  "tags": ["系统设计", "RLM", "LangGraph", "实验方法"],
  "minutes": 22
}
---

## 从失败模式选择研究方向

专业系统设计从可观察失败出发：任务为什么停了、约束在哪里丢了、工具为什么选错、副作用是否重复、验收有没有测到真实目标。下面八个方向是设计清单；厂商与框架只作为实现材料，不作为分类轴。

| 观察到的失败 | 优先研究的问题 | 必须保存的证据 | 深入笔记 |
|---|---|---|---|
| 工具迟到、取消后仍执行 | 运行时与调度 | call ID、时间线、最终状态 | [运行时合同](openai.html) |
| 重启后丢目标或重复行动 | 持久状态与恢复 | 事件位置、工作区版本、幂等记录 | [长任务状态](claude.html) |
| 记忆存在却没有被使用 | 记忆策略与上下文 | 写—读—用链、初始化池、任务顺序 | [记忆进入策略层](agent-memory.html) |
| 能力漏发现、跨服务不一致 | 工具与协议 | schema、权限、关联 ID、产物版本 | [工具系统](gemini.html) |
| 外部内容改变了授权目标 | 权限与安全 | 来源传播、动作范围、实际影响 | [行动边界](muse.html) |
| 分数上升但交付不稳定 | 评测与交付 | trial、grader、资源和完整费用 | [长任务评测](agent-evaluation.html) |

## 复杂度应该购买什么收益

以下是工程判断框架，未跑对照实验：先固定模型、预算、任务与 grader，建立串行基线；一次只改变一个主要机制。增加子 Agent 应减少真实关键路径或提高覆盖，增加记忆应减少跨上下文错误，增加代码式调用应降低中间结果负担。若只有 token、工具次数或局部评分变好，仍需核查最终 outcome。

把成本写成完整轨迹账本：推理与缓存、工具、环境空闲、重试、子任务和存储。比较每成功任务费用，同时保留失败花费。对在线记忆固定任务顺序与初始快照，另测乱序；对服务化运行时加入超时与恢复；对 grader 抽样人工核查分歧。指标和样本量随目标选择，不能用一套平均分概括所有任务。

## 从产品名单转向工程问题

以下公开实现材料呈现共同方向：Agent 持续工作、拥有执行环境、按需使用大量工具、携带长期状态，并向用户交付可验证产物。OpenAI Agents API、Anthropic Managed Agents 与 Gemini 工作 Agent 从不同侧面披露了这些能力，Muse 则突出个人身份与受控外部行动。<sup><a href="#cite-1">[1]</a></sup><sup><a href="#cite-2">[2]</a></sup><sup><a href="#cite-3">[3]</a></sup><sup><a href="#cite-4">[4]</a></sup>

这是跨厂商材料支持的工程趋势；不能据此断定各家采用相同架构，也不构成产品排名。真正有学习价值的主线是八个问题：循环、状态、上下文、工具、协作、权限、成本和评测。

## 八个值得深入的方向

### 1. Agent loop 与任务生命周期

基本循环包含组装上下文、模型推理、解析工具请求、执行、记录结果，再决定继续或结束。Codex 与 Gemini CLI 提供可阅读实现，SDK 提供更高层接口。观察 streaming 时，应分清文本已输出、工具已开始、工具结果已记录与任务已验证。<sup><a href="#cite-1">[1]</a></sup><sup><a href="#cite-5">[5]</a></sup>

下面是学习用交互示意，点击状态查看职责，**不是某一家产品的内部状态机**。真实任务可以多次进入运行、等待审批或恢复阶段。

<div class="lifecycle" role="group" aria-label="学习用 Agent 任务生命周期">
<button type="button" data-state="accepted" aria-pressed="true">Accepted →</button>
<button type="button" data-state="running" aria-pressed="false">Running →</button>
<button type="button" data-state="approval" aria-pressed="false">Awaiting approval →</button>
<button type="button" data-state="recovering" aria-pressed="false">Recovering →</button>
<button type="button" data-state="verified" aria-pressed="false">Verified</button>
<div class="lifecycle-output" aria-live="polite">Accepted：记录目标、授权范围和幂等键。任务状态持久化，页面关闭不应导致任务消失。</div>
</div>

### 2. Durable execution 与恢复

Anthropic 的持久 Session 在 Harness 外保存事件，LangGraph 用 checkpointer / thread id 保存工作流进度。二者都提供恢复能力，但恢复并不总是从相同代码行继续。当前 Checkpointers 文档说明，重放跳过检查点之前的节点，重新执行之后的节点，包括 LLM 与 API 调用。<sup><a href="#cite-2">[2]</a></sup><sup><a href="#cite-6">[6]</a></sup>

因此，应把副作用包装成可记录的任务，并使用幂等键或外部状态查询。执行成功却没持久化结果是典型的不确定区间。**检查点能记住系统知道的状态，不能自动知道外部世界已发生但尚未被记录的行动。**

LangGraph 文档还区分 `exit`、`async`、`sync` durability；性能和中途崩溃的恢复强度不同。内存 checkpointer 适合入门，但不能据此声称进程重启后的持久恢复已完成。<sup><a href="#cite-6">[6]</a></sup>

### 3. Context engineering 与 RLM

上下文要区分原始事件、当前工作集、摘要、长期记忆和产物引用。官方 context engineering 博客提出 compaction、structured notes 与 JIT retrieval；Managed Agents 则让压缩后的视图与可回查事件日志分别存在。<sup><a href="#cite-2">[2]</a></sup><sup><a href="#cite-7">[7]</a></sup>

**Recursive Language Models（RLM）** 提供一个值得阅读的研究方向：将大输入作为外部环境中的变量，让模型用代码检查、拆分，并对子片段递归调用模型。原论文首次提交于 2025-12-31，v3 更新于 2026-05-11；本次读取了摘要与作者仓库，没有重新运行实验。<sup><a href="#cite-8">[8]</a></sup><sup><a href="#cite-9">[9]</a></sup>

RLM 与 RAG、compaction、PTC 的区别在于切入点：

| 方法 | 主要处理什么 | 结果进入模型的方式 |
|---|---|---|
| RAG / JIT retrieval | 外部知识选择 | 返回相关摘录和引用 |
| Compaction | 历史太长 | 返回摘要，省略部分细节 |
| PTC / Code Mode | 大量工具中间结果 | 代码处理后只返回需要的结果 |
| RLM | 输入作为可查询对象 | 模型用程序拆分、检查与子调用 |

作者仓库要求 Python 3.11+，默认 local REPL 与宿主进程共享环境；学习不可信输入时应选择明确隔离的环境。框架有 sandbox 选项并不意味着任意默认配置都拥有生产隔离保证。<sup><a href="#cite-9">[9]</a></sup>

### 4. 工具发现与 Programmatic Tool Calling

Tool search 降低工具定义预加载，PTC / Code Mode 降低中间结果进入模型的量。Anthropic、OpenAI 与 Cloudflare 都有公开材料。MCP 仍负责统一连接和 schema，代码执行方式改变的是 Agent 怎样组织调用。<sup><a href="#cite-1">[1]</a></sup><sup><a href="#cite-10">[10]</a></sup><sup><a href="#cite-11">[11]</a></sup>

Cloudflare 的公开博客使用 TypeScript API 和 V8 isolate，把普通出网能力与指定 bindings 分开。这个机制适合小段受控代码；完整浏览器、Shell 和开发工作区则可能需要不同执行环境。材料中的“更好”要按工作负载判断。

学习 PTC 时，至少记录四个边界：可发现工具、可执行工具、生成代码的资源限制、可返回模型的数据。工具 schema 只约束参数结构，不保证业务权限或副作用语义正确。

### 5. MCP、Skills 与 A2A

三者分别解决不同问题：MCP 连接外部工具和数据；Skills 保存可复用指令、脚本和知识；A2A 让具有独立内部实现的 Agent 应用发现与协作。Google 工作 Agent、ADK 与 Claude 的文档都体现能力模块化，但具体 API 与权限模型并不统一。<sup><a href="#cite-3">[3]</a></sup><sup><a href="#cite-12">[12]</a></sup><sup><a href="#cite-13">[13]</a></sup>

| 机制 | 合适问题 | 不能代替什么 |
|---|---|---|
| MCP | 如何统一发现 / 调用工具与资源 | 业务授权、幂等与最终状态校验 |
| Skills | 如何复用成功的工作方法 | 执行环境、版本管理与质量评估 |
| A2A | 如何与另一个 Agent 服务协作 | 内部状态共享与跨服务事务 |

MCP 规范仓库在本次 README 指向 `2026-07-28` schema。应选定协议版本阅读，尤其扩展 proposal 与正式规范不能混为已经上线的标准。<sup><a href="#cite-12">[12]</a></sup>

### 6. 多 Agent 的上下文与写入控制

Anthropic 研究系统把子 Agent 当独立检索与压缩单元；Cognition 的实践强调单写者周围的 review 与能力咨询。它们适合不同任务：广泛研究有很多独立子问题，代码修改有更多共享决策和依赖。<sup><a href="#cite-14">[14]</a></sup><sup><a href="#cite-15">[15]</a></sup>

完整的拓扑、交接合同、调度与基线比较见 [Agent Teams 深度专题](agent-teams.html)。每个子任务应有目标、证据输入、权限、输出格式和停止条件。主 Agent 需要能处理迟到结果、父任务取消、重复探索和不一致事实。更多 Agent 不是质量保证；要测量并发减少了多少真实时间，又增加了多少费用和协调错误。

### 7. 权限、隔离与凭据

官方 containment 材料区分模型行为、执行环境与外部内容。Muse 披露 Sentinel 出网审核，Claude 披露 OS sandbox 与 VM 路径；开源 Sandbox Runtime 可以阅读实际文件系统与网络策略。<sup><a href="#cite-4">[4]</a></sup><sup><a href="#cite-16">[16]</a></sup><sup><a href="#cite-17">[17]</a></sup>

不要将“网络默认拒绝”理解成“文件读取也默认拒绝”。本次 Sandbox Runtime README 明确默认 reads 可见范围较广，写入与网络采用不同默认规则。阅读策略优先级与平台差异，常常比复制一个配置示例更重要。<sup><a href="#cite-17">[17]</a></sup>

权限也属于产品体验。频繁确认可能增加打断，完全不看重要动作则会产生误操作。值得学习的方向是事先定义范围、生成可审查动作、结构性限制能力，并让用户在真正需要决策的位置参与。

### 8. 成本、排队与评测

官方 Cursor 缓存优化、Claude 缓存定价更新与 OpenAI 模型价格都说明，成本应按完整任务轨迹计算。至少分别记录 uncached input、cached input、output、工具次数、重试、子 Agent、execution idle time 与每成功任务费用。<sup><a href="#cite-18">[18]</a></sup><sup><a href="#cite-19">[19]</a></sup>

对于排队与配额学习，可在同一模型 / effort / 工具集下比较时延与 outcome。将用户限额、模型全局配额、执行 worker 容量分开建模；并发更多可能减少排队，也可能放大限流、缓存冷启动与成本。这是工程练习建议，不是本篇已经测得的结论。

评测同时看最终产物、环境状态、行为边界与用户路径。任务成功不能只由最后一句回答判断；代码生成还应看范围、回归、安全和测试有效性。<sup><a href="#cite-20">[20]</a></sup><sup><a href="#cite-21">[21]</a></sup>

## 四周学习计划

这是可自行调整的学习安排，不是已创建的定时任务。每周产物应保存真实运行记录，不编造结果。

| 阶段 | 资料与任务 | 本周产物 | 验收条件 |
|---|---|---|---|
| 第一周：循环 | OpenAI / Gemini 源码；一个 SDK quickstart | 最小只读 Agent 与事件轨迹 | 工具成功 / 失败 / 取消均可辨认 |
| 第二周：长任务 | Managed Agents、LangGraph durable execution、context engineering | 可重启任务、handoff 与检查点 | 原约束保留，已完成动作不重复 |
| 第三周：工具与协作 | MCP / A2A、PTC、单写者 review | 工具目录与协作任务 | 引用完整，权限限制生效 |
| 第四周：质量与成本 | Cursor 缓存、Agent eval、Devin verification | 真实 task suite 与费用表 | outcome 可验证，失败原因可解释 |

## 推荐学习项目

一个“公开技术资料研究 Agent”可以串联这些问题：

1. 用户指定一个主题与资料截止日。
2. Agent 搜索官方发布、文档、源码与论文，记录日期与 URL。
3. 大量原文保存在外部文件中，上下文只保留关键摘录与引用。
4. 独立验证阶段检查结论和来源是否一致。
5. 主执行者写入 Markdown，生成静态文章。
6. 重启后从目标、事件与已完成产物恢复。
7. 返回引用完整性、失败工具、未核实项与真实费用。

这是一个特别适合基础设施工程师的题目，因为结果质量能直接通过引用和产物检查，同时暴露上下文、工具、长期状态与缓存问题。建议先做串行基线，再加子 Agent、PTC 或 RLM，避免同时改动过多变量。

## 开源实现与课程地图

| 方向 | 起点 | 应追踪的核心概念 |
|---|---|---|
| Coding Harness | Codex / Gemini CLI | turn、tool router、scheduler、compaction |
| 通用运行时 | OpenAI Agents SDK / Claude Agent SDK / ADK | session、工具执行、hooks、handoff |
| 状态编排 | LangGraph + 官方 durable execution | checkpoint、thread、replay、side effect |
| 工具连接 | MCP 官方规范与 SDK | capabilities、tools、resources、auth |
| 跨 Agent | A2A 官方仓库与 DeepLearning.AI 课程入口 | Agent Card、task、artifact、stream |
| 外部上下文 | RLM 论文 / 作者仓库 / minimal 实现 | REPL、subcall、递归预算 |
| Code Mode | Cloudflare Agents 与 Anthropic 工程博客 | typed API、隔离、结果过滤 |
| 隔离 | Anthropic Sandbox Runtime | filesystem、network、proxy、平台差异 |
| 验收 | Anthropic evals / Devin verification / FrontierCode | outcome、rubric、test quality、scope |

想从课程而非长博客开始，可读 A2A 仓库中链接的课程、Gemini CLI README 中的 DeepLearning.AI 课程，以及 LangGraph README 中的 LangChain Academy。课程入口来自官方仓库，本次未逐节观看，不声称已验证全套课程内容。<sup><a href="#cite-5">[5]</a></sup><sup><a href="#cite-13">[13]</a></sup><sup><a href="#cite-22">[22]</a></sup>

## 后续如何持续研究

每次新发布，先查模型是否可用、API 哪些变化，再判断 Harness 的旧假设是否仍有必要。每篇新笔记至少回答一个具体问题：该能力解决哪个失败、公开到哪一层、可以怎样小规模验证。

GitHub 项目发现可用组合查询，例如 `agent in:readme language:python stars:>=100 pushed:>2026-09-01`；这是后续检索模板，不是本篇已执行后取得的仓库排名。更可靠的直接学习入口仍是官方材料中的原始实现与固定源码快照。

维护时保存“发布日期、访问日、原始 URL、读取状态、代码 commit、结论、局限”。发布状态更新与旧文章更正都应留下更新记录。未经验证的数值保持缺失，失败材料保留原因，而不以猜测补齐。

## 更新记录与证据边界

- 2026-10-13：改为技术问题索引，补充失败→研究方向→证据映射，以及复杂度增量实验；保留既有八个方向和四周项目。

- 2026-10-13：创建八个工程方向、四周学习计划与资料地图。
- RLM 阅读范围为论文摘要和作者仓库；没有审查论文全部实验，也没有训练或跑分。
- Code Mode、LangGraph 与 Sandbox 阅读的是官方文档和 README，未部署生产实例。
- 本篇综合各方向资料并提出学习实验，不代表已经建立常驻研究服务或自动订阅。

<footer><div class="sources">
<h2 id="sources">来源与证据说明</h2>
<ol>
<li id="cite-1"><a href="https://openai.com/index/introducing-the-agents-api/">OpenAI · Introducing the Agents API</a><span class="source-meta">2026-09-10 · 官方全文已读取</span></li>
<li id="cite-2"><a href="https://www.anthropic.com/engineering/managed-agents">Anthropic · Scaling Managed Agents</a><span class="source-meta">2026-04-08 · 官方工程全文已读取</span></li>
<li id="cite-3"><a href="https://cloud.google.com/blog/products/ai-machine-learning/welcome-to-gemini-at-work-2026">Google Cloud · Gemini at Work 2026</a><span class="source-meta">2026-10-08 · 官方架构披露已读取</span></li>
<li id="cite-4"><a href="https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/">Meta · Introducing Muse</a><span class="source-meta">2026-09-08 · 官方产品披露已读取</span></li>
<li id="cite-5"><a href="https://github.com/google-gemini/gemini-cli">Gemini CLI · README、代码与课程入口</a><span class="source-meta">2026-10-13 读取 · 源码快照在 Gemini 篇 · 课程未逐节观看</span></li>
<li id="cite-6"><a href="https://docs.langchain.com/oss/python/langgraph/checkpointers">LangGraph · Checkpointers</a><span class="source-meta">滚动官方文档 · 2026-10-13 核查 · 原 durable-execution 入口已重定向；现文档保留重放与 durability 说明</span></li>
<li id="cite-7"><a href="https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents">Anthropic · Effective context engineering</a><span class="source-meta">2025-09-29 · 基础材料，已读取</span></li>
<li id="cite-8"><a href="https://arxiv.org/abs/2512.24601">Zhang, Kraska, Khattab · Recursive Language Models</a><span class="source-meta">2025-12-31 首次提交，v3 2026-05-11 · 读取摘要与版本信息，未独立复测</span></li>
<li id="cite-9"><a href="https://github.com/alexzhang13/rlm">RLM · 作者维护的实现与 minimal / 教程入口</a><span class="source-meta">2026-10-13 README 已读取 · Python 3.11+ · 默认 local 执行环境需理解</span></li>
<li id="cite-10"><a href="https://www.anthropic.com/engineering/code-execution-with-mcp">Anthropic · Code execution with MCP</a><span class="source-meta">2025-11-04 · 官方工程教程已读取</span></li>
<li id="cite-11"><a href="https://blog.cloudflare.com/code-mode/">Cloudflare · Code Mode</a><span class="source-meta">2025 基础工程材料 · 2026-10-13 正文已读取 · 未核实当前生产开放状态</span></li>
<li id="cite-12"><a href="https://github.com/modelcontextprotocol/modelcontextprotocol">MCP · 官方规范仓库</a><span class="source-meta">2026-10-13 README 已读取，指向 2026-07-28 schema · 未逐条审查规范</span></li>
<li id="cite-13"><a href="https://github.com/a2aproject/A2A">A2A · 官方协议、SDK 与课程入口</a><span class="source-meta">2026-10-13 README 已读取 · 课程未逐节观看</span></li>
<li id="cite-14"><a href="https://www.anthropic.com/engineering/multi-agent-research-system">Anthropic · How we built our multi-agent research system</a><span class="source-meta">2025-06-13 · 官方生产经验已读取 · 历史结果不作最新排名</span></li>
<li id="cite-15"><a href="https://cognition.ai/blog/multi-agents-working">Cognition · Multi-Agents: What's Actually Working</a><span class="source-meta">2026-04-22 · 官方正反实践全文已读取</span></li>
<li id="cite-16"><a href="https://www.anthropic.com/engineering/how-we-contain-claude">Anthropic · How we contain Claude across products</a><span class="source-meta">2026-05-25 · 官方隔离经验已读取</span></li>
<li id="cite-17"><a href="https://github.com/anthropic-experimental/sandbox-runtime">Anthropic Sandbox Runtime</a><span class="source-meta">2026-10-13 README 已读取 · Preview，配置与平台行为持续演化</span></li>
<li id="cite-18"><a href="https://cursor.com/blog/improved-token-efficiency">Cursor · Improved token efficiency for longer agent runs</a><span class="source-meta">2026-09-23 · 官方工程全文已读取</span></li>
<li id="cite-19"><a href="https://www.anthropic.com/claude-haiku-5-5">Anthropic · Claude Haiku 5.5 与缓存价格更新</a><span class="source-meta">2026-10-07 · 官方全文已读取 · 不外推所有任务收益</span></li>
<li id="cite-20"><a href="https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents">Anthropic · Demystifying evals for AI agents</a><span class="source-meta">2026-01-09 · 官方评测方法已读取</span></li>
<li id="cite-21"><a href="https://cognition.ai/blog/frontier-code">Cognition · Introducing FrontierCode</a><span class="source-meta">2026-06-08 · 原始评测方法已读取</span></li>
<li id="cite-22"><a href="https://github.com/langchain-ai/langgraph">LangGraph · 官方实现与 Academy 入口</a><span class="source-meta">2026-10-13 README 已读取 · 未运行完整框架</span></li>
</ol>
</div></footer>
