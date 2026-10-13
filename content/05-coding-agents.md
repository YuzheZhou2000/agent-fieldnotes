---
{
  "slug": "coding-agents",
  "title": "Cursor 与 Devin：从写代码走向可验证交付",
  "topic": "Coding Agents",
  "summary": "学习真实产品中的缓存、模型路由、单写者协作、云执行和验收，理解 Coding Agent 的最后一段工作。",
  "order": 5,
  "updated": "2026-10-13",
  "tags": ["Cursor", "Devin", "缓存", "验证"]
}
---

## 最近值得追踪的产品与工程更新

Cursor 10 月 6 日的更新加入 iOS 对本地 Agent 的 Remote Control；9 月 23 日发布 Rollouts / Security Reviewer 与长任务 token efficiency 工程博客。Devin 本次可读取的官方博客目录主要覆盖到 6 月，重点材料是 4 月多 Agent 实践、4 月云 Agent 架构与 5 月自动化验证。**本篇不将旧博客目录最上方条目称作最新版本号。**<sup><a href="#cite-1">[1]</a></sup><sup><a href="#cite-2">[2]</a></sup><sup><a href="#cite-3">[3]</a></sup><sup><a href="#cite-4">[4]</a></sup>

| 更新 / 材料 | 日期 | 直接学习点 |
|---|---|---|
| Cursor Remote Control | 2026-10-06 | 手机 steering 与执行位置的区别 |
| Cursor token efficiency | 2026-09-23 | 稳定前缀、工具按需加载、文件读取压缩 |
| Cursor Rollouts / Security Reviewer | 2026-09-23 | 从 PR 到部署后监控与回滚审查 |
| Cursor Self-Hosted Machines | 2026-09-02 | 云端 Harness 与自有 execution workers |
| Cursor Router | 2026-08-06 | 逐 turn 复杂度、任务标签与成本路由 |
| Devin verification | 2026-05-29 | 源码驱动的测试计划与可审查证据 |
| Devin multi-agents | 2026-04-22 | 单写者加协作智能、独立 review 上下文 |

这些材料没有提供全部产品源码，学习重心是公开工程机制、接口与可检验行为。

## Cursor：上下文组织直接影响成本

9 月的 token efficiency 博客描述了几个互补优化：精简旧模型需要的系统提示，将低频工具放入动态上下文，稳定缓存边界前的内容，把变化较大的设置移动到后面，减少逐行编号开销，并让模型更自然地选择子 Agent。<sup><a href="#cite-3">[3]</a></sup>

### 稳定前缀比“更短提示词”更具体

Agent 每轮会重发工具、系统规则与历史。缓存命中取决于 provider 能复用的前缀是否稳定。工具顺序变化、用户动态信息、环境快照和模型切换都可能让命中降低。Cursor 博客把内容按稳定程度组织，并描述在可用 API 上使用 cache breakpoints。<sup><a href="#cite-3">[3]</a></sup>

对实现者而言，最好建立一张 prompt 分层表：

| 层 | 内容例子 | 变化频率 | 应观察什么 |
|---|---|---|---|
| 固定协议 | 工具基础定义、系统行为 | 低 | 长期缓存复用 |
| 用户 / 项目设定 | Skills、环境、子 Agent 描述 | 中 | 变化时会打断哪些前缀 |
| 当前任务 | 用户输入、近期历史 | 高 | 每回合增长量 |
| 临时工具结果 | 大文件、日志、列表 | 很高 | 是否需要全部进入上下文 |

这张表是学习用建模，不是 Cursor 的完整内部 schema。官方自报成本改善属于其流量与系统配置，不能直接当作其他产品的收益预测。

### 动态工具与文件读取

Cursor 说明保留高频读写、检索和 Shell 工具，低频能力在需要时加载。对于 Read 输出，博客介绍只在每十行提供行号以减少重复开销。每项变化都评估质量、成本、时延和工具错误。<sup><a href="#cite-3">[3]</a></sup>

这是很好的小实验模板：一次只改一项上下文格式，用真实引用任务检查行号精度与最终内容。不要在只看到 token 下降时，就认为工程效果一定改善。

## Cursor Router：质量与成本来自真实任务分布

8 月的 Router 博客描述两阶段选择：Compass 先判断当前 turn 是否值得升级，再按 domain、task、modifier 选择更适合的前沿模型。它把 API 单价与实际 tokens 结合，并把模型切换造成的 cache miss 成本纳入数据。<sup><a href="#cite-5">[5]</a></sup>

这比“总用最便宜模型”细致，因为一次低质量回答可能造成额外检索、重写、用户纠正和重新缓存。路由也不能只依赖公开 benchmark：当前任务的上下文、工具和执行环境与 benchmark 不同。

官方把用户下一步行为作为满意度信号，例如纠正负面、转向新任务正面。**这类行为是 proxy，不能直接等同准确率。** 学习时应结合最终状态、人工审查与实际完成结果，尤其用户沉默可能意味着满意，也可能意味着放弃。

## 执行位置与远程控制不是同一件事

Cursor 10 月 6 日 Remote Control 公告明确，本地 Agent 仍在用户电脑运行；手机只是连接它，电脑需要保持开机在线。**远程观察不会自动把任务迁移到云端。**<sup><a href="#cite-1">[1]</a></sup>

9 月 Self-Hosted Machines 则描述自有机器上的 worker 与 Cursor 云端 Harness 建立向外 HTTPS 连接，工具执行在用户环境，推理与规划仍在云端。工具输出仍可能回传代码和数据，因此“执行自托管”不能等同“所有数据只留本地”。<sup><a href="#cite-6">[6]</a></sup>

| 模式 | 执行环境 | 规划 / 推理 | 客户端关闭后 |
|---|---|---|---|
| 本地 Agent + Remote Control | 用户电脑 | 按产品模型服务路径 | 依赖电脑仍然运行 |
| Cursor-hosted cloud agent | 云端专用 VM | Cursor 云端 | 云任务继续 |
| Self-hosted execution worker | 自有机器 / worker pool | Cursor 云端 | 取决于 worker 生命周期与恢复设置 |

对基础设施学习者，worker 队列、空闲回收、snapshot、复用工作区、取消与迟到工具结果都是值得继续追的实现问题。公开博客给出机制方向，没有提供完整保证。

## Devin：多个智能贡献者与一个写者

2026 年 4 月 Walden Yan 的博客更新了早期对 multi-agent 的看法，指出已有价值的模式往往是 **多个 Agent 贡献检索、计划或 review，写入仍由一个主要执行者控制**。共享代码会产生隐含风格、边界和设计决策，多写者更容易碎片化。<sup><a href="#cite-7">[7]</a></sup>

### 独立 review 上下文

博客描述 coding agent 与 review agent 迭代，并发现 review 使用干净上下文可以重新检查实现，而不被原先路线牵引。主 Agent 仍需结合用户目标筛选建议，防止不相关修改或无限往返。<sup><a href="#cite-7">[7]</a></sup>

这个模式不要求两个不同厂商模型才能成立。重要变量是任务、上下文、工具、验收标准和权限。是否有收益应通过新发现的真实缺陷、误报、返工与总成本验证。

### Smart Friend 的失败也是学习资料

Cognition 公开了让小模型按需咨询强模型的实验：过弱的主模型可能不知道何时求助、也不知道提供什么上下文，最终质量受主模型限制。文章同时指出，在强模型之间按能力互补咨询更有效。<sup><a href="#cite-7">[7]</a></sup>

这提醒学习者，路由收益依赖 **升级决策是否可靠**。不能仅计算“便宜主模型 + 少量贵模型咨询”的理论账单。应把漏升级、错误问题、上下文遗漏和反复咨询算进评测。

## Devin：云任务要跨越异步空档

4 月云 Agent 工程博客描述开发任务的真实间隙：开 PR、等 CI、等 review、回复意见、再次执行。Cognition 的公开方案是 VM 状态快照、空闲停止、事件到来后恢复，以及调度、身份和集成。<sup><a href="#cite-8">[8]</a></sup>

博客对容器局限的表述带有产品立场。工程上应更精确地区分“进程内全部状态”“文件检查点”“外部事件日志”与“整机快照”。容器加持久存储 / 外部日志也可实现某些恢复语义；VM 快照更擅长保留机器状态，但并非任何 Agent 都必须采取相同架构。Anthropic 的 Session / Harness / Sandbox 解耦提供另一种公开参照。<sup><a href="#cite-8">[8]</a></sup><sup><a href="#cite-9">[9]</a></sup>

## 验证应返回能检查的证据

5 月 Devin verification 博客介绍测试前先读取代码、写 grounded test plan，执行时在动作前记录预期，再产生标注截图、断言和有章节的视频。可复用的 setup 被保存为测试 Skill，以减少重复和不稳定。<sup><a href="#cite-10">[10]</a></sup>

博客也明确两个失败点：截图可能错过短暂状态；Agent 可能用 JavaScript 直接制造结果而未真正完成用户路径。**“最终状态存在”和“真实用户能走通”是不同验收维度。** 对重要 UI 修改，两者都可能需要。

6 月 FrontierCode 进一步将验收扩展为行为正确、回归安全、构建和格式、测试有效性、范围与代码质量；reverse-classical 检查让新测试在旧错误代码上应失败。这里应学习 rubric 与验证方法，不直接沿用数月前模型分数排名。<sup><a href="#cite-11">[11]</a></sup>

## 官方材料阅读清单

| 材料 | 价值 | 阅读时做什么 |
|---|---|---|
| Cursor Improved token efficiency | 缓存与提示组织 | 标出 stable / dynamic 各层 |
| Cursor Router | 真实任务成本路由 | 列出 proxy 与真正 outcome 的区别 |
| Self-Hosted Machines | 混合执行架构 | 标出代码、工具结果与凭据的数据流 |
| Multi-Agents: What's Actually Working | 正反实践 | 记录成功前提与失败原因 |
| What We Learned Building Cloud Agents | 异步开发基础设施 | 对照日志恢复与整机快照 |
| Verifying Agentic Development at Scale | 测试与证据交付 | 设计 grounded test plan |
| Introducing FrontierCode | 新评测方法 | 将范围与有效测试纳入 rubric |

## 可动手验证的三个练习

1. **上下文与缓存**：为同一只读仓库问答构建稳定前缀与动态前缀两个版本。检查输入 / cached tokens、引用准确性、任务回合和真实费用，不只看提示词长度。
2. **单写者 + review**：主 Agent 在实验仓库修改一个小功能，review Agent 只读 diff 与相关代码。记录有效缺陷、误报、超范围建议与终止原因，限制迭代轮数。
3. **可验证产物**：修改一个表单验证规则，写明动作、预期状态和断言；分别用 UI 路径与结果状态验证。报告通过、失败和未测试，而不是一段笼统“已验证”。

这三项是学习实验设计，本次未运行付费产品，不填写估计的性能与成本数据。

## 更新记录与证据边界

- 2026-10-13：核实 Cursor 10 月 Remote Control 与 9 月工程文章，补 Devin 多 Agent、云任务与验证材料。
- 未核实 Devin 在 10 月的全部版本变化，官方博客目录不能视作完整 changelog。
- Cursor / Devin 核心 Harness 没有完整源码审计；厂商数字未经独立复测。
- 对于云、自托管、容器 / VM 等架构选择，保留适用条件，不将厂商产品路线写成行业唯一结论。

<footer><div class="sources">
<h2 id="sources">来源与证据说明</h2>
<ol>
<li id="cite-1"><a href="https://cursor.com/changelog/remote-control-local-agents">Cursor · Remote control for local agents</a><span class="source-meta">2026-10-06 · 官方全文已读取 · 明确运行仍在本地电脑</span></li>
<li id="cite-2"><a href="https://cursor.com/blog/rollouts-and-security-reviewer">Cursor · Bots for the last mile: Rollouts, Security Review</a><span class="source-meta">2026-09-23 · 官方全文已读取 · 功能与 coming soon 分开</span></li>
<li id="cite-3"><a href="https://cursor.com/blog/improved-token-efficiency">Cursor · Improved token efficiency for longer agent runs</a><span class="source-meta">2026-09-23 · 官方工程全文已读取 · 流量测量为厂商自报</span></li>
<li id="cite-4"><a href="https://cognition.ai/blog">Cognition 官方博客目录</a><span class="source-meta">2026-10-13 读取 · 当前抓取目录内容不能证明 10 月完整更新</span></li>
<li id="cite-5"><a href="https://cursor.com/blog/how-cursor-router-works">Cursor · How Cursor Router chooses the right model for the task</a><span class="source-meta">2026-08-06 · 官方工程全文已读取 · 用户满意度为行为 proxy</span></li>
<li id="cite-6"><a href="https://cursor.com/blog/self-hosted-machines">Cursor · Run cloud agents on machines you manage</a><span class="source-meta">2026-09-02 · 官方架构全文已读取 · 工具执行与云推理分开</span></li>
<li id="cite-7"><a href="https://cognition.ai/blog/multi-agents-working">Cognition · Multi-Agents: What's Actually Working</a><span class="source-meta">2026-04-22 · 官方工程全文已读取 · 保留 Smart Friend 的失败条件</span></li>
<li id="cite-8"><a href="https://cognition.ai/blog/what-we-learned-building-cloud-agents">Cognition · What We Learned Building Cloud Agents</a><span class="source-meta">2026-04-23 · 官方产品工程全文已读取 · 容器 / VM 表述需按语义判断</span></li>
<li id="cite-9"><a href="https://www.anthropic.com/engineering/managed-agents">Anthropic · Scaling Managed Agents</a><span class="source-meta">2026-04-08 · 独立厂商架构参照 · 已读取</span></li>
<li id="cite-10"><a href="https://cognition.ai/blog/testing-development">Cognition · Verifying Agentic Development at Scale</a><span class="source-meta">2026-05-29 · 官方工程全文已读取 · 包含验证失败案例</span></li>
<li id="cite-11"><a href="https://cognition.ai/blog/frontier-code">Cognition · Introducing FrontierCode</a><span class="source-meta">2026-06-08 · 原始评测方法全文已读取 · 不将旧分数当最新排名</span></li>
</ol>
</div></footer>
