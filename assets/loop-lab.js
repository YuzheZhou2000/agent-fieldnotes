(function () {
  "use strict";
  const app = document.querySelector("#loop-app");
  if (!app) return;
  const machine = globalThis.FieldnotesLoop;
  let run = machine.create();
  const labels = {ready: "准备 Ready", deciding: "决策 Deciding", approval: "等待审批 Awaiting approval", executing: "待执行 Ready to dispatch", retry_wait: "等待重试判断 Retry wait", unknown: "结果未知 Unknown", verifying: "等待独立验收 Verifying", succeeded: "验收成功 Succeeded", failed: "明确失败 Failed", cancelled: "已取消调度 Cancelled", exhausted: "预算耗尽 Exhausted"};
  const hints = {ready: "推进以支付一次决策成本。", deciding: "推进以检查本轮写入审批规则。", approval: "批准或拒绝当前固定动作，工具尚未派发。", executing: "推进会支付 3 单位并执行一次模拟写入尝试。", retry_wait: "推进会检查重试限额，尚不执行工具。", unknown: "先核对外部状态，再判断是否需要重试；取消后也不会自动确认结果。", verifying: "写入已确认；推进以支付 2 单位进行独立验收。", succeeded: "本轮已结束。可修改配置重新实验。", failed: "本轮已结束。失败不自动追加重试。", cancelled: "后续调度已停止。检查已确认写入和未确认结果。", exhausted: "下一动作没有执行。预算停止不等于任务成功或回滚。"};
  const stageOf = s => machine.terminal(s) ? "terminal" : ["unknown", "retry_wait"].includes(s.status) ? "checking" : s.status;
  const $ = selector => document.querySelector(selector);
  function render() {
    const focused = document.activeElement;
    $("#run-state").textContent = labels[run.status];
    $("#run-hint").textContent = hints[run.status];
    $("#run-budget").textContent = `${run.spent} / ${run.config.budget}`;
    $("#run-attempts").textContent = String(run.attempts);
    $("#run-effect").textContent = run.knownEffect === null ? "待核对" : run.knownEffect ? "1 条" : "0 条";
    $("#run-contract").textContent = `${run.config.approval ? "需审批" : "预授权"} · 重试 ≤ ${run.config.retries}`;
    $("#active-scenario").textContent = `本轮场景：${$("#scenario").querySelector(`option[value="${run.config.scenario}"]`).textContent}`;
    document.querySelectorAll("[data-stage]").forEach(node => {
      const current = node.dataset.stage === stageOf(run);
      node.classList.toggle("current", current);
      if (current) node.setAttribute("aria-current", "step"); else node.removeAttribute("aria-current");
    });
    document.querySelectorAll("[data-event]").forEach(button => { button.disabled = !machine.allowed(run).includes(button.dataset.event); });
    const fragment = document.createDocumentFragment();
    run.events.forEach(event => {
      const item = document.createElement("li"), heading = document.createElement("strong"), text = document.createElement("p");
      heading.textContent = `${labels[event.status]} · 用量 ${event.spent} · 尝试 ${event.attempts}`;
      text.textContent = event.text;
      item.append(heading, text); fragment.append(item);
    });
    $("#run-log").replaceChildren(fragment);
    if (focused?.matches("[data-event]") && focused.disabled) {
      (document.querySelector("[data-event]:not(:disabled)") || $("#lab-reset")).focus();
    }
  }
  function fields(config) {
    $("#budget").value = config.budget;
    $("#retries").value = config.retries;
    $("#approval").checked = config.approval;
    $("#scenario").value = config.scenario;
  }
  function error(message) {
    $("#config-error").hidden = !message;
    $("#config-error").textContent = message;
  }
  $("#lab-config").addEventListener("submit", event => {
    event.preventDefault();
    try {
      if (!$("#budget").value.trim() || !$("#retries").value.trim()) throw new Error("请填写总预算与额外重试次数。");
      const next = machine.create({budget: Number($("#budget").value), retries: Number($("#retries").value), approval: $("#approval").checked, scenario: $("#scenario").value});
      run = next; error(""); render();
    } catch (e) { error(e.message); }
  });
  $("#lab-reset").addEventListener("click", () => { run = machine.create(); fields(run.config); error(""); render(); });
  document.querySelectorAll("[data-event]").forEach(button => button.addEventListener("click", () => { run = machine.transition(run, button.dataset.event); render(); }));
  fields(run.config); render(); app.hidden = false;
})();
