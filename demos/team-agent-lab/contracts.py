"""Small teaching contracts, not a general fact checker or security sandbox."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKERS = ("implementation", "validation")


class ContractError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def packet():
    # No user-controlled file path, recursive directory reading or shell tool.
    path = ROOT / "fixtures" / "packet.json"
    if (ROOT / "fixtures").is_symlink() or path.is_symlink() or path.resolve().parent != (ROOT / "fixtures").resolve():
        raise ContractError("fixture must be the bundled regular file")
    data = path.read_bytes()
    if len(data) > 65536:
        raise ContractError("fixture too large")
    return json.loads(data)


def text(value, limit=500):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ContractError("expected bounded nonempty text")
    return value


def evidence(data, document_ids):
    if not isinstance(document_ids, list) or not document_ids or len(document_ids) > 3:
        raise ContractError("read_evidence requires 1–3 document IDs")
    if any(not isinstance(key, str) or key not in data["documents"] for key in document_ids):
        raise ContractError("read_evidence: document outside allowlist")
    if len(set(document_ids)) != len(document_ids):
        raise ContractError("duplicate document ID")
    return [dict(line, document=key) for key in document_ids for line in data["documents"][key]]


def all_evidence(data):
    return evidence(data, list(data["documents"]))


def plan(value, data):
    tasks = value.get("tasks") if isinstance(value, dict) else None
    if not isinstance(tasks, list) or len(tasks) != 2:
        raise ContractError("planner must fill exactly two bounded worker slots")
    by_id = {}
    task_ids = set()
    for task in tasks:
        if not isinstance(task, dict) or task.get("worker_id") not in WORKERS:
            raise ContractError("unregistered worker")
        key = task["worker_id"]
        task_id = task.get("task_id")
        if not isinstance(task_id, str) or not re.fullmatch(r"[a-z0-9-]{1,40}", task_id) or task_id in task_ids:
            raise ContractError("task ID must be unique and bounded")
        task_ids.add(task_id)
        if key in by_id:
            raise ContractError("duplicate worker")
        ids = task.get("document_ids")
        evidence(data, ids)
        required = {"policy", "release" if key == "implementation" else "tests"}
        if not required <= set(ids):
            raise ContractError("worker missing required source family")
        by_id[key] = {"task_id": task_id, "worker_id": key, "document_ids": ids, "focus": text(task.get("focus"))}
    return [by_id[key] for key in WORKERS]


def findings(value, visible):
    if not isinstance(value, dict) or value.get("assessment") not in ("ready", "needs_gate"):
        raise ContractError("invalid assessment")
    rows = value.get("findings")
    if not isinstance(rows, list) or not 1 <= len(rows) <= 8:
        raise ContractError("expected 1–8 findings")
    available = {row["id"]: row["text"] for row in visible}
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ContractError("finding must be an object")
        key = row.get("evidence_id")
        if not isinstance(key, str) or key not in available or key in seen:
            raise ContractError("invalid, unseen or duplicate evidence")
        if row.get("quote") != available[key]:
            raise ContractError("quote must match the visible source exactly")
        text(row.get("note"))
        seen.add(key)
    return value


def review(value, data):
    if not isinstance(value, dict) or type(value.get("approved")) is not bool:
        raise ContractError("review must contain a boolean decision")
    feedback = value.get("feedback")
    if not isinstance(feedback, list) or len(feedback) > 2 or value["approved"] == bool(feedback):
        raise ContractError("approved reviews have no feedback; rejected reviews need feedback")
    ids = {row["id"] for row in all_evidence(data)}
    seen = set()
    for item in feedback:
        if not isinstance(item, dict) or item.get("worker_id") not in WORKERS or item["worker_id"] in seen:
            raise ContractError("feedback targets one registered worker once")
        text(item.get("message"))
        cited = item.get("evidence_ids")
        if not isinstance(cited, list) or not cited or any(not isinstance(x, str) or x not in ids for x in cited):
            raise ContractError("feedback needs existing evidence IDs")
        seen.add(item["worker_id"])
    return value


def report(value, data):
    if not isinstance(value, dict) or value.get("verdict") != "shadow_only":
        raise ContractError("fixture grader: only restricted read-only shadow is justified")
    text(value.get("summary"), 1200)
    rows = value.get("reasons")
    if not isinstance(rows, list) or not 3 <= len(rows) <= 6:
        raise ContractError("report needs 3–6 cited reasons")
    ids = {row["id"] for row in all_evidence(data)}
    used = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ContractError("reason must be an object")
        text(row.get("text"))
        cited = row.get("evidence_ids")
        if not isinstance(cited, list) or not cited or any(not isinstance(x, str) or x not in ids for x in cited):
            raise ContractError("report cites unknown evidence")
        used.update(cited)
    if not {"R2", "T2", "P1", "P2"} <= used:
        raise ContractError("fixture grader: missing implementation, test or policy evidence")
    return value
