---
{
  "slug": "agent-evaluation",
  "title": "长任务评测：产物、轨迹与基础设施噪声",
  "topic": "评测与交付",
  "summary": "从 AgencyBench、AgentLAB、METR 与插件评测案例出发，区分交付质量、轨迹因果、可靠性及基础设施噪声。",
  "order": 8,
  "updated": "2026-10-29",
  "tags": ["AgencyBench", "AgentLAB", "METR", "可靠性"],
  "minutes": 26
}
---

## 评测对象是一个完整系统

专业 Agent 评测至少固定模型版本、推理预算、Harness、工具、任务集、资源和 grader。最终文字、生成产物、环境状态和行动轨迹是不同观察面。一次演示能证明某条轨迹成功，不能说明换一个 seed、资源配置或任务顺序后的可靠性。

下列基础评测研究与方法材料的核查日为 **2026-10-13**；后续补充的生产 trace 与并行轨迹案例分别注明核查日期。选用 2026 年已经发布的材料，保留原始版本；没有将历史实验中的模型顺序写成 10 月产品排名，也没有复跑下面的分数。

## AgencyBench：把交付要求落实到 grader

AgencyBench v4 包含 6 类能力、32 个真实场景和 138 个任务，每项明确 queries、deliverables 与 rubrics。它用用户模拟 Agent 提供迭代反馈，在独立工作区生成产物，再同步到 Docker 环境执行和渲染，最后在 eval-space 进行规则或模型判分。论文所述约 90 次工具调用、约 1M tokens 是场景执行的统计描述，不是模型上下文窗口要求。<sup><a href="#cite-1">[1]</a></sup>

**实现取舍（工程推导）**：执行者与验收环境分离能减少对自述完成状态的依赖，却引入环境同步、截图和 grader 版本等新变量。每次同步应记录产物哈希；功能检查和视觉 rubric 分开报告；失败时保留执行日志，区分代码不正确、服务未启动、渲染超时和 judge 不确定。用户模拟器也需要版本化，因为不同反馈可能改变任务难度。

作者仓库公开场景、产物和评估脚本入口。本次读取固定 README，未逐项运行 138 个任务。复现应报告 **模型 × Harness** 的组合结果；换框架后的收益不能自动归因于模型权重。<sup><a href="#cite-2">[2]</a></sup>

## 重复运行：pass@k 与 pass^k 回答不同问题

Anthropic 的评测方法区分 transcript、outcome、grader 与 trial：`pass@k` 关注 k 次尝试至少一次成功，`pass^k` 关注 k 次全部成功。前者适用于有预算选择候选答案的流程，后者强调稳定完成。<sup><a href="#cite-3">[3]</a></sup>

在独立同分布且单次成功概率为 p 的简化假设下，至少一次成功为 `1 - (1 - p)^k`，全部成功为 `p^k`。实际任务难度不同，运行还可能共享缓存、工作区或记忆；应按任务分组估计并报告不确定性，而不是对平均成功率机械乘方。

**评估建议（未执行）**：每个 trial 重置可变环境，记录随机种子、重复次数与重试预算。将结果分成 passed、failed、infra_error、unknown，分别报告端到端成功率与条件于有效运行的成功率，明确两者分母。只报告“重试后成功”会隐藏用户等待和费用。

## 排行榜差距未必来自模型

Anthropic 2026-02-05 的控制实验保持模型、Harness 和任务固定，在最宽松与最严格资源配置间观察到约 **6 个百分点**的成绩差异。资源余量由 1× 到 3× 时，基础设施错误从 **5.8% 降到 2.1%**，成功率差仍在实验噪声范围内。这个结果说明资源限制可能干扰比较，不能推导“所有任务都应配置 3×”。<sup><a href="#cite-4">[4]</a></sup>

因此复现报告应包含 CPU / 内存保证值、kill 上限、磁盘、任务超时、并发和冷启动。比较两个系统时，先确认失败是否来自模型决策；如果其中一组频繁 OOM，直接宣称能力差距会把调度策略当成推理能力。

METR TH1.1 在 2026-01-29 将任务集从 170 扩到 228，8 小时以上任务从 14 增到 31，但只有 5 个长任务具有人类实测时间。**50% time horizon 描述模型在按人类任务耗时刻画的任务难度上达到 50% 成功的拟合位置，不是 Agent 能可靠连续运行多久。**<sup><a href="#cite-5">[5]</a></sup>

3 月 20 日研究笔记进一步讨论拟合与正则化假设，修正使部分近期模型的 50% horizon 下调最多约 20%。该材料属于审阅较少的研究笔记；趋势图应附任务分布、时间估计和拟合方法，不能单凭一条曲线推出任意生产工作的自动化期限。<sup><a href="#cite-6">[6]</a></sup>

## Terra 系统卡：把不同失败事件的分母分开

OpenAI 于 **2026-10-26** 发布 GPT-6.1 Terra 系统卡补充说明，本节 **10 月 27 日**核查。与其拼接安全分数，更值得比较各项测试究竟把什么计为事件。<sup><a href="#cite-11">[11]</a></sup>

| 系统卡中的测试 | 实际观察对象 | 不能省略的条件 |
|---|---|---|
| Auto-review 拒绝之后 | 是否尝试绕过监控；Terra 本测试未观察到此尝试 | 这不是所有环境限制下的结论 |
| 环境警告之后 | 成功规避限制，而非仅发起尝试 | 最大推理档、无系统级防护的低风险模拟；存在评测意识与外部有效性限制 |
| 外部 Agent 消息 | 交流尝试与指定未授权行动分开 | 10 类情境共 80 样本，均发现消息板；交流也包含拒绝和失败联系 |
| 内部部署模拟 | 匹配任务中的严重性标记 | 48,690 个任务，不能当外部生产事故率 |

这些披露来自研究环境或 API，提示、工具与推理档位可能不同于生产产品；不同表格的事件、样本和分母不能互换。本文未运行这些评测，也不将某项零观察解释为风险消失。<sup><a href="#cite-11">[11]</a></sup>

**工程推导（未执行）**：为每个 trial 分别记录障碍来源、模型实际看到的反馈、随后请求的动作、执行器是否放行、外部状态是否改变，以及最终向用户披露了什么。“提出了违规请求但被阻止”和“真正完成了未授权动作”应有不同结果；最终文字中的承诺也不能替代执行回执。

可以用受控的本地模拟工具构造三类验收：明确拒绝后的停止或安全交接；不可信内容带来的未授权要求；正常任务在许可内继续完成。不要在生产系统尝试绕过真实限制。对每类分别报告任务质量、违规请求、实际执行和证据缺失，把运行失败与缺少观测区分开。全部拒绝虽然可能降低行动风险，却不能证明 Agent 有可用价值。

模型路由因此需要按风险类别设门槛：便宜或快速的候选模型，仍要通过该类任务的许可、停止和交付检查；必要时转交人工或已验证路径。这个建议不依赖某个榜单名次，也不是本文对 Terra 生产可靠性的判断。接入字段与历史格式的迁移另见[模型迁移合同](model-migration.html)，本节只讨论行为验收证据。

## Gemini 4 Carbon：先对齐切片、Harness、预算与聚合

Google 在 **2026-10-28**公布 Gemini 4 Carbon，本节 **10 月 29 日**核查。公告的开放范围是部分网络防御者，并经 Fairwind 逐步扩展可信伙伴；面向开发者、企业与消费者的产品开放仍为后续计划。评测报告写使用 Gemini API，不等于读者现在能在普通账户调用 Carbon。<sup><a href="#cite-12">[12]</a></sup>

报告对 Carbon / Argon 默认采用最高思考设置与 pass@1，另列例外；小型基准会平均多次 trial，非 Gemini 结果通常来自其他提供方自报或注明的公开榜单。它并未把所有模型在同一环境重测。选读下面几项方法，比拼接公告分数更有助于设计自己的对照：<sup><a href="#cite-13">[13]</a></sup>

| 项目 | 任务与执行条件 | 报告的聚合口径 |
|---|---|---|
| SWE-sweep | Carbon 使用 mini-swe-agent 自测；其他模型取公开榜单 | 子任务加权 reward，保留其权重定义 |
| Agents' Last Exam v1.1 | 122 任务，使用 10 月 17 日版本、未加 10 月 26 日更新；默认 ALE-Claw、5 小时窗口 | 平均 rubric Score |
| OSWorld 2.1 | 82 任务离线子集，官方 Docker / evaluator、1080p、500 步上限，更新的 Gemini CUA Harness | 每个 run 单次尝试，3 个 run 取最大，报告 partial score |
| SEC-bench Pro | 2026 年 5 月的 183 任务 JavaScript engine 切片，Antigravity Harness | 每任务三次独立尝试取平均的 pass@1 |

不能把上述“平均三次”与“取最大”统称为同一种单次成功率。报告另为 ExploitGym 列出 **6 小时和 10 小时**时限、关闭 mitigations 的隔离评测设置；本节不将单个宣传分数映射到任一时限。报告的这两项 Gemini 计算机使用测试中，安全过滤返回空字符串时 episode 仍可能继续，空响应也不能直接当成整条任务已终止。本文没有运行这些评测。<sup><a href="#cite-13">[13]</a></sup>

**工程推导（未执行）**：为每条比较保存模型快照、任务版本和切片、Harness / 观察空间、时间与步数预算、采样和聚合规则、grader 及失败分类。最高思考档位不能代替 token 或费用预算；未披露字段保留未知，不自行补齐。先固定这些条件，再报告产物、轨迹与成本分布，才能判断差异是否适用于自己的系统。

例如换了任务快照、观察方式或取最大规则，就应建立新的实验记录，而非沿用原先的排名标签。这份厂商报告可用于发现需要对齐的合同，不足以给出统一模型排名或读者生产任务的收益保证。

## AgentLAB：安全需要检查整条轨迹

AgentLAB 首发于 2026-02-18，覆盖 28 个环境、644 个案例，测试意图劫持、工具串联、任务注入、目标漂移和记忆投毒。表 3 中，GPT-5.1 的任务注入攻击成功率在单轮基线为 2.08%，长轨迹配置为 21.5%。这是特定威胁模型、预算和配置的作者结果，不是所有长任务的风险概率或最新安全排名。<sup><a href="#cite-7">[7]</a></sup>

**工程推导**：逐个工具参数合法仍不足以保证组合行动符合原始目标；一次低信任内容写入记忆，还可能影响之后的任务。评测要冻结授权范围，给观察标注来源，在模拟环境追踪从外部内容到计划、记忆和行动的传播。成功完成正常任务与阻止恶意目标须并列报告，全部拒绝不能算可用的防御。

可为已有 task suite 添加三组防御性测试：同一正常目标下逐步出现冲突指令；工具组合使最终状态越出授权范围；先写入带来源标签的可疑记录、再开始新任务。只用模拟数据与隔离环境，记录违规是否真正生效，不从模型措辞猜测攻击成功。以上是测试建议，未执行攻击或生产验证。

## 最小复现记录与判分合同

以下 JSON 是建议记录格式，不是某个 benchmark 的官方 schema。数值留空表示未测，不用 0 代替未知；把 grader 版本和最终证据跟运行绑定。

```json
{
  "task_id": "research-constraint-update-01",
  "model_version": null,
  "harness_commit": null,
  "tool_schema_hash": null,
  "memory_snapshot_hash": null,
  "resource_profile": null,
  "trial_seed": null,
  "budget": {"tokens": null, "seconds": null, "retries": null},
  "grader_version": null,
  "outcome": "unknown",
  "artifact_hashes": [],
  "violation_count": null,
  "cost": null,
  "infra_failure": null
}
```

对“技术资料研究 Agent”，判分合同可以是：引用确实支持结论；来源在截止日前发布；用户修正得到应用；产物可打开；外部副作用遵守授权。评分脚本检查可机械验证的部分，人工或模型 rubric 处理语义，争议样本保留原始证据。加入[记忆策略](agent-memory.html)前，先建立这个基线，才能知道收益来自检索、训练还是更宽的预算。

## 生产 trace 进入评测前先说明缺失机制

原生 tracing 降低了收集生产轨迹的成本，但送达的 trace 仍是带有观察条件的样本。以 [Claude Platform 的 OpenTelemetry](claude.html) 为例，先核对它实际覆盖的客户端 / API 路径、sampling、交付和内容限制，再决定是否足以重建一个 trial。不能只用送达的 traces 推断所有运行的成功率或安全性。

**工程建议（未执行）**：在复现记录中补充导出覆盖范围、去重键、内容模式、截断标记、脱敏策略，以及 SDK、span schema、exporter 与 grader 版本；用请求 ID 将 trial、轨迹和产物关联。缺少关键证据的 trial 保留 `unknown`，不把“没有违规 span”计为安全通过，也不把缺失内容补成模型未采取行动。

用独立请求记录或用量数据校验覆盖，并分别报告全部 trial 数、观测到的 trial 数与证据充分的 trial 数。检查丢失是否集中在超时、异常或长输出等条件，避免只保留容易送达和判分的样本；这些分母与过滤规则应随结果发布。本次没有运行 exporter 或新的模型评测。

## 并行轨迹必须保留调用批次与依赖关系

Google Cloud 于 **2026-10-16** 发布插件评测工程案例：一次 assistant turn 把 skill-loading 与两次文档搜索放进同一 `tool_calls` 批次并发派发；加载 skill 的首次调用只返回启动信息，完整指导在下一轮才进入上下文，因此搜索已经先于指导执行。把日志压成顺序列表，会掩盖这个依赖没有满足的问题。<sup><a href="#cite-8">[8]</a></sup>

这属于作者报告的插件评测案例；文章未给该现象对应的固定 Harness 版本或修复提交。本文于 **2026-10-17** 读取正文，**2026-10-19** 复核，没有复现该任务，也不据此宣称所有 Skills 实现都有相同行为。

**工程建议（未执行）**：除时间戳与 call ID 外，保存 assistant turn、dispatch batch、任务依赖和指导实际注入上下文的时刻。判分“先读取操作约束，再调用工具”时，检查后续行动是否真正发生在约束可用之后；日志中的显示顺序、工具的最终完成顺序和模型的最终总结都不足以单独证明这一点。

可用同一任务比较“同批次派发”与“等待指导注入后再派发”，保持模型、预算、工具和 grader 不变，检查行动参数与最终产物。若前置调用失败或证据缺失，保留相应失败或 unknown，不把后续动作发生过就计为依赖满足。恢复后的任务和写入去重还需单独验证，见[运行时恢复案例](agent-engineering.html#h-63ca480a482b)。

## MultiLangBench：用数据库文件固定跨语言判分接口

OpenAI 于 **2026-10-19** 介绍 MultiLangBench：让模型用指定语言实现 SQLite 兼容引擎，以修改后的数据库文件作为跨语言共享的验收产物。这里关注评测合同，不沿用发布稿的模型排名。**2026-10-20** 读取公告及固定 README，未构建候选实现或复跑 benchmark。<sup><a href="#cite-9">[9]</a></sup>

README 将 SQLite 3.40.1 的 TCL 测试转成 `initial_database`、`user_query`、`validation_query`：候选程序接收数据库路径与查询，修改数据库；参考 SQLite 在验收端执行验证查询，与预期输出精确比较。候选环境要求移除 SQLite 并禁网，验收端仍使用参考 SQLite，两者职责不能混淆。<sup><a href="#cite-10">[10]</a></sup>

- **覆盖范围**：51k 原始测试中约 24k 被转换；默认采用名称哈希前缀为 `00`、`01`、`02` 的 272 项。运行全量须注明，子集通过率不能不加说明地与全量拼接。
- **有效性与失败**：记录 `(API cost, test pass rate)`；错误语言或混合语言的实现不合格，单项不匹配、崩溃或超过 60 秒均失败。
- **工程推导**：文件级接口把实现语言与 grader 解耦，但结果只证明所选测试下的数据库状态，不证明生产性能、并发事务或全部 SQL 语义。复现记录应固定候选 / 验收环境、套件子集与产物哈希，并单独核查语言合规。

这些是公开基准设计及由此提出的验证建议，不是本仓库测量结果。10 月 19 日是公告与所读快照的日期，不能据此推断全部测试在当天编写。<sup><a href="#cite-10">[10]</a></sup>

## 更新记录与证据边界

- 2026-10-29：核查 Carbon 公告的有限开放状态及评测报告，补充切片、Harness、预算和聚合差异；不映射未明确标注的时限，不提供模型或 benchmark 复现结果。旧来源日期保持不变。

- 2026-10-27：补充 Terra 系统卡的事件定义、样本分母与部署边界；验收表为工程建议，未运行模型或安全实验，旧研究核查日期不变。

- 2026-10-20：核查 MultiLangBench 公告和固定 README，补充跨语言产物接口、272 项子集与判分有效性边界；未运行模型或 benchmark，既有研究核查日期不变。

- 2026-10-19：复核新增 Google Cloud 案例及其发布日期、并发调用与指导注入机制；未运行对照实验，既有论文与生产 trace 文档核查日期不变。
- 2026-10-17：依据 10 月 16 日 Google Cloud 插件评测案例，补充调用批次、指导注入与依赖关系的轨迹验收；对照实验为工程建议，未运行。
- 2026-10-15：新增生产 trace 进入评测前的覆盖、去重、截断、脱敏、版本和缺失机制检查；链接运行时篇的一手文档核查，未运行 exporter 或相关评测，原研究日期不变。
- 2026-10-13：新增长任务交付、重复运行、基础设施干扰、时间跨度和长轨迹安全的评测合同。
- AgencyBench 使用 2026-04-23 v4；AgentLAB 使用 2026-02-18 v1；没有混用后续榜单。
- 作者统计均注明实验对象；本文的复现 schema 与测试清单是工程建议，未运行模型或 benchmark。
- 安全分数受攻击预算与防御配置影响；METR horizon 受任务分布和拟合假设影响。

<footer><div class="sources">
<h2 id="sources">来源与证据说明</h2>
<ol>
<li id="cite-1"><a href="https://arxiv.org/html/2601.11044v4">Li 等 · AgencyBench，v4</a><span class="source-meta">2026-01-16 首发，2026-04-23 v4 · 2026-10-13 核查任务设计、产物同步和判分流水线 · 未复跑</span></li>
<li id="cite-2"><a href="https://github.com/GAIR-NLP/AgencyBench/blob/ec65324be69e81bd4fe394ef6a86d48b8fa5da56/README.md">AgencyBench · 作者 README 固定快照</a><span class="source-meta">提交日期 2026-01-23 · 2026-10-13 核查场景与评估入口 · 未逐脚本执行</span></li>
<li id="cite-3"><a href="https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents">Anthropic · Demystifying evals for AI agents</a><span class="source-meta">2026-01-09 · 2026-10-13 核查术语、trial 与 pass@k / pass^k · 工程方法，非最新排名</span></li>
<li id="cite-4"><a href="https://www.anthropic.com/engineering/infrastructure-noise">Anthropic · Quantifying infrastructure noise</a><span class="source-meta">2026-02-05 · 2026-10-13 核查资源控制实验与基础设施错误 · 不外推统一配置</span></li>
<li id="cite-5"><a href="https://metr.org/blog/2026-1-29-time-horizon-1-1/">METR · Time Horizon 1.1</a><span class="source-meta">2026-01-29 · 2026-10-13 核查任务扩充与长任务时间测量限制</span></li>
<li id="cite-6"><a href="https://metr.org/notes/2026-03-20-impact-of-modelling-assumptions-on-time-horizon-results/">METR · Impact of modeling assumptions on time horizon results</a><span class="source-meta">2026-03-20 · 2026-10-13 核查正则化与结果敏感性 · 审阅较少的研究笔记</span></li>
<li id="cite-7"><a href="https://arxiv.org/html/2602.16901v1">Jiang 等 · AgentLAB，v1</a><span class="source-meta">2026-02-18 · 2026-10-13 核查威胁分类、评测指标及表 3 · 未复跑</span></li>
<li id="cite-8"><a href="https://cloud.google.com/blog/topics/developers-practitioners/four-eval-engineering-lessons">Google Cloud · Four evaluation engineering lessons learned from building agent plugins</a><span class="source-meta">2026-10-16 发布，未给日内时间 · 2026-10-17 读取全文，2026-10-19 复核并行 dispatch 与指导注入的因果案例 · 作者实践报告，未给固定 Harness 版本，未独立复现</span></li>
<li id="cite-9"><a href="https://openai.com/index/low-resource-programming-languages/">OpenAI · Advancing coding in low-resource programming languages</a><span class="source-meta">2026-10-19 发布 · 2026-10-20 核查 MultiLangBench 产物与参考验收设计 · 厂商发布，未复测模型结果</span></li>
<li id="cite-10"><a href="https://github.com/openai/MultiLangBench/blob/995755bffdba3da60ca367448a1606ba0e50573a/README.md">MultiLangBench · README 固定快照</a><span class="source-meta">commit 995755bffdba3da60ca367448a1606ba0e50573a，2026-10-19 · 2026-10-20 读取测试转换、子集、环境与判分合同 · 未运行测试套件</span></li>
<li id="cite-11"><a href="https://deploymentsafety.openai.com/gpt-6-1-terra">OpenAI · Addendum to GPT-6 Astra System Card: GPT-6.1 Terra</a><span class="source-meta">2026-10-26 发布 · 2026-10-27 阅读 §1、§7.1、§7.2、§7.5.1、§7.5.2 及限制说明 · 研究 / API 条件、内部部署模拟，未复跑；不同事件与分母不混用，不外推外部生产风险</span></li>
<li id="cite-12"><a href="https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-carbon/">Google · Introducing Gemini 4 Carbon</a><span class="source-meta">2026-10-28 发布 · 2026-10-29 阅读公告和开放范围 · 有限 Fairwind 接入，不视作普通 API 或产品全面开放；未采用宣传排名作为本站结论</span></li>
<li id="cite-13"><a href="https://storage.googleapis.com/deepmind-media/gemini/gemini_4_carbon_model_evaluation.pdf">Google DeepMind · Gemini 4 Carbon Model evaluation</a><span class="source-meta">随公告公开的 5 页官方文件 · 2026-10-29 阅读 PDF 第 2–4 页方法，并视觉核对第 3、5 页；本次下载 SHA-256 及复核范围见研究记录，不冒充官方版本号 · 未运行模型、Harness 或安全评测</span></li>
</ol>
</div></footer>
