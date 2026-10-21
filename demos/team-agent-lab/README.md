# Team Agent Lab 0.1.0

一个可在本机运行的**多智能体编排机制模拟器**，以及可选的回环模型适配器。不是 Claude Code Agent Teams 的复刻，也不依赖 OpenAI Agents SDK 或 xAI 托管服务。

任务是评审仓库自带的虚构 Helios 发布包：实现分析、测试分析两位 worker 提取带原文引用的证据，reviewer 检查，synthesizer 写评审单。样例的正确边界是：只允许隔离生产写能力的只读 shadow；生产写入所需去重与恢复测试尚不具备。不会执行部署、发送消息或读取用户目录。

必须分开两个轴：

| 执行单元 | 控制流 | 本工程 |
|---|---|---|
| 规则 / mock | 代码规定 | 默认模式，验证调度和合同，没有 LLM 推理 |
| 真实模型 | 代码规定的阶段 + 有界模型决策 | 可选 local 模式；模型选择 worker 资料、分析、复核、修订和生成 |
| 真实模型 | 自由动态规划 | 未实现；不能由本 demo 推断其效果 |

固定代码编排的模型团队仍可以是多 Agent 系统。这个工程的外层图、两个 worker 槽位、权限和上限由代码规定，不支持任意生成新角色；local 模式的实际内容与有界分配来自模型，失败时不会偷偷切回 mock。

## 取得与运行

需要 Python **3.9+**，无第三方依赖，不需要密钥。Python 3.9.6 / 3.12.13 已用于本工程验证。

```sh
git clone https://github.com/YuzheZhou2000/agent-fieldnotes.git
cd agent-fieldnotes/demos/team-agent-lab
python3 run.py run --mode parallel
python3 -m unittest discover -s tests -v
```

若使用虚拟环境：

```sh
python3 -m venv --without-pip .venv
# macOS / Linux；Windows 用 .venv\Scripts\python.exe
.venv/bin/python run.py run --mode compare
.venv/bin/python -m unittest discover -s tests -v
```

`requirements.txt` 只有标准库说明，无需 pip install。HTTP 测试会短暂绑定 `127.0.0.1` 随机端口；严格禁止 socket 的执行器需在允许回环通信的本机环境运行完整测试，不能将无法启动服务器当作通过。

## 看懂第一轮输出

`run` 输出 JSON 数组，每项包含 `run_id`、`status`、`validated`、调用预留数、最高在途数和 `candidate_sha256`。正常团队是：

```text
status: awaiting_approval     # 分析完成，尚未批准本地发布
validated: true              # 通过这个固定样例的检查，不是通用事实证明
calls_reserved: 5            # planner + 2 workers + reviewer + synthesizer
peak_active_calls: 2         # parallel 的两个 worker 请求发生重叠
reported_usage: null         # mock 不伪造 token 用量
```

所有产物只写进本目录忽略的 `runs/<run_id>/`：

| 文件 | 用途 |
|---|---|
| `manifest.json` | 版本、输入哈希、模式、状态、实际时间和预算统计 |
| `events.jsonl` | 单 owner 排序的事件流，含逻辑 call ID、attempt 与关联哈希 |
| `inputs.json` | 每次逻辑调用的实际业务 payload：任务、证据与反馈；重试复用同一逻辑输入，local 的固定系统指令见 `backends.SCHEMAS` |
| `artifacts.json` | 通过结构 / 引用检查的产物及修订号，单写者 blackboard |
| `candidate.json` | 通过最终固定样例 grader 的候选；失败时不存在 |
| `report.json` | 只有明确批准后才创建，含批准哈希与报告 |

这些是运行末尾保存的教学审计文件，**不实现崩溃恢复、checkpoint replay 或跨进程事务**。`events.jsonl` 也不是模型完整推理链。运行中进程被直接杀死时，不能承诺保存全部事件。

## 先审阅，再按哈希批准

先打开本轮 `candidate.json`、`inputs.json` 和 `events.jsonl`。用输出中的值替换下列占位符：

```sh
python3 run.py approve RUN_ID --hash CANDIDATE_SHA256
```

它只在该 run 下创建 `report.json`，不联网、不运行模型、不部署。相同哈希重复批准返回 `already_published`；改动候选、输入快照标识不匹配或哈希错误会拒绝。模型给出的 `approved: true` 只是内容复核，不是人的授权。这是单用户本地教学审批，不是抗恶意本机用户的签名或权限服务。

## 三种对照

```sh
python3 run.py run --mode compare --max-calls 8 --latency-ms 40
python3 run.py run --mode single --single-turns 1
```

- `single`：同一 generalist 连续 5 轮看全部证据和前一候选，最后用相同 grader 检查。可用 `--single-turns 1` 另建最小基线。
- `sequential`：planner、两个 worker、reviewer、synthesizer 相同合同，worker 顺序执行。
- `parallel`：同一团队合同，只有独立 worker 使用 `asyncio.gather` 并行。

默认三组各 5 次调用、同样的 8 次**尝试上限**。single 输入会重复携带原始资料，团队也有计划、交接和复核成本；这不是严格等 token、等 FLOPs 或等费用实验。顺序 / 并行团队才主要隔离调度差异。mock 每次人为 `sleep(40ms)`，时间差只展示关键路径；不能据此宣称多模型推理更快或团队质量更高。`examples/verified-mock-summary.json` 是一次真实执行的**模拟调度记录**，不是模型 benchmark。

## 冲突、返工与失败练习

```sh
python3 run.py run --fault conflict
python3 run.py run --fault conflict --max-revisions 0
python3 run.py run --fault review_reject
python3 run.py run --fault transient
python3 run.py run --fault timeout --timeout 0.05
python3 run.py run --fault transient --retries 0
python3 run.py run --fault malformed
python3 run.py run --max-calls 4
python3 run.py run --cancel-after-ms 60 --latency-ms 40
python3 run.py run --deadline 0.02 --latency-ms 40
```

预期：`conflict` 首次让 validation 的结论为 `ready`，但原文说明恢复测试缺失。reviewer 返回带 `T2/P1` 证据的修订消息；主管只重跑 validation，再复核，最后生成候选，共 **7** 次调用。`inputs.json` 能看到修订前后收到的反馈，`artifacts.json` 保留该 worker 两个修订。

`transient` / `timeout` 仅在 validation 第一次请求模拟可重试故障，默认最多额外 1 次；通常总计 **6** 次尝试。结构错误不自动重试，持久拒绝只允许默认 1 轮修订。预算不足在派发前拦截；失败或取消不会继续解锁 synthesizer。失败退出码为 2，正常生成待批准候选为 0。对照命令只接受干净运行，故障练习单独运行。

故障注入只适用于 mock。生产写入不可以照抄这里的重试规则：本工程只有只读资料与内容生成，没有远端副作用；需要另看本站[服务化专题](../../posts/agent-operations.html)。

## 决策归属与代码路线

| 决策 / 术语 | 负责人 | 代码 |
|---|---|---|
| 外层 workflow、两个 worker 槽位、barrier/join | 代码 | `lab.pipeline`、`lab.workers` |
| 子任务资料与 focus / routing | mock 规则或本地 planner 模型提出；代码校验 | `gate.plan`、`MockBackend.complete` / `LocalBackend.complete` |
| 证据读取 tool | 代码白名单，无任意路径或 shell | `contracts.evidence` |
| worker 的分析与 reviewer 的具体反馈 | mock 规则或本地模型 | `complete` 各 stage；实际输入见 `inputs.json` |
| 是否启动有界修订 | reviewer 提案 + 主管检查轮数和目标 | `contracts.review`、`lab.pipeline` |
| 重试、取消、deadline、调用预算 | 代码 | `Context.call`、`lab.run` |
| 原文引用 / 最终样例门槛 | 代码，不依赖 reviewer 权威 | `contracts.findings`、`contracts.report` |
| 本地发布 | 人明确提交哈希，代码比对 | `lab.approve` |

本工程是 delegation / return 模式：主管始终拥有控制权。reviewer → worker 是定向信息传递；没有持久 mailbox、自由同伴聊天或 SDK handoff。blackboard 由主管单独写入，模型只看到显式注入的快照；`Context` 不会自动变成共享模型记忆。

## 可选：自行启动的本地模型

本工程不会下载模型、安装推理服务、读取 API key 或调用云服务。先由你自行启动支持 `/v1/chat/completions`、非流式 JSON 对象输出的本地端点，再显式运行：

```sh
python3 run.py run --backend local \
  --base-url http://127.0.0.1:8000/v1 \
  --model YOUR_LOCAL_MODEL \
  --mode parallel --timeout 30 --deadline 120 \
  --max-calls 8 --max-output-tokens 1024
```

`YOUR_LOCAL_MODEL` 必须替换成服务已有模型名。请求包含 `response_format: {"type":"json_object"}`；服务或模型不支持时会明确失败，不会自动改成 mock。仅允许带端口的 HTTP loopback（127.*、localhost、::1），拒绝远程主机、URL 凭据、查询参数和重定向，忽略环境代理。回环地址只证明连接位置，不证明你启动的服务内部未代理到云端；自行确认它是离线本地推理。

local 模式实际向模型请求 plan、worker finding、review feedback、synthesis；模型返回的资料分配和文本会进入下一层。trace 保存的是实际输入 / 输出关联摘要，不是假装模型参与的固定答案外壳。程序仍约束两个槽位、允许资料、输出 schema、引用、预算和审批。

连接、读响应和总 run 都可取消客户端等待；取消连接不能保证服务端停止生成。没有 token usage 时保留未知；收到 usage 时只累计端点报告值，并用 `usage_complete` 提醒失败 / 取消尝试可能未结算。没有价格和 FLOPs 估计。

**验证边界：本轮没有启动或请求真实本地 LLM。** 16 项测试中的回环 HTTP stub 证明请求格式、模型返回值传递、分工变化、分块响应、超时和失败边界；它不能证明真实模型能遵守 schema、理解材料或正确修订。首次 local 运行可能合法失败，应检查证据与日志，而不是放宽验收伪造成功。

## 局限与下一步

这个固定样例 grader 检查原文精确引用、必要证据与已知正确决策，不能一般性判断所有解释是否被证据支持。reviewer 可能和 worker 共同犯错；“另一个角色说同意”不构成安全边界。默认 mock 输出与 fixture 是人工设计的，只能验证编排。

没有任意 shell、私密文件读取工具、自由网络检索、动态创建角色、持久任务队列、分布式锁、重放恢复或生产权限服务。重试保留逻辑调用 ID、接受结果由单一 owner 去重，不等于模型只运行一次或端到端 exactly-once。拓展前先固定更大的独立任务集、强单 Agent 基线、真实用量与失败归因。

完整术语、官方机制差别、结构图与日志 walkthrough 见[站内实战教程](../../posts/team-agent-lab.html)，研究证据与选型边界见[团队协作综述](../../posts/agent-teams.html)。
