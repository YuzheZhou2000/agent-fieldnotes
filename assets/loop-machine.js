/* Deterministic teaching model. No network, storage, timers or model calls. */
(function (root) {
  "use strict";
  const defaults = Object.freeze({budget: 12, retries: 1, approval: true, scenario: "success"});
  const scenarios = ["success", "transient", "lost_committed", "lost_uncommitted", "permanent"];
  const terminal = state => ["succeeded", "failed", "cancelled", "exhausted"].includes(state.status);
  const allowed = state => terminal(state) ? [] : [
    ...(["ready", "deciding", "executing", "retry_wait", "verifying"].includes(state.status) ? ["next"] : []),
    ...(state.status === "approval" ? ["approve", "deny"] : []),
    ...(state.status === "unknown" ? ["reconcile"] : []), "cancel"
  ];
  function create(config = defaults) {
    const c = {...defaults, ...config};
    if (!Number.isInteger(c.budget) || c.budget < 1 || c.budget > 40) throw new Error("总预算须为 1–40 的整数。");
    if (!Number.isInteger(c.retries) || c.retries < 0 || c.retries > 3) throw new Error("额外重试须为 0–3 的整数。");
    if (typeof c.approval !== "boolean" || !scenarios.includes(c.scenario)) throw new Error("请选择有效场景与审批选项。");
    return {config: Object.freeze(c), status: "ready", spent: 0, attempts: 0, writes: 0, knownEffect: false, events: [{status: "ready", text: "固定目标：登记 DEMO-001 / verified，并独立读取验收。", spent: 0, attempts: 0}]};
  }
  function transition(previous, event) {
    if (!allowed(previous).includes(event)) return previous;
    const s = {...previous, events: [...previous.events]};
    const log = text => s.events.push({status: s.status, text, spent: s.spent, attempts: s.attempts});
    const move = (status, text) => { s.status = status; log(text); };
    const pay = cost => {
      if (s.spent + cost > s.config.budget) {
        move("exhausted", `剩余预算不足以支付下一动作的 ${cost} 单位。停止调度，保留既有写入与未知项。`);
        return false;
      }
      s.spent += cost;
      return true;
    };
    if (event === "cancel" || event === "deny") {
      move("cancelled", event === "deny" ? "此固定写动作被拒绝，没有派发工具。" : "取消后续调度；已写入的记录不回滚，未核对的结果仍未知。");
      return s;
    }
    if (event === "approve") {
      move("executing", "批准 DEMO-001 / verified 的固定参数；等待推进以派发工具。");
      return s;
    }
    if (event === "reconcile") {
      if (!pay(1)) return s;
      s.knownEffect = s.writes === 1;
      move(s.knownEffect ? "verifying" : "retry_wait", s.knownEffect ? "独立核对确认记录已存在，无需再次写入，进入验收。" : "独立核对确认没有写入；进入受限重试判断。");
      return s;
    }
    switch (s.status) {
      case "ready":
        if (pay(2)) move("deciding", "付出 2 单位形成固定写入意图；意图尚未执行。");
        break;
      case "deciding":
        move(s.config.approval ? "approval" : "executing", s.config.approval ? "写入需要批准，等待人对当前固定动作作决定。" : "当前合同允许此固定写入；等待推进派发。");
        break;
      case "executing": {
        if (!pay(3)) break;
        s.attempts++;
        const first = s.attempts === 1;
        if (s.config.scenario === "permanent") move("failed", "参数或权限类永久失败；确认未写入，不进行盲目重试。");
        else if (first && s.config.scenario === "transient") move("retry_wait", "模拟明确未写入的暂时失败；下一步检查重试限额。");
        else if (first && s.config.scenario.startsWith("lost_")) {
          s.writes = s.config.scenario === "lost_committed" ? 1 : 0;
          s.knownEffect = null;
          move("unknown", "响应丢失。仅凭超时不能判断是否写入；直接重试被禁用，请先核对。");
        } else {
          s.writes = 1;
          s.knownEffect = true;
          move("verifying", "收到写入确认，但尚未独立验收。下一步读取记录并检查约束。");
        }
        break;
      }
      case "retry_wait":
        if (s.attempts > s.config.retries) move("failed", "重试限额已用完；没有派发下一次工具尝试。");
        else move("executing", "满足重试限额且已确认未写入；保持原动作与审批范围，等待再次派发。");
        break;
      case "verifying":
        if (pay(2)) move("succeeded", "独立读取确认工单、字段与唯一记录符合本教学合同，验收成功。");
        break;
    }
    return s;
  }
  root.FieldnotesLoop = Object.freeze({defaults, scenarios: Object.freeze(scenarios), create, transition, terminal, allowed});
})(globalThis);
