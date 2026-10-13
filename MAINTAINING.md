# Agent Fieldnotes 维护约定

博客面向专业 Agent 工程师，主分类按技术问题组织，厂商作为案例来源和次级标签。文章源文在 `content/`，模板在 `templates/`，生成网页在 `posts/`，首页为 `index.html`。

## 选题与内容

采用五个稳定方向：运行时与状态、记忆与上下文、工具与协议、权限与安全、评测与交付。系统设计综述归入评测与交付，用跨方向链接提供入口。若一篇覆盖多个方向，选择主要技术问题作为 `topic`，其余用标签与正文链接表达。

新文章先回答一个具体失败或决策：机制如何工作、接口怎样划分、增加了什么成本、评测证明了什么、在什么条件下适用、还没有证明什么。保留有价值的产品披露，但不以发布清单代替技术分析。

资料必须使用一手论文、作者项目或官方技术文档。来源处写原始发布日期、论文版本或代码 commit、核查日、阅读范围和复现状态。滚动文档若未给独立发布日期，注明滚动文档，不能把核查日当发布日期。

作者实验、独立复现、厂商披露与工程推导分别标注。百分比与百分点、延迟与费用、单 episode 与跨任务状态不能混用。跨模型、Harness、任务集、资源或 grader 的分数不能拼成统一排名。未执行的训练、模型请求和建议实验不得标成已复现。

## 生成与检查

`content/*.md` 使用 JSON frontmatter：`slug`、`title`、`topic`、`summary`、`order`、`updated`、`tags`、`minutes`。`order` 是稳定笔记编号，`minutes` 是阅读时间估计；来源列表使用 `cite-N`，引用指向同一篇的来源 ID。

```sh
npm ci --ignore-scripts
npm run build
npm run check
```

`scripts/build.mjs` 用锁定版本的 Markdown renderer 生成全部文章、首页、导航、方向计数、阅读链和离线全文搜索。首页布局在 `templates/index.html`，文章布局在 `templates/post.html`，本地 SVG 缩略图在 `templates/thumbnails.json`。不要直接编辑生成的 HTML 或搜索索引。

`npm run check` 检查生成结果是否过期、JavaScript 语法、本地链接、锚点、唯一 ID、分类与元数据一致性、旧锚点和离线资源。修改交互或布局后，还应在浏览器验证分类与多词全文搜索、空结果、旧学习进度、标记/撤销、主题、代码复制，以及桌面/手机宽度。建议同时通过 `file://` 检查离线阅读。

## 兼容策略

保留原有 `posts/openai.html`、`claude.html`、`gemini.html`、`muse.html`、`coding-agents.html` 和 `agent-engineering.html`，这些 slug 也是学习进度键；标题和技术分类可以更新，路径不随厂商标签迁移。

`templates/heading-ids.json` 保留初版八篇文章的标题→锚点映射。修改标题时应迁移映射或提供旧 ID，不能默默破坏外部片段链接。新标题使用稳定内容哈希生成锚点。学习进度仍在 `fieldnotes-progress`，主题仍在 `fieldnotes-theme`，均只保存在当前浏览器，不上传到服务端。

## 发布

静态产物与源文一同提交 main，复用仓库现有 GitHub Pages 流程。推送前检查远端是否前进，保留已有工作区改动，不强推。推送后确认远端 SHA 和该提交的 Pages 构建/部署状态，不新增独立部署。
