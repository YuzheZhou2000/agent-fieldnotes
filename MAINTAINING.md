# Agent Fieldnotes 维护约定

博客面向专业 Agent 工程师，主分类按技术问题组织，厂商作为案例来源和次级标签。文章源文在 `content/`，模板在 `templates/`，生成网页在 `posts/`，首页为 `index.html`。

## 选题与内容

采用五个稳定方向：运行时与状态、记忆与上下文、工具与协议、权限与安全、评测与交付。系统设计综述归入评测与交付，用跨方向链接提供入口。若一篇覆盖多个方向，选择主要技术问题作为 `topic`，其余用标签与正文链接表达。

新文章先回答一个具体失败或决策：机制如何工作、接口怎样划分、增加了什么成本、评测证明了什么、在什么条件下适用、还没有证明什么。保留有价值的产品披露，但不以发布清单代替技术分析。

资料必须使用一手论文、作者项目或官方技术文档。来源处写原始发布日期、论文版本或代码 commit、核查日、阅读范围和复现状态。滚动文档若未给独立发布日期，注明滚动文档，不能把核查日当发布日期。

基础教程与近期发布案例分开维护。优先跟踪 Anthropic、OpenAI、xAI 的官方博客、研究及技术文档，提炼可复用机制；其他一手论文与公开实现按问题选用，不按厂商分配篇幅。

作者实验、独立复现、厂商披露与工程推导分别标注。百分比与百分点、延迟与费用、单 episode 与跨任务状态不能混用。跨模型、Harness、任务集、资源或 grader 的分数不能拼成统一排名。未执行的训练、模型请求和建议实验不得标成已复现。

有实质更新时，可随同发布提交 `research/YYYY-MM-DD.md`，记录基线、来源日期、采用理由、未采用线索与读取限制，供下一次去重；无重要增量时不为核查记录单独制造提交。

## 生成与检查

`content/*.md` 使用 JSON frontmatter：`slug`、`title`、`topic`、`summary`、`order`、`updated`、`tags`、`minutes`。`order` 是稳定笔记编号，`minutes` 是阅读时间估计；来源列表使用 `cite-N`，引用指向同一篇的来源 ID。

长篇指南可设置可选字段 `collapsibleToc: true`，以可展开目录保留全部章节与题目锚点，避免手机阅读时目录占据过长的首段空间。资料核查日使用 `updated`，网站发布日可另记为 `published`，不能将发布日当作重新研究的日期。

```sh
npm ci --ignore-scripts
npm run build
npm run check
```

`scripts/build.mjs` 用锁定版本的 Markdown renderer 生成全部文章、首页、导航、方向计数、阅读链和离线全文搜索。首页布局在 `templates/index.html`，文章布局在 `templates/post.html`，本地 SVG 缩略图在 `templates/thumbnails.json`。不要直接编辑生成的 HTML 或搜索索引。

`content/learning-path.json` 维护全流程学习地图，`available` 表示存在专题入口，`planned` 表示尚无独立专题。每一站要写清学习目标、已有文章、练习和待补项，不用百分比暗示内容完整；新增文章也应加入路线。`learn.html` 与 `tools/loop-lab.html` 由模板生成。

执行循环实验室的规则在 `assets/loop-machine.js`，界面在 `assets/loop-lab.js`；纯客户端，不调用模型或外部接口，不持久化实验。`npm test` 验证预算、审批、未知副作用、取消、重试与所有配置的有界终止，并包含在 `npm run check`。修改规则时同步页面成本、假设与练习；不要将教学单位当成价格或真实模型测量。

`demos/team-agent-lab/` 是 Python 3.9+ 标准库本地实战工程，默认 mock；`npm run check` 包含其 unittest，HTTP 协议测试只使用本机回环 stub。改动要同步 README、教程、fixture 合同与测试；模拟延迟、协议 stub 和真实模型实验分开记录。运行产物在忽略的 `runs/`，不要提交用户的本地日志或凭据。可选 local 模式不得默认下载模型、放开任意文件 / shell 或使用云 API。

`npm run check` 检查生成结果是否过期、JavaScript 语法、本地链接、锚点、唯一 ID、分类与元数据一致性、旧锚点和离线资源。修改交互或布局后，还应在浏览器验证分类与多词全文搜索、空结果、旧学习进度、标记/撤销、主题、代码复制，以及桌面/手机宽度。建议同时通过 `file://` 检查离线阅读。

## 兼容策略

保留原有 `posts/openai.html`、`claude.html`、`gemini.html`、`muse.html`、`coding-agents.html` 和 `agent-engineering.html`，这些 slug 也是学习进度键；标题和技术分类可以更新，路径不随厂商标签迁移。

`templates/heading-ids.json` 保留初版八篇文章的标题→锚点映射。修改标题时应迁移映射或提供旧 ID，不能默默破坏外部片段链接。新标题使用稳定内容哈希生成锚点。学习进度仍在 `fieldnotes-progress`，主题仍在 `fieldnotes-theme`，均只保存在当前浏览器，不上传到服务端。

## 发布

静态产物与源文一同提交 main，复用仓库现有 GitHub Pages 流程。推送前检查远端是否前进，保留已有工作区改动，不强推。推送后确认远端 SHA 和该提交的 Pages 构建/部署状态，不新增独立部署。
