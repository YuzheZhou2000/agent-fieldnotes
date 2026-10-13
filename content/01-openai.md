---
{
  "slug": "openai",
  "title": "OpenAI：从 Codex 的工具循环到常驻 Agent",
  "topic": "OpenAI",
  "summary": "沿着 Codex、Agents SDK、托管 Agents API 与 dots，理解模型、Harness 和执行环境如何分工。",
  "order": 1,
  "updated": "2026-10-13",
  "tags": ["Codex", "Harness", "Compaction", "源码"]
}
---

## 本期进展与可用边界

OpenAI 在 2026 年 9 月 10 日发布 **Agents API 公测**，将 Codex 的 Harness 与长时间执行基础设施作为托管服务提供；9 月 29 日 DevDay 又宣布 Computer use 支持、GPT-6.1 Sol 与常驻 Agent dots。这里最值得学习的变化是交付单位从一次模型响应扩大到一个可持续执行的任务。<sup><a href="#cite-1">[1]</a></sup><sup><a href="#cite-2">[2]</a></sup>

| 更新 | 原始发布日期 | 已披露状态 | 学习价值 |
|---|---|---|---|
| Agents API | 2026-09-10 | Public beta；9 月 29 日新增 Computer use，具体账号资格按文档 | 观察托管 Harness、会话和 Sandbox 的接口 |
| GPT-6.1 Sol | 2026-09-29 | API、ChatGPT Work 和 Codex；发布稿明确尚未进入 Chat | 理解能力、推理预算与每任务成本 |
| dots | 2026-09-29 | 合资格市场中的 Pro / Business Premium；企业需管理员开启 beta | 常驻身份、跨渠道上下文、主动任务 |
| Codex CLI / Cloud 更新 | 2026-09-29 | 发布稿描述语音 steering、`/agents`、复用开发环境 | 看运行中的任务怎样接受纠正与恢复 |

上述状态来自当时发布稿，**访问范围需以使用时的账户与最新文档复核**。9 月 10 日的“面向所有开发者公测”与 9 月 29 日新增 Computer use 的套餐说明针对的能力并不完全相同，不能据此假设每个账号都具有全部工具。<sup><a href="#cite-1">[1]</a></sup><sup><a href="#cite-2">[2]</a></sup><sup><a href="#cite-3">[3]</a></sup>

## 把四种入口放到正确层次

**Responses API、Agents SDK、Agents API 与 Codex 并非四个同名包装。** Responses API 提供较低层的响应与工具能力；应用可以自己维护工具 dispatch、循环和状态。Agents SDK 提供 Python 运行时，将 Agent、Runner、Tools、Handoffs、Guardrails、Sessions、Tracing 组合起来。托管 Agents API 接管云端 Harness；Codex 则是面向开发者的产品与公开代码基础。<sup><a href="#cite-1">[1]</a></sup><sup><a href="#cite-4">[4]</a></sup><sup><a href="#cite-5">[5]</a></sup>

| 入口 | 主要控制者 | 应用仍需负责什么 | 适合先学什么 |
|---|---|---|---|
| Responses API | 应用拥有循环 | 工具执行、状态、重试、权限、最终结果校验 | 一个完整 tool-use 回合 |
| Agents SDK | 应用内 SDK runtime | 业务工具、持久化选择、运行环境、策略 | Runner、session 与 handoff |
| Agents API | OpenAI 托管 Harness | 业务知识、工具、环境选择、授权与产物验收 | 会话与环境分离 |
| Codex | 产品 Harness | 仓库上下文、开发环境、审查和交付约束 | 源码中一个 turn 的生命周期 |
| dots | 常驻产品 Agent | 用户连接应用、设边界、检查重要行动 | 身份、记忆、事件触发与审批 |

这是依据公开接口做的工程分类，并不意味着公开 CLI 的每一行代码都与云端服务完全相同。

## Agents API 的实现思路

### Harness 与 Sandbox 解耦

官方将 Harness 定义为负责模型调用、工具使用、上下文与子 Agent 协调的运行时。Sandbox 则提供文件、命令与产物执行环境，可选 OpenAI 托管、自有环境或合作商。**任务决策与执行资源的生命周期可以不同**：一个长会话需要持续存在，不代表一台执行机器必须永远不坏。<sup><a href="#cite-1">[1]</a></sup>

对基础设施工程的启示是，评估托管服务时要分别问：会话存在哪儿？机器崩溃后如何恢复？文件是否保留？未返回的工具调用如何查明结果？发布稿提供了架构方向，但不能代替这些具体 SLA 与恢复语义的验证。

### 自动压缩与工具按需加载

官方披露 Agents API 会在接近上下文限制时自动压缩旧内容；Tool search 按需加载相关定义；Programmatic tool calling 用代码串联、并行和过滤工具结果。三者分别处理历史增长、工具目录增长和中间数据增长。<sup><a href="#cite-1">[1]</a></sup>

它们影响缓存的方式也不同。稳定的工具与指令前缀可以反复命中缓存；把所有动态能力塞入前缀，可能让工具发现节省的 token 被冷缓存抵消。应同时测量 cached input、uncached input、总回合数与任务成功率，不能只数缩短了多少提示词。

### 独立上下文的子 Agent

Agents API 支持主 Agent 分解任务、子 Agent 保持独立上下文，主 Agent 汇总结果。独立上下文可以让检索与验证不污染主任务，但信息交接、重复探索、取消和并发预算都需要观察。官方示例包含 `max_concurrent_subagents`，说明并行度是应显式控制的资源。<sup><a href="#cite-1">[1]</a></sup>

## Codex 源码阅读路线

本次实际读取的快照是 `openai/codex@b043762f9e3eb65dd5164ff5880f139bc6d084c7`。阅读链接固定到该 commit，避免主分支目录变化让笔记失效。没有编译整个 Codex，也没有运行付费模型任务。<sup><a href="#cite-6">[6]</a></sup>

| 阅读顺序 | 文件 / 关键符号 | 本次源码观察 | 带着什么问题读 |
|---|---|---|---|
| 1 | `session/turn.rs`：`run_turn`、`run_sampling_request` | 组装历史、创建 sampling 请求，处理需要后续执行的结果 | 模型输出如何重新进入循环？ |
| 2 | `tools/router.rs`：`ToolRouter` | 区分模型可见 specs 与可执行 registry，并存在 deferred / code-mode 等 exposure | “可见”是否等于“有权限执行”？ |
| 3 | `tools/handlers/tool_search.rs`：`handle_call` | 工具搜索有独立 handler 和缓存构建入口 | 工具发现怎样连接执行 registry？ |
| 4 | `compact.rs`：`run_compact_task_inner_impl` | 压缩使用 client session、执行 hooks、记录分析状态；区分中断、预算耗尽和上下文溢出 | 失败时是否仍然保留用户新输入？ |
| 5 | `session/context_window.rs`、`rollout.rs` | token 状态和 rollout 被拆成独立模块 | 历史存储与当前 prompt 如何分别表示？ |

这些是特定源码快照的观察。比如 `compact.rs` 在上下文超限时可移除最旧历史项重试，而中断与预算超限会走不同返回路径；这说明 **compaction 本身也需要失败分类和遥测**，并非一次永不失败的摘要调用。服务端具体实现与账号启用哪些路径，仍需另外核实。<sup><a href="#cite-6">[6]</a></sup>

建议阅读时画一个小表，每种事件写清 `input → state mutation → persisted event → user-visible output`。先追踪普通工具成功，再追踪取消、压缩失败和重新恢复，通常比通读整个大型仓库更容易形成系统理解。

## dots 值得研究的产品机制

dots 的官方说明包含独立云电脑、浏览器、跨 ChatGPT / Slack / Teams 的上下文和反馈学习。它的“主动研究”使用受限的只读工具；敏感行动会经过规则与 auto-review，用户可以查看 Activity View 并纠正任务。**主动发现机会与对外产生副作用，属于不同权限阶段。**<sup><a href="#cite-3">[3]</a></sup>

这适合启发一个学习项目：观察新事件，整理可执行工作，生成待审查产物，再在得到相应授权后执行。难点通常在事件去重、身份映射、跨渠道状态和恢复后避免重复写入。官方没有公开完整 dots 后台源码，因此本篇没有将这些建议描述成其内部既定设计。

## 模型成本要沿任务轨迹计算

GPT-6.1 Sol 发布稿给出的标准 API 单价是每百万 tokens 输入 **$2**、缓存输入 **$0.10**、输出 **$10**。这是 2026-09-29 发布稿口径，不包含工具、执行环境、特殊速度档和未来变价。<sup><a href="#cite-7">[7]</a></sup>

```text
单次模型费用 =
  非缓存输入 tokens × 输入单价
  + 缓存输入 tokens × 缓存输入单价
  + 输出 tokens × 输出单价

完整任务费用 =
  所有模型调用费用
  + 工具 / 执行环境费用
  + 失败、重试和子 Agent 费用
```

应把“缓存 tokens 已包含在总输入内”这类账单语义先确认，避免重复计算。也要同时记录每个成功任务的费用，而不是只报告单次调用便宜了多少。不同厂商、不同 effort 和不同 benchmark 的结果不宜拼成总排名。

## 资料导读与动手练习

| 资料 | 类型 | 阅读重点 | 建议顺序 |
|---|---|---|---|
| Introducing the Agents API | 官方发布 / 架构 | Harness、环境、压缩、工具搜索与子 Agent | 第一篇 |
| DevDay 2026 Recap | 官方更新目录 | 区分已上线、preview、coming soon | 快速定位近期变化 |
| Agents SDK 文档 | 官方教程 | Quickstart → Running agents → Sessions → Orchestration | 实现本地小项目 |
| Codex 公开仓库 | 开源实现 | 固定 commit 追主循环与工具路由 | 深入工程 |
| Introducing dots | 官方产品博客 | 主动只读研究、审批、身份与跨渠道 | 理解常驻产品 |

先按官方 [SDK Quickstart](https://openai.github.io/openai-agents-python/quickstart/) 跑通最小示例。下面是基于其公开接口的学习用改写，需要 API key 与模型资格，本仓库没有实际调用验证。`OPENAI_MODEL` 必须显式配置，避免示例把某个模型可用性当成永久事实。<sup><a href="#cite-4">[4]</a></sup>

```python
import os
from agents import Agent, Runner, function_tool

@function_tool
def source_policy() -> str:
    """Return the evidence requirements for a learning note."""
    return "Every release claim needs an official URL and date."

agent = Agent(
    name="Learning assistant",
    model=os.environ["OPENAI_MODEL"],
    instructions="制定学习计划，调用工具确认引用要求。",
    tools=[source_policy],
)
result = Runner.run_sync(agent, "给我一个研究 Agent SDK 的三步计划。")
print(result.final_output)
```

练习扩展按以下次序进行：

1. 加一个只读文件工具，限制到专用实验目录，返回摘录与来源路径。
2. 增加 session，重启应用后确认历史能继续使用；记录存储方式。
3. 故意制造一次工具失败，核对模型、runtime 和用户分别看到了什么。
4. 比较单 Agent 与“检索子 Agent + 主 Agent”两种方式，使用相同题目与验收条件。
5. 保存 token、时延、工具错误和来源完整性，不在没有实际运行时填写数字。

## 更新记录与未验证项

- 2026-10-13：创建首版，核实 9 月发布与公开源码快照。
- 未验证：账号实际开放范围、生产 SLA、付费 API 跑分、dots 的私有实现、源码快照是否对应所有服务端路径。
- 继续更新入口：官方 News、产品 release notes、SDK changelog、Codex releases。新模型发布后优先检查接口与任务评测，而不是替换一个模型名字就认为升级完成。

<footer><div class="sources">
<h2 id="sources">来源与证据说明</h2>
<ol>
<li id="cite-1"><a href="https://openai.com/index/introducing-the-agents-api/">OpenAI · Introducing the Agents API</a><span class="source-meta">2026-09-10 · 官方发布全文已读取 · 能力与架构属厂商披露</span></li>
<li id="cite-2"><a href="https://openai.com/index/devday-2026-recap/">OpenAI · DevDay 2026 Recap</a><span class="source-meta">2026-09-29 · 官方发布全文已读取 · 各能力有独立可用条件</span></li>
<li id="cite-3"><a href="https://openai.com/index/introducing-dots/">OpenAI · Introducing dots</a><span class="source-meta">2026-09-29 · 官方产品博客全文已读取 · 私有产品，未审计内部实现</span></li>
<li id="cite-4"><a href="https://openai.github.io/openai-agents-python/">OpenAI Agents SDK · 文档与学习入口</a><span class="source-meta">滚动文档 · 2026-10-13 读取 · 示例未执行付费请求</span></li>
<li id="cite-5"><a href="https://github.com/openai/codex">OpenAI · Codex 公开仓库</a><span class="source-meta">README 已读取 · Apache-2.0 · CLI 与云产品边界需区分</span></li>
<li id="cite-6"><a href="https://github.com/openai/codex/tree/b043762f9e3eb65dd5164ff5880f139bc6d084c7/codex-rs/core/src">Codex core/src · 本次源码快照</a><span class="source-meta">2026-10-13 拉取并读取 turn、router、tool_search、compact、context_window、rollout · 未编译</span></li>
<li id="cite-7"><a href="https://openai.com/index/introducing-gpt-6-1-sol/">OpenAI · Introducing GPT-6.1 Sol</a><span class="source-meta">2026-09-29 · 官方定价与能力披露 · 未独立复测性能</span></li>
</ol>
</div></footer>
