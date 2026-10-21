"""Bounded teaching orchestrator. Python 3.9+, standard library only."""
from __future__ import annotations

import argparse
import asyncio
import json
import math
import re
import time
import uuid
from pathlib import Path

import contracts as gate
from backends import LocalBackend, MockBackend, RetryableError

VERSION = "0.1.0"
RUNS = gate.ROOT / "runs"


class BudgetError(Exception):
    pass


class ReviewRejected(Exception):
    pass


class Context:
    def __init__(self, backend, max_calls=8, retries=1, timeout=2):
        self.backend, self.max_calls, self.retries, self.timeout = backend, max_calls, retries, timeout
        self.started = time.monotonic()
        self.events, self.inputs, self.artifacts = [], {}, []
        self.calls = self.active = self.peak = 0
        self.usage = []
        self.fixture_sha256 = None

    def emit(self, event, **fields):
        self.events.append({"seq": len(self.events) + 1, "ms": round((time.monotonic() - self.started) * 1000, 3), "event": event, **fields})

    def accept(self, name, value):
        artifact = {"schema_version": 1, "fixture_sha256": self.fixture_sha256, "name": name, "revision": 1 + sum(x["name"] == name for x in self.artifacts), "sha256": gate.digest(value), "value": value}
        self.artifacts.append(artifact)
        self.emit("artifact_accepted", name=name, revision=artifact["revision"], sha256=artifact["sha256"])

    async def call(self, stage, payload, role):
        call_id = f"{role}.{len(self.inputs) + 1}"
        # Only this explicit payload reaches a backend. App context is not implicit model memory.
        payload = json.loads(gate.canonical(payload))
        self.inputs[call_id] = {"stage": stage, "role": role, "payload": payload}
        for attempt in range(1, self.retries + 2):
            # Single event-loop owner; no await between checking and reserving.
            if self.calls >= self.max_calls:
                self.emit("budget_blocked", call_id=call_id)
                raise BudgetError("attempt budget exhausted before dispatch")
            self.calls += 1
            self.active += 1
            self.peak = max(self.peak, self.active)
            self.emit("call_started", call_id=call_id, role=role, attempt=attempt, input_sha256=gate.digest(payload), calls_reserved=self.calls)
            try:
                reply = await asyncio.wait_for(self.backend.complete(stage, payload, attempt, self.timeout), self.timeout)
                self.usage.append(reply.usage)
                self.emit("call_finished", call_id=call_id, role=role, attempt=attempt, output_sha256=gate.digest(reply.data), usage=reply.usage)
                return reply.data
            except (asyncio.TimeoutError, RetryableError) as exc:
                self.usage.append(None)
                self.emit("call_retryable", call_id=call_id, role=role, attempt=attempt, reason=type(exc).__name__)
                if attempt > self.retries:
                    raise
            except asyncio.CancelledError:
                self.usage.append(None)
                self.emit("call_cancelled", call_id=call_id, role=role, attempt=attempt)
                raise
            finally:
                self.active -= 1
            self.emit("retry_scheduled", call_id=call_id, next_attempt=attempt + 1)
            await asyncio.sleep(.005 * attempt)


async def workers(ctx, data, tasks, mode, feedback=None):
    feedback = feedback or {}

    async def one(task):
        key = task["worker_id"]
        visible = gate.evidence(data, task["document_ids"])
        message = feedback.get(key)
        if message:
            # A message carries information, not publication permission.
            ctx.emit("message_delivered", sender="reviewer", recipient=key, evidence_ids=message["evidence_ids"])
            more = [x for x in gate.all_evidence(data) if x["id"] in message["evidence_ids"]]
            visible = list({x["id"]: x for x in visible + more}.values())
        ctx.emit("evidence_read", role=key, task_id=task["task_id"], document_ids=task["document_ids"], evidence_ids=[x["id"] for x in visible])
        result = await ctx.call("worker", {"task": task, "evidence": visible, "feedback": message}, key)
        return key, gate.findings(result, visible)

    if mode == "sequential":
        results = [await one(task) for task in tasks]
    else:
        pending = [asyncio.create_task(one(task)) for task in tasks]
        try:
            results = await asyncio.gather(*pending)
        except BaseException:
            for task in pending:
                task.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
            raise
    # All-success barrier; workers never concurrently mutate the blackboard.
    for key, value in results:
        ctx.accept(key, value)
    ctx.emit("join_passed", workers=[key for key, _ in results])
    return dict(results)


async def pipeline(ctx, data, mode, max_revisions, single_turns):
    if mode == "single":
        previous = None
        for turn in range(1, single_turns + 1):
            previous = await ctx.call("single", {"task": data["task"], "evidence": gate.all_evidence(data), "previous": previous, "turn": turn}, "generalist")
        result = gate.report(previous, data)
        ctx.accept("generalist", result)
        return result
    proposed = await ctx.call("plan", {"task": data["task"], "document_ids": list(data["documents"])}, "planner")
    tasks = gate.plan(proposed, data)
    ctx.accept("plan", {"tasks": tasks})
    findings = await workers(ctx, data, tasks, mode)
    for revision in range(max_revisions + 1):
        verdict = gate.review(await ctx.call("review", {"task": data["task"], "workers": findings, "evidence": gate.all_evidence(data)}, "reviewer"), data)
        ctx.accept("review", verdict)
        if verdict["approved"]:
            break
        if revision == max_revisions:
            raise ReviewRejected("bounded review loop rejected; synthesis remains locked")
        feedback = {x["worker_id"]: x for x in verdict["feedback"]}
        ctx.emit("revision_requested", workers=list(feedback), revision=revision + 1)
        revised = await workers(ctx, data, [task for task in tasks if task["worker_id"] in feedback], mode, feedback)
        findings.update(revised)
    result = gate.report(await ctx.call("synthesize", {"task": data["task"], "workers": findings, "review": verdict, "evidence": gate.all_evidence(data)}, "synthesizer"), data)
    ctx.accept("candidate", result)
    return result


async def run(backend, mode="parallel", max_calls=8, retries=1, timeout=2, deadline=10, cancel_after_ms=None, max_revisions=1, single_turns=5):
    if mode not in ("single", "sequential", "parallel"):
        raise gate.ContractError("unknown execution mode")
    for name, value, low, high in [("max_calls", max_calls, 1, 50), ("retries", retries, 0, 2), ("max_revisions", max_revisions, 0, 2), ("single_turns", single_turns, 1, 10)]:
        if type(value) is not int or not low <= value <= high:
            raise gate.ContractError(f"{name} outside supported bounds")
    for value in (timeout, deadline):
        if type(value) not in (int, float) or not math.isfinite(value) or not .01 <= value <= 120:
            raise gate.ContractError("timeout/deadline must be finite and between .01 and 120 seconds")
    if cancel_after_ms is not None and (type(cancel_after_ms) is not int or not 1 <= cancel_after_ms <= 120000):
        raise gate.ContractError("cancel-after-ms must be 1–120000")
    data = gate.packet()
    ctx = Context(backend, max_calls, retries, timeout)
    ctx.fixture_sha256 = gate.digest(data)
    ctx.emit("run_started", mode=mode, backend=backend.name, fixture_sha256=gate.digest(data), version=VERSION)
    work = asyncio.create_task(pipeline(ctx, data, mode, max_revisions, single_turns))

    async def cancel_later():
        await asyncio.sleep(cancel_after_ms / 1000)
        ctx.emit("cancel_requested")
        work.cancel()

    timer = asyncio.create_task(cancel_later()) if cancel_after_ms is not None else None
    candidate = None
    try:
        candidate = await asyncio.wait_for(work, deadline)
        status, error = "awaiting_approval", None
    except asyncio.CancelledError:
        status, error = "cancelled", "local scheduling cancelled; a local model server may still be computing"
    except asyncio.TimeoutError:
        status, error = "deadline", "call or run deadline exceeded; no candidate published"
    except (gate.ContractError, BudgetError, ReviewRejected, RetryableError) as exc:
        status, error = "failed", f"{type(exc).__name__}: {exc}"
    finally:
        if timer:
            timer.cancel()
            await asyncio.gather(timer, return_exceptions=True)
    ctx.emit("run_ended", status=status)
    usage = {key: sum(x[key] for x in ctx.usage if x) for key in ("prompt_tokens", "completion_tokens")}
    summary = {
        "version": VERSION, "mode": mode, "backend": backend.name, "status": status,
        "validated": candidate is not None, "error": error, "fixture_sha256": gate.digest(data),
        "calls_reserved": ctx.calls, "max_calls": max_calls, "peak_active_calls": ctx.peak,
        "elapsed_ms": round((time.monotonic() - ctx.started) * 1000, 3),
        "synthetic_delay_ms": getattr(backend, "latency_ms", None),
        "reported_usage": usage if any(ctx.usage) else None,
        "usage_complete": bool(ctx.usage) and len(ctx.usage) == ctx.calls and all(x is not None for x in ctx.usage),
    }
    return {"summary": summary, "candidate": candidate, "events": ctx.events, "inputs": ctx.inputs, "artifacts": ctx.artifacts}


def safe_runs(root):
    root = Path(root)
    if root.is_symlink():
        raise gate.ContractError("runs directory cannot be a symlink")
    root.mkdir(exist_ok=True)
    return root


def save(result, root=RUNS):
    root = safe_runs(root)
    run_id = uuid.uuid4().hex[:12]
    folder = root / run_id
    folder.mkdir(mode=0o700)
    summary = dict(result["summary"], run_id=run_id)
    candidate = result["candidate"]
    if candidate is not None:
        summary["candidate_sha256"] = gate.digest(candidate)
        (folder / "candidate.json").write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n")
    for filename, content in [("manifest.json", summary), ("inputs.json", result["inputs"]), ("artifacts.json", result["artifacts"])]:
        (folder / filename).write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n")
    (folder / "events.jsonl").write_text("".join(json.dumps(dict(x, run_id=run_id), ensure_ascii=False) + "\n" for x in result["events"]))
    return summary


def approve(run_id, candidate_hash, root=RUNS):
    if not re.fullmatch(r"[a-f0-9]{12}", run_id) or not re.fullmatch(r"[a-f0-9]{64}", candidate_hash):
        raise gate.ContractError("approve requires the printed run ID and exact SHA-256")
    root = safe_runs(root)
    folder = root / run_id
    if folder.is_symlink() or not folder.is_dir():
        raise gate.ContractError("unknown local run")
    for name in ["manifest.json", "candidate.json", "report.json"]:
        if (folder / name).is_symlink():
            raise gate.ContractError("run files cannot be symlinks")
    manifest = json.loads((folder / "manifest.json").read_text())
    candidate = json.loads((folder / "candidate.json").read_text())
    data = gate.packet()
    gate.report(candidate, data)
    if (manifest.get("status") != "awaiting_approval" or manifest.get("fixture_sha256") != gate.digest(data)
            or manifest.get("candidate_sha256") != candidate_hash or gate.digest(candidate) != candidate_hash):
        raise gate.ContractError("candidate, input or hash changed; do not publish")
    published = {"approved_by": "explicit local CLI user", "candidate_sha256": candidate_hash, "report": candidate}
    path = folder / "report.json"
    if path.exists():
        if json.loads(path.read_text()) != published:
            raise gate.ContractError("existing report differs; refusing overwrite")
        return {"status": "already_published", "path": str(path)}
    with path.open("x") as output:
        output.write(json.dumps(published, ensure_ascii=False, indent=2) + "\n")
    return {"status": "published_locally", "path": str(path)}


def parser():
    p = argparse.ArgumentParser(description="Team Agent Lab 0.1.0: deterministic orchestration simulator / optional loopback model")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("run")
    r.add_argument("--mode", choices=["single", "sequential", "parallel", "compare"], default="parallel")
    r.add_argument("--backend", choices=["mock", "local"], default="mock")
    r.add_argument("--base-url", default="")
    r.add_argument("--model", default="")
    r.add_argument("--max-calls", type=int, default=8)
    r.add_argument("--retries", type=int, default=1)
    r.add_argument("--timeout", type=float, default=2)
    r.add_argument("--deadline", type=float, default=10)
    r.add_argument("--cancel-after-ms", type=int)
    r.add_argument("--max-revisions", type=int, default=1)
    r.add_argument("--single-turns", type=int, default=5)
    r.add_argument("--latency-ms", type=int, default=40)
    r.add_argument("--max-output-tokens", type=int, default=512)
    r.add_argument("--fault", choices=["none", "transient", "timeout", "malformed", "conflict", "review_reject"], default="none")
    a = sub.add_parser("approve")
    a.add_argument("run_id")
    a.add_argument("--hash", required=True)
    return p


def main():
    args = parser().parse_args()
    try:
        if args.command == "approve":
            print(json.dumps(approve(args.run_id, args.hash), ensure_ascii=False, indent=2))
            return 0
        if not 0 <= args.latency_ms <= 2000 or not 128 <= args.max_output_tokens <= 2048:
            raise gate.ContractError("latency must be 0–2000 ms; max-output-tokens 128–2048")
        if args.backend == "local" and args.fault != "none":
            raise gate.ContractError("fault injection is mock-only")
        if args.mode == "compare" and (args.fault != "none" or args.cancel_after_ms is not None):
            raise gate.ContractError("compare uses clean runs; inject faults separately")
        backend = LocalBackend(args.base_url, args.model, args.max_output_tokens) if args.backend == "local" else MockBackend(args.latency_ms, args.fault)

        async def execute():
            results = []
            for mode in (["single", "sequential", "parallel"] if args.mode == "compare" else [args.mode]):
                result = await run(backend, mode, args.max_calls, args.retries, args.timeout, args.deadline, args.cancel_after_ms, args.max_revisions, args.single_turns)
                results.append(save(result))
            return results

        results = asyncio.run(execute())
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0 if all(x["validated"] for x in results) else 2
    except (gate.ContractError, OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
