# Agent Fieldnotes

面向专业 Agent 工程师的中文技术博客，以机制、实现取舍、评估证据、适用条件和局限组织内容。

主分类：运行时与状态 · 记忆与上下文 · 工具与协议 · 权限与安全 · 评测与交付。厂商与框架作为实现案例和次级标签。

GitHub Pages 继续使用 `main` 分支根目录的 `index.html`。网页资源全部本地化，支持离线全文搜索、方向筛选、主题切换和浏览器内学习进度。

本地维护（Node.js 20+、Python 3）：

```sh
npm ci --ignore-scripts
npm run build
npm run check
python3 -m http.server 8000
```

在浏览器打开 `http://localhost:8000`。发布所需静态文件已提交，Pages 不需要运行 Node.js。

学习入口：[全流程地图](learn.html) · [执行循环基础](posts/agent-loop.html) · [上下文与检索](posts/context-retrieval.html) · [服务化与故障处置](posts/agent-operations.html) · [执行循环实验室](tools/loop-lab.html)。地图区分已有专题与待补方向；工具是确定性教学模拟，不调用模型或外部服务。

文章源文在 `content/`；路线数据在 `content/learning-path.json`，页面在 `templates/`。`npm run check` 同时运行无依赖的状态机边界测试。生成约定、来源规范及旧链接兼容策略见 [MAINTAINING.md](MAINTAINING.md)。
