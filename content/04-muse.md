---
{
  "slug": "muse",
  "title": "行动边界：身份、凭据与持久记忆的信任",
  "topic": "权限与安全",
  "summary": "拆分用户身份、执行权限和证据信任，比较 VM、凭据代理与出网控制，检查跨任务记忆的权限传播。",
  "order": 4,
  "updated": "2026-10-13",
  "tags": ["身份", "凭据隔离", "记忆来源", "Meta"],
  "minutes": 15
}
---

## 常驻身份不等于无限授权

个人 Agent 需要持续身份与记忆，但权限应随目标、资源和时间限定。Meta 披露 VM、Sentinel 与凭据隔离；Anthropic 的 Managed Agents 提供凭据不进入生成代码环境的另一实现参照。厂商披露描述设计意图，不能替代独立安全审计。<sup><a href="#cite-2">[2]</a></sup><sup><a href="#cite-8">[8]</a></sup>

| 边界 | 工程上要分开的对象 | 需要验证的属性 |
|---|---|---|
| 身份与任务 | 长期用户身份、当前目标、一次行动 | 旧任务权限不会自动扩展到新目标 |
| 能力与凭据 | 可调用代理、真实 token、外部资源 | 代码可以完成获授权行动，却不能读取 token |
| 数据与指令 | 用户要求、网页观察、文件、长期记忆 | 外部内容的信任级别在写回后仍可追溯 |
| 执行与出网 | 本地进程、文件读写、网络目的地 | 分别执行策略，拒绝路径具有审计记录 |

这是一组工程检查目标，不是已经验证的 Muse 安全属性。

## 多层限制各自保护什么

**工程推导**：VM 提供进程和资源边界；凭据代理控制外部服务身份；出网控制约束数据离开的路径；任务授权决定合法目的。任一层都不能单独判断完整行动是否符合用户意图。凭据对模型不可见仍需要防止代理被诱导执行越权操作，因此操作范围和最终环境状态要进入验收。

持久记忆尤其需要保留来源、有效时间、用户归属和适用范围。一次低信任观察被压成“用户偏好”，会跨任务改变计划。应把用户明确修正与推测分开存储，支持撤销和失效，测试旧任务结束后权限是否仍被沿用。

## 安全与正常交付一起测

为同一正常任务建立无扰动与有冲突外部内容的配对测试，保存最终状态、拒绝原因、来源传播和多工具组合行为。记录正常任务成功率与违规行动生效率，避免把全部拒绝误报成可用的安全系统。长轨迹和记忆投毒的研究证据见[AgentLAB 评测导读](agent-evaluation.html)；这里没有执行攻击或验证生产隔离。

下面保留 Meta 的个人 Agent 案例与公开状态，以便区分可用能力、架构承诺和仍未公开的实现。

## 先确认讨论的是哪个 Muse

本篇案例为 **Meta 的个人 AI Agent Muse，以及 Muse Spark、Muse Wonder / Wonder Full 和 Muse Code**。检索中还出现 `museai.ltd` 的同名桌面工具；这里依据 Meta 官方 9 月与 10 月公告，避免混用产品资料。<sup><a href="#cite-1">[1]</a></sup><sup><a href="#cite-2">[2]</a></sup>

Meta 在 **2026 年 10 月 12 日**发布 Muse Wonder 与 Muse Wonder Full，距离本篇资料快照仅一天。官方明确：Wonder 已经可以通过 Meta Model API 与 Muse Code 使用；Wonder Full 供 Muse Code 订阅者使用；Wonder 在 Muse App 中的部署仍是“即将推出，先面向订阅者”。**不能把模型发布直接改写成 Muse App 全量升级。**<sup><a href="#cite-1">[1]</a></sup>

| 对象 | 官方定位 | 本次核实的状态 |
|---|---|---|
| Muse | 常驻个人 Agent 产品 | 9 月发布稿描述美国 iOS / Android / Web rollout |
| Muse Secure VM | 每个人的 Agent 执行环境 | 官方披露已用于 Muse；未验证底层具体虚拟化实现 |
| Muse Spark | 为个人 Agent 提供推理能力的模型 | 9 月稿链接 Spark 1.3；研究详情本次未成功读取 |
| Muse Wonder | 最新前沿模型 | 10 月 12 日公布，Meta Model API / Muse Code 可用 |
| Muse Wonder Full | 更高档模型 | 官方描述 Muse Code 订阅用户可用 |
| Muse Confidential VM | 计划中的加密执行环境 | 9 月稿说“今年晚些时候”，本次未核实已上线 |

这里仅保留能够追溯到官方的状态。API 价格、模型参数规模、权重开放程度、地区扩张和 App 订阅细节没有得到足够直接证据，不填写猜测值。

## Wonder 的 Active Memory 与 Active Focus

10 月公告将两项能力单独命名：**Active Memory** 帮助跨对话携带相关信息，**Active Focus** 帮助长任务保持目标、换方法、错误恢复，并在重要行动前确认。它们分别对应跨任务连续性与单任务持续性。<sup><a href="#cite-1">[1]</a></sup>

这些是官方能力描述，而不是已经公开的算法接口。当前证据不足以断定 Active Memory 使用何种向量数据库、知识图谱、检索排序或训练方法，也不能将 Active Focus 直接等同某个固定 planner-agent 架构。

从工程角度理解，Memory 的主要问题是哪些信息值得持久保存、什么时候取回、如何修改与删除。Focus 的主要问题是目标仍否有效、当前动作是否推进任务、失败后何时重试或换路。**两项问题需要不同的观测指标。**

| 学习问题 | 可观测现象 | 不应据此推断 |
|---|---|---|
| 跨对话记忆是否有用 | 新任务能准确引用先前偏好 | 模型权重已经实时更新 |
| 是否能遗忘 | 删除后不再取回该信息 | 后端所有副本已物理即时清除 |
| 是否持续推进 | 错误后找到有效替代路径 | 永远不需要人类补充信息 |
| 是否保留目标 | 多阶段后仍符合原始约束 | 仅凭更长上下文即可实现 |

这是建议的学习检查表，不包含本次没有运行的产品实验结果。

## Muse 产品的执行环境

### 独立云电脑与后台任务

9 月 8 日官方发布说明 Muse 在自己的 dedicated Secure VM 中运行，包含浏览器与用户连接的数据。任务可以在用户关闭 App 后继续，并在有变化或需要批准时回来。产品入口包括 Muse App、Web 和 WhatsApp。<sup><a href="#cite-2">[2]</a></sup>

独立执行环境让 Agent 不必直接占用用户电脑，但长期任务仍需要解决浏览器状态、服务凭据过期、外部页面变化、断线恢复与用户撤销。发布稿没有给出完整 Session API 或故障恢复协议，所以本篇将这些列为后续研究问题。

### Sentinel 位于出网路径

官方说一个 **独立的 Sentinel Agent** 在同一 VM 上运行，并与 Muse 在系统层隔开；Muse 的内容到互联网之前，需要 Sentinel 审核。它还可能请求用户许可。<sup><a href="#cite-2">[2]</a></sup>

这里应精确区分三件事：

1. 模型规划一个动作。
2. 执行环境可以实际访问哪些资源。
3. 外部行动或数据流经过怎样的审核。

Sentinel 的公开描述对应第三层。模型拒绝和环境隔离对应其他层，彼此可以补充。没有公开策略代码、测试和边界细节时，不能称其已消除 prompt injection 或保证任何路径都无风险。

### 凭据使用与凭据可见性

发布稿称 Muse 可以使用安全存储中的密码与支付能力，但不能直接看到明文密码或支付方式；用户自己在浏览器输入的密码也不向 Agent 暴露。它还提供操作审计与连接权限控制。<sup><a href="#cite-2">[2]</a></sup>

这是一项值得学习的产品原则：**授权一个能力，不必把明文凭据变成模型上下文。** 对实现者而言，要检查整个数据路径，包括 URL、异常信息、截图、日志、下载文件与 code environment。公开宣传中的“看不见密码”不是足以证明所有侧路泄漏都被排除的证据。

## 重要动作的控制面

官方例子包括发送邮件、购买、预订和填写表单。发布稿明确重要行动前会确认，用户选择连接的应用及读写范围，可随时修改或断开，并看到审计记录。<sup><a href="#cite-2">[2]</a></sup>

从个人 Agent 学习的角度，应将“找到一个合适商品”“准备结账”“实际扣款”“收到订单状态”分别观察。审批前形成的动作参数应该清晰，审批后执行也应核对相同对象。发生超时后，先查询结果，再判断是否重试。

下面是**学习用状态示意**，不是 Muse 内部协议：

```text
目标与授权范围
  → 只读探索
  → 形成可审查动作
  → 权限 / 出网检查
  → 需要时获得用户批准
  → 执行动作
  → 查询外部最终状态
  → 记录结果与后续计划
```

真正的难点在副作用和时间：一次付款或邮件发送已经生效，恢复任务时不能因为 Agent 没看到成功消息就再做一次。

## 和 dots、Gemini 工作 Agent 的共同问题

OpenAI dots、Google Gemini 工作 Agent 和 Meta Muse 的官方材料都描述持续执行、记忆与跨应用工作，但它们面向用户、访问范围和治理方式不同。对学习者更有价值的是比较共同工程问题，而非将厂商宣传词做成胜负表。<sup><a href="#cite-2">[2]</a></sup><sup><a href="#cite-3">[3]</a></sup><sup><a href="#cite-4">[4]</a></sup>

| 维度 | Muse 官方披露 | dots 官方披露 | Gemini 官方披露 |
|---|---|---|---|
| 主体 | 个人 Agent | 个人 dot 与 specialist dots | 个人 / 团队 / coworker agents |
| 环境 | Dedicated Secure VM | 独立云电脑 | 持续云执行与企业 Sandbox |
| 记忆 | 用户偏好与 Wonder Active Memory | 跨入口上下文、反馈学习 | 多类 memory 与 personalization graph |
| 控制 | Sentinel、凭据隔离、重要动作确认 | Custom Rules、auto-review、主动只读研究 | 企业身份、工具与 Skills registry、成本治理 |
| 可复现程度 | 公开产品与研究说明，核心实现未核实 | Codex / SDK 可读，dots 核心不公开 | CLI / ADK 可读，工作 Agent 私有实现不公开 |

这张表是按各自公开材料归纳，不能视作独立安全审计结果。更强的结论需要测试、实现代码或外部评估。

## 可用博客、教程与材料缺口

| 材料 | 状态 | 应怎样使用 |
|---|---|---|
| Introducing Muse Wonder and Muse Wonder Full | 官方全文已读取 | 最新发布与 API / App 区分 |
| Introducing Muse | 官方全文已读取 | Secure VM、Sentinel、凭据、权限与地区 |
| Meta research / muse-wonder | 官方发布稿指向；本次抓取超时 | 下一轮优先补模型卡、实验和定价 |
| How We Designed Muse | 官方发布稿指向；本次抓取超时 | 继续核对长任务与记忆的设计细节 |
| How We Built Safety Into Muse | 官方发布稿指向；本次抓取超时 | 继续核对 Sentinel 与 VM 威胁模型 |
| Claude Managed Agents / containment | 其他厂商公开工程博客，已读取 | 学习可替换的会话与凭据隔离模式，不代表 Muse 使用同实现 |

Muse 的核心公开材料以产品说明为主。本次没有取得可验证的完整开源 Harness 或端到端官方编码教程，因此不能假装已完成源码复现。可以先用 OpenAI SDK、Claude Agent SDK 或 ADK 实现相同类别的学习项目，并明确这只是概念练习。

## 一个适合学习的个人 Agent 实验

实验题目是“为下一周学习安排形成候选计划”，数据只来自实验目录中的学习目标和公开文章；最终产物是一份候选日程，不直接写入真实日历。

1. **目标记录**：保存时间预算、主题优先级与不可覆盖时段。
2. **只读探索**：检索文章，保留 URL、日期和摘录位置。
3. **跨回合记忆**：持久保存明确偏好与证据，不把一次随机建议当永久偏好。
4. **生成候选动作**：计划中每一项有来源、预计学习内容与时间。
5. **结果检查**：核对时间没有冲突、引用确实存在、主题满足目标。
6. **恢复与遗忘**：重启后继续；删除一个偏好后核对下次规划是否仍引用它。

验收条件是具体产物和状态：计划遵守约束、来源可追溯、旧目标修改后被替换、恢复不重复生成同一项。没有实际执行数据时，费用与成功率字段应保持空白。

## 更新记录与未验证项

- 2026-10-13：按身份、凭据、数据与行动边界组织内容，补充记忆来源和配对评测；保留 `muse.html`。新增设计为工程推导，未进行安全审计。

- 2026-10-13：纳入 10 月 12 日 Wonder / Wonder Full，确认 Muse App 更新仍是后续 rollout。
- 官方 9 月页面同时显示 9 月 8 日发布与后续修改时间；本篇采用原发布日，能力以本次读取正文为准。
- 未验证：Wonder 架构、上下文规模、参数规模、API 单价、开源权重、Sentinel 具体实现与 Confidential VM 是否已上线。
- 同名桌面产品只作消歧，不并入 Meta 产品分析。
- 本篇未登录 Muse 实测，未调用 Meta Model API。

<footer><div class="sources">
<h2 id="sources">来源与证据说明</h2>
<ol>
<li id="cite-1"><a href="https://about.fb.com/news/2026/10/introducing-muse-wonder-models/">Meta · Introducing Muse Wonder and Muse Wonder Full: Frontier Models for Agents</a><span class="source-meta">2026-10-12 · 官方全文已读取 · 最新模型发布与使用边界</span></li>
<li id="cite-2"><a href="https://about.fb.com/news/2026/09/introducing-muse-personal-ai-agent/">Meta · Introducing Muse: The World’s First Personal AI Agent Built for Everyone</a><span class="source-meta">2026-09-08 发布，页面显示后续修改 · 2026-10-13 读取 · 安全承诺未独立审计</span></li>
<li id="cite-3"><a href="https://openai.com/index/introducing-dots/">OpenAI · Introducing dots</a><span class="source-meta">2026-09-29 · 官方全文已读取 · 跨产品比较只用公开披露</span></li>
<li id="cite-4"><a href="https://cloud.google.com/blog/products/ai-machine-learning/welcome-to-gemini-at-work-2026">Google Cloud · Welcome to Gemini at Work 2026</a><span class="source-meta">2026-10-08 · 官方架构披露已读取</span></li>
<li id="cite-5"><a href="https://research.meta.ai/blog/muse-wonder">Meta · Muse Wonder research blog</a><span class="source-meta">官方公告指向 · 本次抓取超时，尚未全文核验 · 仅作补充阅读入口</span></li>
<li id="cite-6"><a href="https://introducing.muse.ai/">How We Designed Muse</a><span class="source-meta">官方公告指向 · 本次抓取超时，未用于支持内部算法结论</span></li>
<li id="cite-7"><a href="https://security.muse.ai/">How We Built Safety Into Muse</a><span class="source-meta">官方公告指向 · 本次抓取超时，未验证底层安全细节</span></li>
<li id="cite-8"><a href="https://www.anthropic.com/engineering/managed-agents">Anthropic · Scaling Managed Agents</a><span class="source-meta">2026-04-08 · 可用的工程学习参照，不能当 Muse 源码</span></li>
</ol>
</div></footer>
