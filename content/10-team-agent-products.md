---
{
  "slug": "team-agent-products",
  "title": "Team agent 选型：业务流程与 CLI 协调",
  "topic": "工具与协议",
  "summary": "核查 AvatarGaia TeamAgent、Cosmic Team Agents 与 Florious95/team-agent，按控制权、审批、状态、部署和证据边界比较。",
  "order": 10,
  "updated": "2026-10-13",
  "tags": ["Team agent", "AvatarGaia", "Cosmic", "CLI 编排"],
  "minutes": 23
}
---

## 同一个名字，三个不同层次

“Team agent”可能是加入人类业务团队的数字员工，也可能是把多个原生 Coding CLI 组织成团队的运行时。本文核查用户指定的三个对象：**AvatarGaia TeamAgent、Cosmic Team Agents、Florious95/team-agent**。`team-agent.net` 与最后一个 GitHub 仓库属于同一项目，不能计作两个产品。

资料核查日为 **2026-10-13**。前两者的机制主要来自公开文档；第三个额外检查固定版本源码。本文没有注册账户、安装运行时、调用付费模型、执行业务动作或开展安全审计。文档能力、可到达的代码路径和实机验证是不同证据等级，不能合并成“已经验证支持”。

| 对象 | 工作单元与控制面 | 本次可核查层次 | 适合先验证的场景 |
|---|---|---|---|
| AvatarGaia TeamAgent | 业务工作区、岗位、模板、共享文件与审批 | 官网流程、MCP 索引、转接层 README | 已有业务模板中的人机交接 |
| Cosmic Team Agents | 项目内 Agent 与 CMS / workflow 能力 | 发布文、当前 Agent / workflow / API 文档 | 已采用 Cosmic 的内容与代码流程 |
| Florious95/team-agent | 本地 lead、多个原生 CLI、消息与恢复状态 | README、官网、固定 Rust 源码与配置 | 跨 Claude / Codex / Copilot CLI 的协作 |

表中的适用场景是工程判断，不是实测推荐排名。协作拓扑、同预算基线与验收设计见[Agent Teams 深度主文](agent-teams.html)；这里回答产品究竟提供了哪一层，以及集成后哪些责任仍属于应用。

## AvatarGaia：业务岗位、画布与人的审批

### 公开流程能说明什么

AIcare 的 SOP 页面描述：人类与 Agent 在工作区频道沟通，资料进入共享文件夹，模板把后台操作包装成任务，主 Agent 可拆分工作，在关键节点等待机构人员确认。这里公开的是业务配置链与结果复核入口。专业业务审批不能自动证明平台拥有已审计的通用权限引擎，本文也不从这些流程推导临床有效性或合规结论。<sup><a href="#cite-1">[1]</a></sup>

AvatarGaia 的公开 MCP 索引和自描述区分匿名入口、`dk_` 开发者 Key 与 `ta_` 账号令牌，按身份开放不同能力；HTTP 接入与 stdio 转接是两个入口。`get_job` 区分 queued、running、done、failed，另有会话及事件查询。这提供可观察状态，但不说明所有任务都能从任意进程崩溃处恢复。<sup><a href="#cite-2">[2]</a></sup>

### 审批卡片不是 token 自动代签

当前索引称审批卡保留内容指纹、提交人、审批人、时间和完成结果，令牌不能代替人批准；未批卡片有过期时间，过期不代表批准。索引也披露一种由主人设置的同类动作信任机制，其适用主体有限，不能据此认定所有外部 Agent 都获得永久授权。<sup><a href="#cite-2">[2]</a></sup>

**工程验证建议（未执行）**：生成候选动作，记录其内容指纹；批准前改变参数或目标，检查是否需要重审；让不同账号、不同岗位访问同一卡片和任务，验证真实资源边界。再模拟“动作完成但回执丢失”，检查重试是否重复副作用。按成功扣费、缓存或账单去重只覆盖部分计费语义，不等于所有业务动作幂等或可回滚。

### 开源边界与数据发布边界

`AvatarGaia/canvas-mcp` 的 MIT 仓库公开的是 **stdio 到远程 streamable-HTTP 的无状态转接层**。README 称不缓存、不改写请求，并透传上游错误、处理 SSE / JSON。这不能证明整个 TeamAgent 平台开源、可完整私有部署，或远端具备特定租户隔离保证。<sup><a href="#cite-3">[3]</a></sup>

同一 README 明确知识库发布采用整库替换，并使内容可被匿名岗位访客问到。它与团队共享文件不是同一隐私边界；真实客户资料、内部运维与凭据不应通过这一公开发布路径迁移。本次固定 README 与部分网页抓取的工具数、服务端版本存在差异，工具数不作为稳定能力指标。<sup><a href="#cite-3">[3]</a></sup>

集成前还应确认私有 / 共享 / 公开数据的 ACL、导出删除、日志留存、服务端部署与恢复合同。本次只读文档，未审计转接层或远端服务；机器可读索引中的“token / credits”是平台计费术语，不直接当作模型 tokens 或人民币价格。

## Cosmic：统一 Agent 引擎加项目工作流

### 从发布定位走到现行机制

2026-03-31 发布文把 Team Agents 定位为进入 Slack、WhatsApp、Telegram 的 AI 成员，同时介绍项目 Dashboard 中的 Cosmic Agent。它们连接 CMS、代码、外部 API 和委派工具。内置 Agent 不占数量配额，不意味着调用、tokens 或外部工具无限免费。<sup><a href="#cite-4">[4]</a></sup>

当前官方文档比发布时的“四类 Agent”图更具体：Agent 为 project-scoped，运行在同一引擎上，content / code / browser / team 等入口是能力预设，实际工具由 capabilities 决定。一个 Team Agent 可以是服务人类团队的单个助手，也可以通过项目内委派参与多 Agent 流程；名称本身不是协作拓扑。<sup><a href="#cite-5">[5]</a></sup>

文档的 `message_agent` 在等待上限后可能返回 `still_running`，后续通过 `get_delegation_reply` 取结果。会话采用近期原文加旧历史摘要，并区分 session / persistent 记忆。独立会话不等于任意应用数据、凭据或长期记忆的隔离。<sup><a href="#cite-5">[5]</a></sup>

### Agent 对话审批与 workflow Gate 是两条路径

2026-06-02 的 workflow 发布文说明：Team Agent step 引用现有 Agent 的 **live ID**，并不是保存一份冻结配置；更新 prompt、model 或 capabilities 会影响所有引用流程。每步开启新会话、把输出传给后续节点，可以串行或并行。<sup><a href="#cite-6">[6]</a></sup>

该文也明确 **Team Agent step 不支持交互式审批**。需要生产审核时应设计独立 Approval Gate，不能假设 conversational `request_approval` 会在流程中自动停住。新会话隔离与实时配置引用同时存在，复现时要额外记录每步实际配置版本。<sup><a href="#cite-6">[6]</a></sup>

**工程验证建议（未执行）**：把流程分为读资料→生成候选内容→Gate→发布，批准绑定候选产物与目标。Gate 后如果内容、账号或 Agent 能力发生变化，应重新校验；并行步骤不同时写同一 CMS 对象，失败分支不能绕过审批进入发布。验证 Gate 审阅的是实际副作用，而不只是提前生成的一段摘要。

### 任务状态、历史和产物各自有寿命

Agent 消息 API 文档把同一 conversation 忙碌时的新消息标为 `202 / queued`；SSE 分开报告 `tool_progress`、`awaiting_approval`、`done`、`error`。收到排队确认、看到进度和最终完成属于三个事件，调用方要保留 conversation 与执行关联。<sup><a href="#cite-7">[7]</a></sup>

Workflows 文档当前对终态 execution 设置 90 天默认留存，清理日志、消息、步骤结果和使用记录；CMS 内容、Git 提交与 PR 的产物生命周期另行保留。因此业务产物仍存在，不代表其验收轨迹一直可追溯。通用自动重试、补偿与 exactly-once 语义未由本次资料确认。<sup><a href="#cite-8">[8]</a></sup>

安全页面描述 Workspace / Project / Bucket 分层访问，但这是平台披露，不能当作 Agent 委派、浏览器凭据和跨渠道数据传播已经独立审计的证据。所谓 Customer Facing mode 的配置收窄也不是操作系统沙箱。<sup><a href="#cite-9">[9]</a></sup><sup><a href="#cite-5">[5]</a></sup>

它比较适合将已有 Cosmic 内容资产与团队流程连接起来。若目标是通用自托管 MAS，应先确认环境、状态导出、数据驻留及供应方变更控制，不把 CMS 平台能力等同于开放运行时。

## Florious95/team-agent：跨 CLI 的本地协调层

本次静态核查固定在 `4a31d02a7410f3633e8165f5c1952f72470aae6e`，提交日期 **2026-10-13**，Cargo / npm 版本 **0.5.116**。官网与仓库描述同一项目；未安装、编译或运行原生 CLI，也未复跑仓库测试。

### 它包装原生 CLI，而不是统一模型 API

源码把 `TEAM.md` 与角色文件编译成团队配置，启动原生 CLI 成员并接入 MCP 控制面。compiler 的默认结构是 supervisor-worker、leader-centered，允许 worker-to-worker 消息；默认初始任务不是自动生成完整业务 DAG 的证明。provider adapters 为 Claude、Codex、Copilot 分别构造 prompt、MCP 和启动参数。<sup><a href="#cite-10">[10]</a></sup>

例如 Codex 路径注入 developer instructions 与 MCP 配置；Copilot 路径通过专用参数接 MCP，角色 overlay 使用工作区中的 AGENTS.md。控制面必须适配 CLI 各自的会话、权限提示和输入载体，不能把“有 adapter 文件”当成所有 provider / 版本 / 平台都已实机认证。<sup><a href="#cite-10">[10]</a></sup>

### 消息接收和工作完成不是同一个状态

固定代码中的 SQLite messages 记录 owner、task、sender、recipient、reply、状态、时间与 delivery attempts，另有 results、scheduled events、delivery tokens、health 等表。MCP 处理侧捕获成员与团队身份，检查消息作用域；delivery 路径包含原子认领、忙碌延后以及提交后仍未验证的状态。<sup><a href="#cite-11">[11]</a></sup>

这是可见的可靠性机制，但不是 exactly-once 的证明。消息被持久化、注入终端、被 CLI 消费、产生结果和完成业务任务需要分别观察；若注入已发生而状态落盘失败，立即重投可能重复工作。语义交付要回到 artifact、任务版本和外部状态。

### 恢复依赖两份状态

runtime state 保存使用锁、临时文件替换、退避和备份恢复路径；CLI 模型上下文则仍依赖其原生 transcript / session backing。restart selection 会检查恢复依据，允许显式选择 fresh，并区别 stopped / paused 成员。控制面持久化不意味着 transcript 丢失后仍有同样记忆，也不意味着主机重启即可无条件续跑。<sup><a href="#cite-12">[12]</a></sup>

建议分别验证 worker 进程崩溃、tmux 会话丢失、宿主重启、transcript 缺失和人为停止。记录哪些可以 resume，哪些必须新会话，以及旧尝试如何被阻止写回。官网的“明天继续”属于产品承诺，不能代替这些场景的实测结果。

### 控制面隔离不等于工作区隔离

常规 spawn 路径以 workspace 为工作目录。本次选读没有确认默认每 worker 都有 worktree、容器或独立文件系统；MCP scope 检查不能阻止同用户 Shell 直接改另一个成员的文件。多个 builder 并行时仍需要文件 owner、隔离工作区和单一集成点。<sup><a href="#cite-13">[13]</a></sup>

operator 文档说 `dangerously_skip_permissions: false` 保留原生 CLI 权限，它不提供只读或沙箱保证；`true` 映射为各 provider 的绕过参数。旧角色键 `tools` / `permission_mode` 会被忽略，不能用它们限制成员。内部 `send_message` / `report_result` 在部分路径可自动放行，因此“保留原生审批”也不等于每个调用都由人审阅。<sup><a href="#cite-13">[13]</a></sup>

本文不把绕过权限作为上手建议。验收应分开验证成员可见工具、CLI 原生策略、控制面身份与真正的文件 / 网络范围；环境变量绑定身份是在合作成员模型下的机制，不是同用户恶意代码的安全边界。

### 部署与文档成熟度要看实际入口

package 元数据要求 Node.js 18+，预编译安装入口列出 macOS arm64 / x64 与 Linux x64；Rust 版本要求用于源码构建。源码存在 Windows / ConPTY 相关实现，不能据此写成 npm 原生 Windows 路径已验证。仓库采用 AGPL 标注，README 与 package 元数据的具体标注存在差别，选型时保存对应 LICENSE 与版本。<sup><a href="#cite-14">[14]</a></sup>

`provider-contract-spec.md` 自称 **尚未实施的设计提案**，其中目标 API 与兼容矩阵不能当当前运行时合同。<sup><a href="#cite-15">[15]</a></sup> README 关于 Claude subagents 无法互聊的对照也应以[现行官方文档](https://code.claude.com/docs/en/sub-agents)纠正：具名通信和可恢复 subagents 已存在。这个项目值得验证的区别是跨 CLI 的控制与恢复层，而不是凭旧对照宣称首创多会话通信。

## 用同一组问题做选型

| 比较轴 | AvatarGaia | Cosmic | Florious95/team-agent |
|---|---|---|---|
| 权威资源 | 岗位、账号、模板与业务配置 | Project / Bucket、CMS 与代码产物 | 本地团队、原生 CLI 会话和工作区 |
| 审批入口 | 文档描述人的审批卡与业务确认 | 会话审批与 workflow Approval Gate 分开 | 原生 CLI 审批与内部控制工具放行分开 |
| 已知状态机制 | job / 会话 / 事件查询 | conversation、SSE、execution history | SQLite 消息状态、runtime state、原生 transcript |
| 开放实现边界 | MIT MCP 转接层 | 本次只查到托管平台文档 | AGPL 项目，可静态检查协调与适配源码 |
| 仍需确认 | 真实 ACL、审批与执行绑定、远端恢复 | live 配置变更、跨渠道数据、重试补偿 | 实机 provider 兼容、工作区隔离、重启 / 取消 |
| 成本应怎样计 | 平台单位、对话与动作计费分别确认 | 平台配额、模型 token、工具与流程成本 | 原生 CLI 计费、宿主资源与协调维护 |

没有统一 benchmark、相同模型与 workload，不能从功能表排出“最强”。应先决定要买的是业务集成、托管工作流，还是原生 CLI 的协调层，再为该层定义验收。

## 一个小范围验证方案

以下为设计建议，**未执行**。使用模拟资料和专用测试仓库，让三者完成可比较的“生成候选内容→人工确认→发布或提交→查最终状态”任务；平台资源不同，不将绝对成绩混为同一排名。

1. 固定输入资料、目标实体与候选产物 hash；增加一份无权访问的文件或账号资源，检查访问边界。
2. 批准前后分别改变候选内容和目标，检查旧批准能否被复用；所有实际副作用保留操作 ID。
3. 在动作发出但回执未到时断开会话，再重试，测重复创建、未知结果及 reconciliation。
4. 并行生成两个互相冲突的版本，检查最终由谁合并，是否会悄悄覆盖已有工作。
5. 修改角色 / Agent 配置、清理会话或删除 transcript，区分配置版本、控制面状态与模型记忆恢复。
6. 发出取消后观察在途工具、迟到消息和资源清理；“停止对话”不自动等于副作用撤销。
7. 导出验收记录，跨过平台留存周期检查能否重新追溯原始证据、授权与结果。

指标包括正常完成、越权实际生效、重复副作用、验收前后产物一致性、恢复能力、到验证结果的 p50 / p95 与完整费用。无法测到的字段保持 unknown；供应方示例、README 验证记录和本次独立实测应分开存放。

## 更新记录与证据边界

- 2026-10-13：新增三种 Team agent 对照；按业务工作流与跨 CLI 控制面组织，归入工具与协议。
- AvatarGaia：读取官网流程、公开 MCP 索引 / 自描述和固定转接层 README；未审计服务端，未注册或执行动作。
- Cosmic：读取官方发布与滚动文档；未登录、调用 API、测试 Gate 或验证安全属性。
- Florious95：本地检出固定 commit，选读 compiler、provider、MCP、消息、持久化、restart 与文档；未运行项目测试或 CLI。
- 数量、套餐与版本可能漂移；不以网页抓取失败证明某个能力不存在，不把设计提案或代码声明当实机认证。

<footer><div class="sources">
<h2 id="sources">来源与证据说明</h2>
<ol>
<li id="cite-1"><a href="https://www.aicare.group/sop-templates.html">AIcare · SOP 模板与 TeamAgent 工作区流程</a><span class="source-meta">页面未给独立发布日期 · 2026-10-13 核查频道、共享文件、任务与审批 · 文档披露，未实测</span></li>
<li id="cite-2"><a href="https://agent.avatargaia.top/llms.txt">AvatarGaia · 官方 MCP 索引</a><span class="source-meta">滚动索引，无独立发布日期 · 2026-10-13 读取；同时核对 /api/dev 与 /mcp/canvas.html · 认证、审批与 job 为文档合同，未执行</span></li>
<li id="cite-3"><a href="https://github.com/AvatarGaia/canvas-mcp/blob/33632b130d0f73b4ce66f7cc135191f63adc48dc/README.md">AvatarGaia canvas-mcp · README 固定快照</a><span class="source-meta">提交日期 2026-10-07 · 2026-10-13 读取转接层、MIT 与公开知识库边界 · 未审计转接源码或远端平台</span></li>
<li id="cite-4"><a href="https://www.cosmicjs.com/blog/introducing-team-agents-and-cosmic-agent">Cosmic · Introducing Team Agents and the Cosmic Agent</a><span class="source-meta">2026-03-31 · 2026-10-13 核查原始定位与内置 Agent 配额说明 · 发布文非现行全部机制</span></li>
<li id="cite-5"><a href="https://www.cosmicjs.com/docs/dashboard/ai/agents">Cosmic · Agents 当前文档</a><span class="source-meta">滚动官方文档 · 2026-10-13 核查统一引擎、capabilities、委派、会话记忆与执行限制 · 未登录或执行</span></li>
<li id="cite-6"><a href="https://www.cosmicjs.com/blog/team-agent-workflows-now-available">Cosmic · Team Agent Workflows</a><span class="source-meta">2026-06-02 · 2026-10-13 核查 live references、新会话和不支持交互审批的限制</span></li>
<li id="cite-7"><a href="https://www.cosmicjs.com/docs/api/agent-messages">Cosmic · Agent Messages API</a><span class="source-meta">滚动官方文档 · 2026-10-13 核查排队与 SSE 状态 · 未发送消息</span></li>
<li id="cite-8"><a href="https://www.cosmicjs.com/docs/dashboard/ai/workflows">Cosmic · Workflows</a><span class="source-meta">滚动官方文档 · 2026-10-13 核查 Gate、流程输出与 90 天终态 execution 留存</span></li>
<li id="cite-9"><a href="https://www.cosmicjs.com/security">Cosmic · Security</a><span class="source-meta">滚动页面 · 2026-10-13 核查 Workspace / Project / Bucket 披露 · 非 Agent 独立安全审计</span></li>
<li id="cite-10"><a href="https://github.com/Florious95/team-agent/tree/4a31d02a7410f3633e8165f5c1952f72470aae6e/crates/team-agent/src/provider/adapters">Florious95 · Provider adapters 固定源码</a><span class="source-meta">commit 2026-10-13，v0.5.116 · 同日选读 Claude / Codex / Copilot adapters 与 compiler.rs、worker_env.rs · 未编译或实机认证</span></li>
<li id="cite-11"><a href="https://github.com/Florious95/team-agent/blob/4a31d02a7410f3633e8165f5c1952f72470aae6e/crates/team-agent/src/messaging/delivery.rs">Florious95 · 消息交付源码</a><span class="source-meta">2026-10-13 固定快照核查；关联 db/schema.rs、mcp_server/wire.rs / tools.rs · 代码路径证据，未做故障注入</span></li>
<li id="cite-12"><a href="https://github.com/Florious95/team-agent/blob/4a31d02a7410f3633e8165f5c1952f72470aae6e/crates/team-agent/src/lifecycle/restart/selection.rs">Florious95 · restart selection</a><span class="source-meta">2026-10-13 固定快照核查；关联 state/persist.rs · 恢复依据与显式 fresh，未实测重启</span></li>
<li id="cite-13"><a href="https://github.com/Florious95/team-agent/blob/4a31d02a7410f3633e8165f5c1952f72470aae6e/docs/reference/team-agent-operator.md">Florious95 · Operator 文档</a><span class="source-meta">2026-10-13 核查固定版本；交叉读 launch/spawn.rs、provider/bypass_flags.rs、approvals/runtime_prompts.rs · 原生审批与控制面隔离边界</span></li>
<li id="cite-14"><a href="https://github.com/Florious95/team-agent/tree/4a31d02a7410f3633e8165f5c1952f72470aae6e">Florious95 · 仓库、许可证与安装元数据</a><span class="source-meta">2026-10-13 核查 README、Cargo.toml、package.json、npm/install.mjs；官网 team-agent.net 为同一项目 · 未安装</span></li>
<li id="cite-15"><a href="https://github.com/Florious95/team-agent/blob/4a31d02a7410f3633e8165f5c1952f72470aae6e/docs/reference/provider-contract-spec.md">Florious95 · Provider Contract 设计提案</a><span class="source-meta">2026-10-13 核查：文档明确未实施；Claude 对照另核 code.claude.com/docs/en/sub-agents · 不当当前能力合同</span></li>
</ol>
</div></footer>
