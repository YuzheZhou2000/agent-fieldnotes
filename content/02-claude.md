---
{
  "slug": "claude",
  "title": "长任务状态：事件日志、压缩与崩溃恢复",
  "topic": "运行时与状态",
  "summary": "区分权威事件、模型工作集与产物状态，定位外部副作用的不确定区间，设计恢复与压缩验证。",
  "order": 2,
  "updated": "2026-10-15",
  "tags": ["事件日志", "恢复", "Compaction", "Anthropic"],
  "minutes": 21
}
---

## 三种状态需要分别维护

Managed Agents 将 Session、Harness 和 Sandbox 分离，Session 保存 append-only 事件，Harness 组装模型上下文。这个机制说明恢复日志与当前 prompt 可以有不同生命周期；并不保证任何外部行动都具有 exactly-once 语义。<sup><a href="#cite-5">[5]</a></sup>

下面为工程状态模型，未作为 SDK 示例运行：

| 状态 | 权威范围 | 压缩或丢失后的处理 |
|---|---|---|
| 原始事件日志 | 用户目标修正、工具意图、观察、授权 | 回查带序号原事件，不能依赖摘要重建授权 |
| 模型工作集 | 当前推理需要的摘录、摘要、文件引用 | 可重新组装；检验关键约束和证据能否恢复 |
| 产物与外部世界 | 工作区、提交、数据库变更 | 查询真实版本；日志中的成功记录要与状态对齐 |

## 最危险的恢复点在副作用之后

**工程推导**：工具已执行，但结果尚未写入日志时，系统只能知道“发出了请求”。重放整段过程可能重复提交或重复创建资源。对支持幂等的服务使用稳定操作键；对可查询的结果先查状态；两者都缺失时，将行动标为 unknown 并进入可审查的恢复步骤。

恢复测试至少覆盖发送前、发送后未确认、确认后未落盘、落盘后未呈现四个位置。环境重新 provision 也不能假设文件自动存在，应绑定产物快照与事件位置。该建议不声称某 SDK 已提供所有事务保证。

## 压缩应测保真度与决策影响

摘要 token 更少可能节约成本，也可能遗失否定约束、失败原因或用户最新纠正。应记录摘要引用的事件区间，允许回查证据，并在固定剩余预算下比较压缩前后行动。一次问答正确只能测恢复了某个事实，还要检查是否重复失败尝试、沿用旧目标或把未经验证的推测写成结论。

适用条件是存在可追溯日志、可查询产物和明确操作键。短暂只读问答可从简单会话开始，跨进程长任务应验证持久存储与故障恢复。新的记忆策略另见[文件记忆与异构路由](agent-memory.html)；下面用 Anthropic 的公开机制与产品快照继续分析具体实现。

## OpenTelemetry：诊断轨迹与权威状态分开

Anthropic 于 **2026-10-14** 宣布 Claude Platform 的 OpenTelemetry traces 进入 public beta，覆盖 Messages API、Managed Agents 与 Claude Client SDK。以下为 **2026-10-15** 的文档核查，未配置 exporter 或运行模型请求；不能把这项能力混作 Claude Code / Agent SDK 各自的监控接口。<sup><a href="#cite-13">[13]</a></sup><sup><a href="#cite-14">[14]</a></sup>

| 轨迹来源 | 主要观察范围 | 集成边界 |
|---|---|---|
| SDK spans | 客户端请求、tool runner 执行的工具 | 在应用中注册 tracer provider，由 exporter 导出 |
| API spans | 请求内部的 model runs、服务端工具、Managed Agents turns | 在 Console 配置 destination；AWS 的 API spans 仍是独立 traces |

这两种来源可补全不同层次的观察，不能因名称相同就把 SDK 与 API span 当重复调用。SDK 要在需追踪的首次请求前注册 provider；beta 期间 options 与 span schema 可能破坏兼容，应固定 SDK 版本并对导出查询做回归。<sup><a href="#cite-14">[14]</a></sup><sup><a href="#cite-16">[16]</a></sup>

默认 **Metadata only** 记录标识、时序、状态和用量等元数据，也可能包含自己设置的工具名称与描述。**Full content** 可以带入提示与响应，但仍可能被截断；应检查 `anthropic.content.truncated`。目的平台有独立的访问与保留设置，启用导出不能沿用对原 API 存储范围的假设。<sup><a href="#cite-14">[14]</a></sup>

API 交付为 best effort，span 可能丢失，也可能重复送达；按 **trace ID + span ID** 去重。在支持 W3C `traceparent` 的请求中，关闭 sampled flag 可以不产生 API spans；Claude Platform on AWS 暂不支持该 header，不能套用同一传播规则。没有 trace 不等于没有调用。<sup><a href="#cite-15">[15]</a></sup>

**工程推导**：诊断轨迹不能充当完整计费账本或安全审计记录。用 Usage API 对账用量，权威事件日志与外部产物继续分别核验；证据缺失时保留 unknown，不能从未观察到的 span 推断行动没有发生。官方总览也要求使用 Usage API 检查未产生 spans 的请求用量。<sup><a href="#cite-14">[14]</a></sup>

**练习建议（未执行）**：在隔离、脱敏的工具循环中，分别构造截断、丢失和重复交付；检查去重后能否关联请求、工具与产物，无法判断的结果标为 unknown。记录内容模式、SDK / schema 版本与导出覆盖，再进入[长任务评测](agent-evaluation.html)，避免只用已送达的 traces 代表所有试验。

## 最新状态与近期变化

Claude 5.5 家族分三次发布：Opus 5.5 于 **9 月 22 日**、Sonnet 5.5 于 **9 月 28 日**、Haiku 5.5 于 **10 月 7 日**。官方分别强调复杂判断、日常明确任务、高并发低成本任务。Haiku 发布稿同时宣布 Sonnet 缓存读取降价，并推出 Python / TypeScript 客户端 SDK 的浏览器与 Computer use toolset beta。<sup><a href="#cite-1">[1]</a></sup><sup><a href="#cite-2">[2]</a></sup><sup><a href="#cite-3">[3]</a></sup>

| 模型 | 发布日期 | 标准输入 / 输出单价，每百万 tokens | 本篇关注 |
|---|---|---|---|
| Opus 5.5 | 2026-09-22 | $4 / $20；缓存读 $0.20 | 长任务判断、复杂工程、协作与安全 |
| Sonnet 5.5 | 2026-09-28 | $2 / $10；10 月 7 日缓存读降至 $0.10 | 明确任务、快速迭代、缓存成本 |
| Haiku 5.5 | 2026-10-07 | 提示 ≤100k：$0.10 / $0.50；超过：$0.50 / $2.50 | 摘要、压缩、分类和有边界的子任务 |

**价格必须按最新发布核对。** Sonnet 9 月发布稿仍列缓存读 $0.20，10 月 7 日公告更新为 $0.10；这属于时间更新，不是两份资料互相否定。Haiku 的长提示价格也不能被低价摘要掩盖。以上是标准公开定价，Fast mode、cache write、平台差异和最终账单仍需单独确认。<sup><a href="#cite-2">[2]</a></sup><sup><a href="#cite-3">[3]</a></sup>

本篇不依据不同基准版本排出“最强模型”。比如官方 Sonnet 与 Haiku 文中出现不同 OSWorld 子集 / partial 标注，榜单数字不能脱离版本、effort、fallback 与运行环境解释。

## Claude Code、Agent SDK 与 Managed Agents

**Claude Agent SDK 将 Claude Code 的工具循环和上下文管理作为 Python / TypeScript 库提供；Managed Agents 则提供托管长任务服务。** 普通 Anthropic Client SDK 主要负责 Messages API 请求，应用通常自己实现 tool loop。三者承担的基础设施责任不同。<sup><a href="#cite-4">[4]</a></sup><sup><a href="#cite-5">[5]</a></sup>

| 入口 | 公开能力 | 需要应用考虑的边界 |
|---|---|---|
| Client SDK / Messages API | 模型调用、tool runner、browser / computer toolsets | 工具后端、环境与应用状态 |
| Claude Agent SDK | Read / Edit / Bash / Glob / Grep、hooks、subagents、MCP、sessions | 工作区权限、业务工具、运行资源 |
| Claude Code | 面向开发者的交互产品 | 仓库可信度、配置、审查与交付流程 |
| Claude Managed Agents | 托管 Harness、持久会话、Sandbox / 工具接口 | 环境与凭据边界、业务集成与验收 |
| Cowork | 面向一般知识工作的 Agent 产品 | 选定工作区、连接应用与可见数据 |

Agent SDK 的 wrapper、demos 与 Sandbox runtime 可以公开学习，不能据此称 Claude 模型或全部产品内部实现开源。官方 SDK 文档明确，使用项目 Skills、CLAUDE.md 等文件配置需要选择相应 `setting_sources`，默认配置发现行为应在集成时确认。<sup><a href="#cite-4">[4]</a></sup>

## Managed Agents 的三个稳定接口

2026 年 4 月 8 日的 [Scaling Managed Agents](https://www.anthropic.com/engineering/managed-agents) 是本篇最值得逐段阅读的工程博客。作者把系统拆为 **Session、Harness 与 Sandbox**，目的是让每层独立失败、替换与演化。<sup><a href="#cite-5">[5]</a></sup>

### Session 是持久事件日志

Session 保存发生过的事件，Harness 可以重新启动、读取事件并恢复。模型上下文只是从历史中构建出来的一个视图；压缩丢弃上下文中的消息，不应意味着原事件在持久存储中也消失。官方介绍 `getEvents()` 用于选择历史区间，再由 Harness 决定怎样转换成模型输入。<sup><a href="#cite-5">[5]</a></sup>

这个区分解决两类不同问题：压缩解决模型能读多少，持久日志解决系统能恢复和追溯什么。完整日志不保证正确恢复所有外部副作用，实际实现还要核对工具动作是否已生效、重复执行会不会产生第二笔变更。

### Harness 可以成为无状态执行者

官方描述，早期将日志、Harness、Sandbox 放在同一个容器，机器一坏就影响整段会话；拆分后可以通过 `wake(sessionId)` 重新唤醒 Harness。Sandbox 在需要时配置，工具失败可以返回 Agent，而不必让整个系统跟着消失。<sup><a href="#cite-5">[5]</a></sup>

官方报告这一架构改善了 TTFT，但这是其部署上的测量，不是对所有自建 Agent 的保证。工程上应把模型首响应、首次工具执行、Sandbox 冷启动和完整任务时延分开测量，才能知道优化究竟发生在哪一层。

### 凭据不进入生成代码的环境

官方介绍了外部 vault 与 MCP proxy 等模式，让 Agent 请求操作时不直接接触服务凭据。重点是把访问能力与明文密钥分离。工具输出、异常、URL、进程环境也可能泄漏敏感信息，单纯要求模型“别读密钥”不足以完成隔离。<sup><a href="#cite-5">[5]</a></sup><sup><a href="#cite-6">[6]</a></sup>

这些是官方披露的架构，并未在本仓库复现生产部署或验证安全边界。

## 长任务 Harness 的演化

2025 年的 context engineering 博客强调 compaction、结构化记笔记、按需检索和子 Agent 上下文隔离。2026 年 3 月的长应用开发博客进一步使用 **Planner → Generator → Evaluator**，按 sprint contract 明确这一阶段的交付和验收，然后用真实应用验证反馈迭代。<sup><a href="#cite-7">[7]</a></sup><sup><a href="#cite-8">[8]</a></sup>

其中有一个很容易忽略的细节：某些旧模型接近上下文限制时会过早收工，作者曾用 context reset 与 handoff 解决；换到能力更强的模型后，这些 reset 可能成为不必要开销。**Harness 应保留模型升级后能重新检验的假设。**<sup><a href="#cite-5">[5]</a></sup><sup><a href="#cite-8">[8]</a></sup>

| 机制 | 解决的问题 | 代价 / 需要验证的点 |
|---|---|---|
| Compaction | 历史超出上下文，保留主要事实 | 摘要遗漏、约束丢失、压缩费用 |
| Context reset + handoff | 清掉无效轨迹和上下文焦虑 | 新上下文需完整接收目标与状态 |
| Structured notes | 用外部文件保存可恢复知识 | 陈旧状态、文件权限、并发写入 |
| Independent evaluator | 生成者自评偏乐观 | 评估成本、rubric 校准、循环终止 |
| Sprint contract | “完成”缺少可检验定义 | 防止只按模糊产品描述验收 |

这些模式有不同目标，不能机械叠加。优先跑一个简单基线，再由真实失败例决定加哪层机制。

## Tool search、PTC 与缓存

Anthropic 的 advanced tool use 工程博客公开三个方向：**Tool Search Tool、Programmatic Tool Calling、Tool Use Examples**。Tool search 避免把所有工具定义预加载；PTC 把多步调用和中间数据留在代码执行环境；examples 补充 JSON schema 无法表达的正确用法。<sup><a href="#cite-9">[9]</a></sup>

一个日志分析 Agent 可以先发现查询工具，然后在受控代码中批量取数、过滤、聚合，最终只把异常摘要和可回查引用交给模型。其收益可能同时出现在输入量和回合数上，但要计入 sandbox、工具时延、错误恢复与权限检查。

博客给出 `defer_loading`、`allowed_callers` 等公开字段示例；这些属于当时接口，集成必须对照当前文档。该博客还指出，延迟加载的工具不占初始提示，使稳定部分更容易缓存。是否真的提高命中率，需要观察真实 prompt 组织和 provider 缓存规则。<sup><a href="#cite-9">[9]</a></sup>

## 浏览器 SDK 的重要边界

10 月 7 日公告中的 toolset **并不自带浏览器、桌面或生产 URL 策略**。官方文档要求开发者实现 browser / desktop backend；SDK 负责调用路由、配置的检查、确认 callback 与结果结构。<sup><a href="#cite-3">[3]</a></sup><sup><a href="#cite-10">[10]</a></sup>

这对实现教程很重要。安装一个包并不代表拥有可安全执行的 Computer use Agent。导航、重定向、点击产生的网络请求、上传下载、凭据和最终状态都需要由实际环境处理。官方 minimal CDP 示例是学习起点，并非完整生产方案。<sup><a href="#cite-10">[10]</a></sup>

## 多 Agent 与评测怎么学

Claude Code 文档将普通 subagents、独立 background sessions、cross-session messaging 与 agent teams 分开。普通子 Agent 主要通过独立上下文完成专项工作，返回摘要；不同机制的恢复、消息和模型选择不应混为一谈。<sup><a href="#cite-11">[11]</a></sup>

2026 年 1 月的评测博客区分 **task、trial、grader、transcript 与 outcome**。例如 Agent 声称已经改好认证逻辑，真正 outcome 是测试与实际鉴权状态。代码 grader、模型 rubric、人工抽检各有用途；复杂生成结果不能只由生成者口头自评。<sup><a href="#cite-12">[12]</a></sup>

## 官方教程与练习路线

| 材料 | 类型 | 具体阅读任务 |
|---|---|---|
| Agent SDK overview / quickstart | 官方教程 | 区分 Client SDK 与 Agent SDK 的执行责任 |
| Managed Agents engineering blog | 官方实现解读 | 跟踪三种接口怎样独立失败 |
| Effective context engineering | 工程基础 | 列出进入 prompt 的每一种数据 |
| Harness design for long-running apps | 2026 工程实践 | 把模糊交付变成阶段契约 |
| Advanced tool use | 工具优化教程 | 比较 eager 与 deferred tools |
| Demystifying evals | 评测教程 | 为任务设计环境状态 grader |
| Browser / computer toolsets | 最新 SDK 文档 | 读清 backend、policy 与确认职责 |

下面是依据官方 Agent SDK 接口改写的只读学习示例，需要正确安装与 API 凭据，本次没有执行模型请求。它不授予 Bash / Edit / Write，用来观察工具选择与结果输出。<sup><a href="#cite-4">[4]</a></sup>

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    async for message in query(
        prompt="阅读 README，列出三个值得继续查证的工程问题，附来源路径。",
        options=ClaudeAgentOptions(
            cwd="./learning-sandbox",
            allowed_tools=["Read", "Glob", "Grep"],
        ),
    ):
        if hasattr(message, "result"):
            print(message.result)

asyncio.run(main())
```

推荐练习：

1. 为同一个实验仓库建立只读检索 Agent，记录工具输出大小与最终引用。
2. 保存“目标、已验证事实、未解决问题、下一步”笔记，重启后核对信息是否足够恢复。
3. 使用独立评估上下文，只给任务验收标准与产物，检查其能否发现真实缺陷。
4. 换模型时分别测试有 / 无 reset，记录质量与代价，不沿用旧经验当永久规则。
5. 对一次真实任务做多次 trial，记录 outcome、失败类型和人工纠正次数。

## 更新记录与证据边界

- 2026-10-15：核查 10 月 14 日 OpenTelemetry public beta 与当前 SDK / API 文档，补充轨迹覆盖、截断、交付与权威状态的边界；未运行 exporter、模型调用或相关评测。
- 2026-10-13：补充状态权威范围、副作用确认空档和压缩保真度测试；保留旧 URL 与学习进度。新增恢复方案为工程推导，未执行故障注入。

- 2026-10-13：核实 Claude 5.5 发布、Sonnet 缓存价格更新、浏览器 SDK beta；串联 2025 基础博客与 2026 架构实践。
- 本篇官方发布与工程资料均已读取；厂商性能结果没有独立复测。
- 未验证：当前各云渠道的模型资格与地区状态、Managed Agents SLA、SDK 本地与生产完整安全边界。
- 新版本进入后，优先检查旧 Harness 假设、工具权限和回归结果。

<footer><div class="sources">
<h2 id="sources">来源与证据说明</h2>
<ol>
<li id="cite-1"><a href="https://www.anthropic.com/claude-opus-5-5">Anthropic · Claude Opus 5.5</a><span class="source-meta">2026-09-22 · 官方发布已读取 · 性能数字为厂商报告</span></li>
<li id="cite-2"><a href="https://www.anthropic.com/claude-sonnet-5-5">Anthropic · Claude Sonnet 5.5</a><span class="source-meta">2026-09-28 · 官方发布已读取 · 缓存价格后被 10 月公告更新</span></li>
<li id="cite-3"><a href="https://www.anthropic.com/claude-haiku-5-5">Anthropic · Claude Haiku 5.5</a><span class="source-meta">2026-10-07 · 官方发布已读取 · 含长提示定价、Sonnet 缓存更新与 SDK beta</span></li>
<li id="cite-4"><a href="https://platform.claude.com/docs/en/agent-sdk/overview">Claude Agent SDK overview</a><span class="source-meta">滚动官方文档 · 2026-10-13 读取 · 示例未运行付费请求</span></li>
<li id="cite-5"><a href="https://www.anthropic.com/engineering/managed-agents">Scaling Managed Agents: Decoupling the brain from the hands</a><span class="source-meta">2026-04-08 · 官方工程博客全文已读取 · 架构与部署收益为官方披露</span></li>
<li id="cite-6"><a href="https://www.anthropic.com/engineering/how-we-contain-claude">How we contain Claude across products</a><span class="source-meta">2026-05-25 · 官方工程博客已读取 · 区分 claude.ai / Code / Cowork 的隔离</span></li>
<li id="cite-7"><a href="https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents">Effective context engineering for AI agents</a><span class="source-meta">2025-09-29 · 基础材料，明确不是最新发布 · 已读取</span></li>
<li id="cite-8"><a href="https://www.anthropic.com/engineering/harness-design-long-running-apps">Harness design for long-running application development</a><span class="source-meta">2026-03-24 · 官方工程实践已读取 · 实验不能直接外推所有产品</span></li>
<li id="cite-9"><a href="https://www.anthropic.com/engineering/advanced-tool-use">Introducing advanced tool use on the Claude Developer Platform</a><span class="source-meta">2025-11-24 · 官方教程已读取 · beta 字段使用时需复核</span></li>
<li id="cite-10"><a href="https://platform.claude.com/docs/en/agents-and-tools/tool-use/browser-use-sdk">Browser and computer use with the SDK toolsets</a><span class="source-meta">滚动官方文档 · 2026-10-13 读取 · 不提供内置 browser / desktop backend</span></li>
<li id="cite-11"><a href="https://code.claude.com/docs/en/sub-agents">Claude Code · Create custom subagents</a><span class="source-meta">滚动官方文档 · 2026-10-13 读取 · 不同并行机制有独立语义</span></li>
<li id="cite-12"><a href="https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents">Demystifying evals for AI agents</a><span class="source-meta">2026-01-09 · 官方评测工程博客已读取</span></li>
<li id="cite-13"><a href="https://claude.com/resources/articles/agent-observability-on-the-claude-platform">Anthropic · Agent observability on the Claude Platform</a><span class="source-meta">2026-10-14 发布 · 2026-10-15 核查 public beta 与覆盖产品 · 未接入观测平台</span></li>
<li id="cite-14"><a href="https://platform.claude.com/docs/en/manage-claude/opentelemetry">Claude Platform · OpenTelemetry 总览</a><span class="source-meta">滚动官方文档，无独立发布日期 · 2026-10-15 核查 SDK / API 范围、内容模式、截断、用量与保留边界 · 未实测</span></li>
<li id="cite-15"><a href="https://platform.claude.com/docs/en/manage-claude/opentelemetry/api">Claude Platform · API spans</a><span class="source-meta">滚动官方文档，无独立发布日期 · 2026-10-15 核查 best-effort / 重复交付、traceparent、sampling 与 AWS 例外 · 未配置 destination</span></li>
<li id="cite-16"><a href="https://platform.claude.com/docs/en/manage-claude/opentelemetry/sdk">Claude Platform · SDK spans</a><span class="source-meta">滚动官方文档，无独立发布日期 · 2026-10-15 核查 tracer provider / exporter、客户端工具与 beta schema 兼容性 · 未安装或运行示例</span></li>
</ol>
</div></footer>
