---
{
  "slug": "agent-evaluation",
  "title": "长任务评测：产物、轨迹与基础设施噪声",
  "topic": "Agent Engineering",
  "summary": "从 AgencyBench、AgentLAB 与 METR 的评测口径出发，区分交付质量、可靠性、安全和环境造成的分数差异。",
  "order": 8,
  "updated": "2026-10-13",
  "tags": ["AgencyBench", "AgentLAB", "METR", "可靠性"],
  "minutes": 17
}
---

## 评测对象是一个完整系统

专业 Agent 评测至少固定模型版本、推理预算、Harness、工具、任务集、资源和 grader。最终文字、生成产物、环境状态和行动轨迹是不同观察面。一次演示能证明某条轨迹成功，不能说明换一个 seed、资源配置或任务顺序后的可靠性。

本篇资料核查日为 **2026-10-13**。选用 2026 年已经发布的评测研究与方法材料，保留原始版本；没有将历史实验中的模型顺序写成 10 月产品排名，也没有复跑下面的分数。

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

## 更新记录与证据边界

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
</ol>
</div></footer>
