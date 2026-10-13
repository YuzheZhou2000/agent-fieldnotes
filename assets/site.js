(function () {
  "use strict";
  const storage = {
    read(key, fallback) {
      try { return JSON.parse(localStorage.getItem(key)) ?? fallback; }
      catch (_) { return fallback; }
    },
    write(key, value) {
      try { localStorage.setItem(key, JSON.stringify(value)); return true; }
      catch (_) { return false; }
    }
  };
  const theme = storage.read("fieldnotes-theme", null);
  if (theme === "light" || theme === "dark") document.documentElement.dataset.theme = theme;
  document.querySelector(".theme-button")?.addEventListener("click", () => {
    const dark = document.documentElement.dataset.theme === "dark" ||
      (!document.documentElement.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
    const next = dark ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    storage.write("fieldnotes-theme", next);
  });

  const savedProgress = storage.read("fieldnotes-progress", []);
  const completed = new Set(Array.isArray(savedProgress) ? savedProgress.filter(v => typeof v === "string") : []);
  const cards = Array.from(document.querySelectorAll(".card"));
  function refreshProgress() {
    cards.forEach(card => { card.querySelector(".learned-badge").hidden = !completed.has(card.dataset.slug); });
    const status = document.querySelector(".learning-status");
    if (status) {
      const count = cards.filter(card => completed.has(card.dataset.slug)).length;
      status.textContent = `学习进度 ${count} / ${cards.length}`;
    }
    document.querySelectorAll(".complete-button").forEach(button => {
      const done = completed.has(button.dataset.slug);
      button.setAttribute("aria-pressed", String(done));
      button.textContent = done ? "✓ 已学习 · 点击撤销" : "标记已学习";
    });
  }
  document.querySelectorAll(".complete-button").forEach(button => {
    button.addEventListener("click", () => {
      const slug = button.dataset.slug;
      if (completed.has(slug)) completed.delete(slug); else completed.add(slug);
      const persisted = storage.write("fieldnotes-progress", Array.from(completed));
      refreshProgress();
      if (!persisted) button.textContent += "（仅本次）";
    });
  });
  refreshProgress();

  let filter = "all";
  const searchInput = document.querySelector("#search");
  const searchIndex = new Map((window.FIELDNOTES_SEARCH || []).map(post => [post.slug, post.text]));
  function filterCards() {
    const terms = (searchInput?.value || "").trim().toLowerCase().split(/\s+/).filter(Boolean);
    let count = 0;
    cards.forEach(card => {
      const haystack = searchIndex.get(card.dataset.slug) || card.textContent.toLowerCase();
      const show = (filter === "all" || card.dataset.topic === filter) && terms.every(term => haystack.includes(term));
      card.hidden = !show;
      if (show) count++;
    });
    const label = document.querySelector("#result-count");
    if (label) label.textContent = `${count} 篇文章`;
    const empty = document.querySelector(".empty-state");
    if (empty) empty.hidden = count !== 0;
  }
  searchInput?.addEventListener("input", filterCards);
  function selectFilter(topic) {
    filter = topic;
    document.querySelectorAll("[data-filter]").forEach(button => {
      button.setAttribute("aria-pressed", String(button.dataset.filter === topic));
    });
    filterCards();
  }
  document.querySelectorAll("[data-filter]").forEach(button => {
    button.addEventListener("click", () => selectFilter(button.dataset.filter));
  });
  document.querySelectorAll("[data-choose-topic]").forEach(link => {
    link.addEventListener("click", event => {
      event.preventDefault();
      if (searchInput) searchInput.value = "";
      selectFilter(link.dataset.chooseTopic);
      document.querySelector("#library")?.scrollIntoView();
    });
  });

  document.querySelectorAll(".prose pre:not(.mermaid)").forEach(pre => {
    const code = pre.querySelector("code");
    if (!code) return;
    const button = document.createElement("button");
    button.className = "copy-button";
    button.type = "button";
    button.textContent = "复制代码";
    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(code.textContent);
        button.textContent = "已复制";
      } catch (_) {
        const range = document.createRange();
        range.selectNodeContents(code);
        const selection = window.getSelection();
        selection.removeAllRanges();
        selection.addRange(range);
        button.textContent = "已选中 · 手动复制";
      }
    });
    pre.prepend(button);
  });
  document.querySelector(".print-button")?.addEventListener("click", () => window.print());

  const explanations = {
    accepted: "Accepted：记录目标、授权范围和幂等键。任务状态持久化，页面关闭不应导致任务消失。",
    running: "Running：Harness 组装上下文、调用模型和工具。每次工具调用都要有独立标识、状态与可追溯结果。",
    approval: "Awaiting approval：存储待执行动作与参数。批准后恢复原会话，避免在恢复时重新猜测动作。",
    recovering: "Recovering：从事件日志和工作区检查点恢复。先查外部动作是否已经生效，再决定能否重试。",
    verified: "Verified：检查产物与最终环境状态，记录已通过、失败及未测试项目。模型说完成只是一个信号。"
  };
  document.querySelectorAll(".lifecycle [data-state]").forEach(button => {
    button.addEventListener("click", () => {
      const parent = button.closest(".lifecycle");
      parent.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", String(b === button)));
      parent.querySelector(".lifecycle-output").textContent = explanations[button.dataset.state];
    });
  });
  if (document.querySelector(".article-page")) {
    const updateReading = () => {
      const height = document.documentElement.scrollHeight - innerHeight;
      document.querySelector(".reading-line").style.width = `${height > 0 ? Math.min(100, scrollY / height * 100) : 0}%`;
    };
    addEventListener("scroll", updateReading, { passive: true });
    updateReading();
    if ("IntersectionObserver" in window) {
      const links = Array.from(document.querySelectorAll(".toc a"));
      const observer = new IntersectionObserver(entries => {
        entries.filter(entry => entry.isIntersecting).forEach(entry => {
          links.forEach(link => link.classList.toggle("active", decodeURIComponent(link.hash.slice(1)) === entry.target.id));
        });
      }, { rootMargin: "-10% 0px -70% 0px" });
      document.querySelectorAll(".prose h2, .prose h3").forEach(heading => observer.observe(heading));
    }
  }
})();
