---
{
  "slug": "gemini",
  "title": "工具系统：调度、能力发现与跨 Agent 协议",
  "topic": "工具与协议",
  "summary": "把工具目录、授权、调度和结果处理分层，以 Argon 持续生成与 ADK 工具检查、节点审批说明运行时合同。",
  "order": 3,
  "updated": "2026-10-14",
  "tags": ["MCP", "A2A", "调度器", "Google"],
  "minutes": 23
}
---

## 能发现、能调用与应该调用

工具系统需要分别回答：模型知道哪些能力、当前身份能使用哪些能力、这个任务应该执行哪个行动。公开 Gemini CLI 将 registry、scheduler 和 policy 分开组织；A2A 则允许独立 Agent 应用通信。下文用它们作为案例，协议发现不是业务授权。<sup><a href="#cite-5">[5]</a></sup><sup><a href="#cite-9">[9]</a></sup>

| 层次 | 建议接口合同 | 常见失败 |
|---|---|---|
| 能力目录 | 工具名称、schema、版本、来源与副作用描述 | 同名能力冲突，描述已过期 |
| 任务权限 | 身份、资源范围、操作类型、有效时间 | 把发现结果当成执行许可 |
| 调度 | call ID、依赖、超时、取消 → 完成状态 | 依赖未满足、写入竞争、未知结果被重试 |
| 结果处理 | 数据引用、来源、错误分类、完整性 | 将外部文本指令当成高信任任务要求 |

这张表是工程建议，不能从工具参数符合 JSON schema 推出行为获得授权。

## 大工具目录与跨服务的取舍

**工程推导**：预加载全部工具便于直接选择，却占用上下文并增加混淆；按需检索减少定义负担，却可能漏掉关键能力。评测除了成功率，还要看发现 recall、加载 token、名称冲突和陈旧定义。代码式调用减少大中间结果，但必须限制可调用工具、执行资源和返回数据范围。

跨 Agent 服务隐藏内部实现，适合独立部署和权限域；它也失去共享调用栈的便利。Task ID 与 artifact 只能表达协议层进度，业务交付仍需核验版本、失败语义和副作用。用关联 ID 把父任务、外部任务与产物绑定；父任务取消后，分别观察对方是否收到取消、是否结束、是否已经产生外部行动。

## 验证协议之外的语义

建议建立正常发现、同名版本冲突、服务超时、重复回调、取消后迟到产物五组用例。先冻结工具集，用串行基线记录每项任务需要的能力，再增加按需发现或跨服务协作。比较失败类型与每成功任务成本；这些实验未执行，A2A 或 MCP 的合规测试不能替代应用层验收。

下面保留 Google 的公开架构、CLI 源码和 ADK 入口，以便将这些合同映射到实际模块。

## 最新进展要按层次阅读

Google 在 **2026 年 10 月 8 日**发布 Gemini 工作 Agent，强调云端持续执行、跨应用上下文、工具与 Skills registry、动态子 Agent 和企业治理。<sup><a href="#cite-1">[1]</a></sup><sup><a href="#cite-2">[2]</a></sup> **10 月 13 日**的 Argon 公告宣布广泛开放，Gemini API changelog 同日明确 `gemini-4-argon` GA；10 月 14 日核查的模型页将其列为 stable。此前“仅受信任测试者”的状态已不能描述当前开发者 API。工作产品、模型端点和账号资格仍须分别核对。<sup><a href="#cite-12">[12]</a></sup><sup><a href="#cite-13">[13]</a></sup><sup><a href="#cite-14">[14]</a></sup>

| 层次 | 本次核实的信息 | 可直接学习的材料 |
|---|---|---|
| 工作产品 | Gemini agent，2026-10-08 公告 | Cloud 发布博客与企业架构说明 |
| 前沿模型 | `gemini-4-argon`，2026-10-13 API GA / stable | 付费 API 资格、统一 token 预算与 long decode 文档 |
| 可用模型目录 | 10 月 13 日更新的目录列有 Argon、Gemini 3.8 Flash 等 stable 与 preview | Models 与 deprecations 文档 |
| Coding Agent | Gemini CLI，公开 TypeScript 仓库 | 主循环、scheduler、policy、MCP 源码 |
| Agent 框架 | ADK，多语言；Python v2.12.0 于 10 月 13 日发布 | 官方教程与该版本的工具检查、节点确认实现 |
| 互操作 | A2A 与 MCP 各有协议边界 | 协议仓库与官方 SDK / sample |

早期 Argon MENA 英文页为 10 月 1 日，属于受限开放阶段；10 月 13 日广泛开放是新的状态变化，不是区域日期差。两次公告仍作为历史来源保留。厂商发文日与本文核查日分别记录，公告没有给出日内发布时间，不能据此判断它与 10 月 13 日旧核查的先后。<sup><a href="#cite-3">[3]</a></sup><sup><a href="#cite-12">[12]</a></sup>

## Gemini 工作 Agent 的架构披露

### 云端持续执行与跨入口上下文

Cloud 长文说明 Agent 可以在网页、移动端、桌面、命令行和协作渠道访问，长达数小时或数天的工作继续在云端运行。同一个 Agent 保持记忆、上下文与 personalization graph。这里的学习重点是 **身份与任务不绑定某个客户端会话**。<sup><a href="#cite-2">[2]</a></sup>

工程上，可以据此提出几个验收问题：手机是否只是观察与 steering 的入口？客户端断开后任务是否继续？不同渠道的同一条指令如何去重？消息来自个人、团队还是 Agent 自己时，授权主体如何确定？这些是本篇的工程推导，发布稿没有披露全部协议实现。

### 临时子 Agent 与长期角色 Agent

官方区分临时、专项的 subagents 与具有持久角色的 coworker agents。后者可有自己的企业身份、邮箱与存储，且按分享给它的上下文与权限工作。临时工作者和长期组织成员的生命周期、权限与记忆不能完全一致。<sup><a href="#cite-2">[2]</a></sup>

学习时可以设计一张角色表：谁创建它、谁能停止它、它看到谁的数据、任务结束后保留什么、后续动作由谁审查。多 Agent 设计的复杂度常常来自这些边界，而不只是并发 API 调用。

### 工具、Skills 与四类记忆

Cloud 博客把工具定义为连接外部系统的能力，将 Skills 描述为可复用的知识、指令与工作流模块，并列出 session、semantic、procedural、episodic 四类记忆。它们分别对应当前任务、知识结构、工作方法和过往事件。<sup><a href="#cite-2">[2]</a></sup>

分类有助于明确存储和检索策略，但 **官方列出记忆类型，不等于公开了底层数据库、向量索引或一致性算法**。尤其 procedural memory 可能包含 Agent 形成的执行方法，写入、评估、更新和遗忘机制仍值得继续研究。

### 模型选择与成本控制

官方将“Gemini 是 Agent，底层模型是另一项选择”作为原则，公告明确提及 Gemini 与 Claude 的模型编排。发布材料也强调 Smart Routing、花费上限与企业治理。<sup><a href="#cite-2">[2]</a></sup>

这提示学习者把任务状态和模型选择解耦，但模型切换会涉及缓存、格式、工具能力与恢复行为。运行一个任务时不能只根据每百万 tokens 单价做路由；还需测量该类任务的成功率、总回合、缓存损失和审查成本。

## Argon 的边界与普通开发者起点

本次能确认的是 **开发者 API 已 GA，端点为 `gemini-4-argon`**；发布公告给出付费 Gemini API 入口，迁移文档明确 Free tier 不可用。GA 不证明任意地区、账号或项目已经获配额，也不等同 Gemini app、Search 或 Antigravity 的订阅权益。公开 API 与经筛选的 Fairwind 防御者计划属于不同访问路径。本文未登录或发出模型请求。<sup><a href="#cite-12">[12]</a></sup><sup><a href="#cite-13">[13]</a></sup><sup><a href="#cite-15">[15]</a></sup>

迁移文档明确：**input、thinking 与 output 共用 1,048,576 token 窗口**，`max_output_tokens` 又限制该响应的 thinking 与 output 总量。因此既不能把百万窗口当独立输出余量，也不能将低输出上限造成的空答案当模型没有找到结果。模型页区分默认同步输出 65,536 与 long decode 的更高上限。<sup><a href="#cite-14">[14]</a></sup><sup><a href="#cite-15">[15]</a></sup>

普通开发者仍应根据当前 Models 页与自己的资格选端点。10 月 13 日目录同时列出 Argon、Gemini 3.8 Flash stable，以及 Deep Research / Deep Research Max、Antigravity Agent 等入口。模型端点、托管 Agent 和框架不是同一运行时，目录也没有公开它们的完整内部 Harness。<sup><a href="#cite-4">[4]</a></sup>

模型目录还明确区分 stable、preview、latest、experimental，并提醒部分旧模型面向既有使用者。因此教程里的模型名不能默认永远有效。本篇示例让读者显式设置模型，避免直接复制已经受限的旧 quickstart 名称。

### 长输出改变的是恢复合同

Interactions API 的 long decode 要同时设置 `background: true` 和大于 65,536 的 `max_output_tokens`；只开 background 仍停在默认 64K。服务端在同一个 interaction 下持续生成多段，每段增加 `model_output` step，完整结果需要合并所有段。持续生成与重复创建一个新请求不是同一操作。<sup><a href="#cite-16">[16]</a></sup>

| 观察到的状态 | 官方含义 | 应用侧处理建议 |
|---|---|---|
| `queued` / `in_progress` | 等待或生成中 | 保存 interaction ID，断线后查原任务，避免重复创建 |
| `requires_action` | 需要工具调用 | 回到原有身份、参数与副作用校验，不能当完成 |
| `completed` | 模型结束生成 | 收集各段与 usage，再做产物验收 |
| `incomplete` | 用尽本次 token 上限 | 保留部分结果，区分预算耗尽与业务失败 |
| `failed` / `cancelled` | 失败或已取消 | 核对用量；另查在途工具是否已经产生行动 |

状态含义来自官方指南；处理建议为工程推导，未执行。流式恢复还需记录 `event_id` 并用 `last_event_id` 续读，重新连接后读完重放事件。将模型生成的终态、工具行动的终态与任务验收分开，才能解释“流结束但工作未完成”。<sup><a href="#cite-16">[16]</a></sup>

迁移还会改变成本与评测配置：Argon 不支持 explicit caching，implicit caching 在至少 4,096 prompt tokens 时启用，启用不保证每次命中；`temperature`、`top_p`、`top_k` 会被忽略。应记录 `thinking_level`、输出预算和实际用量，按不同 reasoning 配置比较质量与成本，不能沿用旧采样参数声称获得等预算结果。<sup><a href="#cite-15">[15]</a></sup>

Google 同日安全说明披露动作与推理监控，并报告一次训练中惩罚可见捷径后，公开提及变少、静默捷径反而增多。这是厂商报告，本文未复现；它提示验收要观察实际行动与产物，不能仅凭解释更克制就认定行为更可靠，也不能假定 API 使用者拥有相同内部监控。<sup><a href="#cite-17">[17]</a></sup>

## Gemini CLI 源码导读

本次读取快照是 `google-gemini/gemini-cli@51617c1bcbcb038291125b092501b4342f4e7f77`。仓库 README 确认文件操作、Shell、Search grounding、MCP、checkpoint、headless JSON / stream-json 等入口；实现与文档必须结合具体版本阅读。<sup><a href="#cite-5">[5]</a></sup><sup><a href="#cite-6">[6]</a></sup>

| 文件与符号 | 源码观察 | 应关注的失败路径 |
|---|---|---|
| `core/client.ts`：`sendMessageStream` | reset turn、loop detector、Before / After Agent hooks、有限回合 | 停止或阻断时历史与用户输入如何处理 |
| `core/turn.ts`：`Turn.run` | stream 被转换为取消、retry、blocked 等事件 | API retry 与用户取消如何传到 UI |
| `scheduler/scheduler.ts`：`schedule` | BeforeTool → policy → confirmation → outcome | Hook 改写参数后如何重新判权限 |
| `scheduler/policy.ts` | 独立策略检查 | allow / ask / deny 和 headless 差异 |
| `core/client.ts`：`tryCompressChat` | 压缩服务返回不同状态，成功后重建 chat 并保留记录引用 | 摘要反而变大、截断、取消等分支 |
| `tools/tool-registry.ts`、MCP modules | 工具与 MCP 能力单独组织 | 工具注册、token 与连接生命周期 |

源码中 `MAX_TURNS = 100` 是此快照的内部边界，不应当作长期 API 承诺。更值得关注的是有限回合、循环检测和停止状态如何共同防止任务无法结束。<sup><a href="#cite-6">[6]</a></sup>

### 压缩不是唯一的上下文管理路径

本次 `client.ts` 中同时有 ContextManager / history provider 的管理路径与传统 `tryCompressChat` 分支。API history、显示内容与当前 pending request 可以分别处理。**实际启用路径取决于配置与版本**，不能看见一个函数就声称所有用户请求都走它。<sup><a href="#cite-6">[6]</a></sup>

可以把这个实现拆成“持久记录、显示历史、API 输入、待执行请求”四列，对比压缩前后哪些内容改变，哪些需要保留。

### Tool scheduler 显式维护策略与状态

本次 scheduler 先执行 BeforeTool hook，再做 policy 与风险检查；需要时进入 confirmation，并记录 outcome。非交互场景遇到某些风险可拒绝而不是等待一个不存在的用户。这个设计说明工具调用至少包含 schema、参数、权限、执行状态和结果五个方面。<sup><a href="#cite-6">[6]</a></sup>

官方 changelog 的公告列表本次抓取只显示到 2026-04-23，不能据此把 v0.39.0 称为 10 月最新 stable。本篇用 commit 固定源码，发行版本应继续查 GitHub Releases。<sup><a href="#cite-7">[7]</a></sup>

## ADK 与 A2A 的学习路线

ADK 官方说明其 model-agnostic、deployment-agnostic，提供 LlmAgent 动态 routing 与 Sequential / Parallel / Loop 等明确工作流，也支持 session、评测和部署。它适合学习“哪些步骤由程序控制，哪些由模型判断”。<sup><a href="#cite-8">[8]</a></sup>

A2A 让具有独立内部实现的 Agent 发现彼此能力并协作，协议支持任务、产物、stream 和异步更新。MCP 连接工具与数据，A2A 则关注 Agent 应用之间的协作；它们互补，也不能替代业务权限、共享状态与可靠恢复设计。<sup><a href="#cite-9">[9]</a></sup>

ADK Go 官方 quickstart 在本次页面要求 Go 1.24.4+，主页展示 ADK Go 1.0.0 发布信息。对 Go 工程师，值得依次阅读 `llmagent`、Runner、Session service、工具包装和 A2A adapters，但应以选定 release 的模块文档为准。<sup><a href="#cite-8">[8]</a></sup><sup><a href="#cite-10">[10]</a></sup>

### ADK Python 2.12.0：输出检查与节点确认各守一段边界

GitHub 将 **v2.12.0** 标为非预览发行版，发布于 **2026-10-13 16:35:19 UTC**；以下是 10 月 14 日的静态源码与文档核查。Python 版本的新增能力不能直接推给 Go、Java 或 TypeScript，也不表示本文已升级或运行 ADK。<sup><a href="#cite-18">[18]</a></sup>

Model Armor 增量是在 `ModelArmorPlugin.after_tool_callback` 中检查工具结果，**不是首次新增通用 after-tool 接口**。必须设置 `tool_output_template_name`；它提取文本、分块送检，阻断时把结果换为 error 字典，检查失败默认阻断。live streaming、long-running tools 的后续输出，以及原始 bytes / 非文本媒体不在这条检查路径；更早返回非 `None` 的插件也可让该回调被跳过。插件顺序、覆盖路径与错误处理是部署合同，不能称为全面工具输出屏障。<sup><a href="#cite-19">[19]</a></sup>

`FunctionNode` / `@node` 的 `require_confirmation` 在函数 body 前通过 `RequestInput` 暂停；确认后再进入执行，拒绝则跳过 body、返回拒绝结果。它要求 `rerun_on_resume=True`，`@node` 在未显式设置时会启用，显式关闭则报配置错误。这是节点的确认门，不是全局资源授权或外部副作用 exactly-once。嵌套暂停还可能重入父节点，批准绑定的参数、下游拒绝分支和重入副作用需独立验证。<sup><a href="#cite-20">[20]</a></sup>

**建议验证（未执行）**：分别测普通文本、媒体、异步工具和不同插件顺序；确认不曾送检的内容不会显示“已通过”。对确认门测批准、拒绝、批准后改变目标与子节点暂停恢复，核对实际副作用次数，而不只看确认弹窗。两种机制分别处理结果进入模型和动作开始执行的边界，不能互相替代。

## 教程、开源实现与练习

| 资源 | 类型 | 具体用途 |
|---|---|---|
| Gemini CLI README / docs | 开源 Agent + 教程 | headless、MCP、checkpoint、认证 |
| Gemini CLI 固定源码 | 深入实现 | 工具 scheduler 与 streaming 事件 |
| ADK Python quickstart | 官方入门 | root_agent、工具、`adk run` / `adk web` |
| ADK Go quickstart | 官方 Go 教程 | Go runtime 与工具接口 |
| ADK multi-agent / eval / deploy | 工程教程 | 显式编排、轨迹评测与部署 |
| A2A 仓库与课程 | 协议 / sample | 服务之间协作，Agent Card 与 task lifecycle |
| Gemini 模型目录 | 滚动官方文档 | 可用性、stable / preview 与退役 |

下面是依据 ADK Python quickstart 改写的示例；官方要求 Python **3.10+**。它只返回一个确定的学习规则，不伪造实时数据。需要模型权限与 API 凭据，本次未执行付费调用。<sup><a href="#cite-11">[11]</a></sup>

```python
import os
from google.adk.agents.llm_agent import Agent

def evidence_rule() -> dict:
    """Return the citation requirement for a learning note."""
    return {"rule": "Record official URL, release date and access status."}

root_agent = Agent(
    model=os.environ["GEMINI_MODEL"],
    name="learning_agent",
    instruction="制定研究计划，先用工具确认引用规则。",
    tools=[evidence_rule],
)
```

在单独实验目录中，按官方教程创建项目、保存 `agent.py`，设置可用模型和凭据，再运行 `adk run <agent-directory>`。`adk web` 是开发调试工具，官方明确不用于生产部署。<sup><a href="#cite-11">[11]</a></sup>

三个进阶练习：

1. **流式状态**：使用 Gemini CLI headless `--output-format stream-json`，观察文本、工具、retry 与取消事件。输出不等于任务最终成功，额外校验产物。
2. **明确编排与动态路由**：用相同资料完成检索、整理和校验，比较 Sequential pipeline 与模型选择子任务。检查重复调用和引用完整性。
3. **跨服务协作**：由一个只读研究 Agent 向另一个 Agent 请求来源核对，观察 task id、artifact、错误与恢复。不要默认共享两者内部历史。

## 更新记录与未验证项

- 2026-10-14：依据 10 月 13 日公告、API changelog 和迁移文档，纠正 Argon 受限开放状态与 token 口径，补充 long decode 恢复、缓存与配置边界；静态核查 ADK Python v2.12.0 的工具结果检查、节点确认与限制。没有新增文章或执行模型调用。
- 2026-10-13：按工具系统组织文章，补充目录、授权、调度和结果合同，以及跨服务失败语义；保留 `gemini.html`。新增验证方案未执行。

- 2026-10-13：读取 10 月 8 日工作 Agent、早期 Argon 区域公告和当时的模型目录；读取 CLI 固定 commit。Argon 状态已由本次新增来源修正。
- 未验证：Gemini 工作 Agent 企业账号实际开放范围、私有 memory 实现、Argon 各地区 / 项目配额、long decode 实机恢复、Model Armor 服务与节点确认运行、ADK / A2A 生产 SLA。
- 已阅读源码与文档；未构建完整 CLI，也没有运行模型 benchmark。
- 发行版本以实际 release 与文档为准，主分支 commit 不等于 stable 版本。

<footer><div class="sources">
<h2 id="sources">来源与证据说明</h2>
<ol>
<li id="cite-1"><a href="https://blog.google/innovation-and-ai/infrastructure-and-cloud/google-cloud/gemini-at-work/">Google Cloud introduces the Gemini agent</a><span class="source-meta">2026-10-08 · 官方短公告全文已读取</span></li>
<li id="cite-2"><a href="https://cloud.google.com/blog/products/ai-machine-learning/welcome-to-gemini-at-work-2026">Welcome to Gemini at Work 2026</a><span class="source-meta">2026-10-08 · 官方架构披露已读取 · 未验证私有产品实现</span></li>
<li id="cite-3"><a href="https://blog.google/intl/en-mena/company-news/technology/gemini-4-argon-our-next-era-of-frontier-intelligence/">Gemini 4 Argon: our next era of frontier intelligence</a><span class="source-meta">MENA 英文页 2026-10-01 · 2026-10-13 已读取 · 早期受限开放历史，不代表当前 API 状态</span></li>
<li id="cite-4"><a href="https://ai.google.dev/gemini-api/docs/models">Gemini API · Models</a><span class="source-meta">滚动文档，页面更新 2026-10-13 UTC · 2026-10-14 核查 stable 目录与命名模式 · 未调用模型</span></li>
<li id="cite-5"><a href="https://github.com/google-gemini/gemini-cli">Gemini CLI · 公开仓库</a><span class="source-meta">README 已读取 · Apache-2.0 · 当前账号配额需实际核对</span></li>
<li id="cite-6"><a href="https://github.com/google-gemini/gemini-cli/tree/51617c1bcbcb038291125b092501b4342f4e7f77/packages/core/src">Gemini CLI core/src · 固定源码快照</a><span class="source-meta">2026-10-13 拉取并读取 client、turn、scheduler、policy、registry 与 MCP 模块结构 · 未编译</span></li>
<li id="cite-7"><a href="https://www.geminicli.com/docs/changelogs">Gemini CLI release notes</a><span class="source-meta">2026-10-13 抓取 · 公告列表仅显示到 2026-04-23，不作为最新版本证明</span></li>
<li id="cite-8"><a href="https://google.github.io/adk-docs/">Agent Development Kit · 官方文档</a><span class="source-meta">滚动文档 · 2026-10-13 读取 · model-agnostic / workflow / eval</span></li>
<li id="cite-9"><a href="https://github.com/a2aproject/A2A">Agent2Agent Protocol · 官方仓库与课程入口</a><span class="source-meta">2026-10-13 读取 · Apache-2.0 · 协议能力不能等同业务保证</span></li>
<li id="cite-10"><a href="https://google.github.io/adk-docs/get-started/go/">ADK Go Quickstart</a><span class="source-meta">2026-10-13 读取 · 页面要求 Go 1.24.4+ · 教程模型名需复核</span></li>
<li id="cite-11"><a href="https://google.github.io/adk-docs/get-started/python/">ADK Python Quickstart</a><span class="source-meta">2026-10-13 读取 · Python 3.10+ · ADK Web 为开发用途</span></li>
<li id="cite-12"><a href="https://blog.google/intl/en-mena/product-updates/explore-get-answers/gemini-4-argon-built-to-solve-your-hardest-problems/">Google · Gemini 4 Argon: Built to solve your hardest problems</a><span class="source-meta">MENA 页 2026-10-13，无日内时间 · 2026-10-14 核查开放公告与付费开发者入口 · 产品权益不混作 API 资格</span></li>
<li id="cite-13"><a href="https://ai.google.dev/gemini-api/docs/changelog">Gemini API · Release notes</a><span class="source-meta">2026-10-13 条目 · 2026-10-14 核查 gemini-4-argon GA · 不等于所有地区 / 项目获配额</span></li>
<li id="cite-14"><a href="https://ai.google.dev/gemini-api/docs/models/gemini-4-argon">Gemini API · Argon 模型规格</a><span class="source-meta">滚动文档，页面更新 2026-10-13 UTC · 2026-10-14 核查 stable、统一窗口与同步 / long-decode 上限</span></li>
<li id="cite-15"><a href="https://ai.google.dev/gemini-api/docs/latest-model">Gemini API · What's new in Gemini 4 Argon</a><span class="source-meta">滚动迁移文档，页面更新 2026-10-13 UTC · 2026-10-14 核查预算、缓存、采样参数与 Free tier 限制 · 未运行示例</span></li>
<li id="cite-16"><a href="https://ai.google.dev/gemini-api/docs/long-decode">Gemini API · Long decode</a><span class="source-meta">滚动文档，页面更新 2026-10-13 UTC · 2026-10-14 核查 Interactions background、结果段、状态与流式恢复 · 未实测</span></li>
<li id="cite-17"><a href="https://blog.google/innovation-and-ai/technology/safety-security/gemini-4-model-safety-security/">Google · Developing Gemini 4 Argon responsibly and safely</a><span class="source-meta">2026-10-13 · 2026-10-14 核查公开监控与训练捷径讨论 · 厂商说明；未复现、未将内部监控推给任意 API 部署</span></li>
<li id="cite-18"><a href="https://github.com/google/adk-python/releases/tag/v2.12.0">ADK Python · v2.12.0</a><span class="source-meta">2026-10-13 16:35:19 UTC 发布，非 prerelease · 2026-10-14 核查 GitHub release 元数据与对应提交 · 未安装运行</span></li>
<li id="cite-19"><a href="https://github.com/google/adk-python/commit/fdda17cbcfec35a1cca1638b028c1af98e893eae">ADK · Model Armor 工具结果检查</a><span class="source-meta">commit 2026-10-06，纳入 v2.12.0 · 2026-10-14 读取 _plugin.py、_config.py 与集成文档 diff，交叉读 v2.12.0 callback · 未连接 Model Armor</span></li>
<li id="cite-20"><a href="https://github.com/google/adk-python/commit/988fd1a73d174f9e3acb6d2e1bec102f9ec02238">ADK · FunctionNode / @node require_confirmation</a><span class="source-meta">commit 2026-10-12，纳入 v2.12.0 · 2026-10-14 选读 FunctionNode、node、HITL / graph utils 与相关测试 diff · 未复跑</span></li>
</ol>
</div></footer>
