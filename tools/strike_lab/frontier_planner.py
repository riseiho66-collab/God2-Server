"""Pure, frontier-local substrate selection. No execution or persistence.

API: FrontierPlanner().plan(frontier) returns a JSON-compatible dict.
Input: {id: str, current_handler: str | None, substrates: {NAME: evidence}}.
Names are VM, TRANSACTION, HYPERFORK, FULL_NATIVE_CLIENT. Evidence is local
to this frontier: available/qualified/fidelity are explicit booleans, failures
is a list of frontier-specific failures. Accelerated gates are:
VM: successful_replays >= 3, closure=True;
TRANSACTION: handler == current_handler, rollback=True, side_effect_safe=True;
HYPERFORK: access=True, checkpoint=True, successful_restores >= 3.
cost: {frontier_id: str, measured: True, milliseconds: nonnegative number}.
All costs use the same per-candidate scope; absent/invalid/unmeasured/foreign
costs are UNKNOWN and never inferred. FULL_NATIVE_CLIENT needs availability,
execution_available=True (automated execution, separate from preflight), and
no failures; explicit qualified=False or fidelity=False also disables it.
Cheapest ready measured substrate wins, including native. Ties use name order
below. If none has a usable measurement, native is the selected fallback;
ready still reflects its evidence. Unknown-cost accelerators never win.
"""

from math import isfinite


SUBSTRATES = ("VM", "TRANSACTION", "HYPERFORK", "FULL_NATIVE_CLIENT")


class FrontierPlanner:
    def plan(self, frontier):
        frontier_id = frontier.get("id")
        if not isinstance(frontier_id, str) or not frontier_id:
            raise ValueError("frontier.id must be a nonempty string")
        candidates = {}
        for name in SUBSTRATES:
            evidence = frontier.get("substrates", {}).get(name, {})
            reasons = []
            if evidence.get("available") is not True:
                reasons.append("UNAVAILABLE")
            if evidence.get("failures"):
                reasons.append("FRONTIER_FAILURE")
            native = name == "FULL_NATIVE_CLIENT"
            if native and evidence.get("execution_available") is not True:
                reasons.append("AUTOMATION_UNAVAILABLE")
            for field in ("qualified", "fidelity"):
                if evidence.get(field, native) is not True:
                    reasons.append(field.upper() + "_NOT_PROVEN")
            if name == "VM":
                if not _three_successes(evidence.get("successful_replays")):
                    reasons.append("THREE_REPLAYS_REQUIRED")
                if evidence.get("closure") is not True:
                    reasons.append("CLOSURE_NOT_PROVEN")
            elif name == "TRANSACTION":
                handler = frontier.get("current_handler")
                if not isinstance(handler, str) or not handler or evidence.get("handler") != handler:
                    reasons.append("CURRENT_HANDLER_NOT_QUALIFIED")
                if evidence.get("rollback") is not True:
                    reasons.append("ROLLBACK_NOT_PROVEN")
                if evidence.get("side_effect_safe") is not True:
                    reasons.append("SIDE_EFFECT_SAFETY_NOT_PROVEN")
            elif name == "HYPERFORK":
                for field in ("access", "checkpoint"):
                    if evidence.get(field) is not True:
                        reasons.append(field.upper() + "_NOT_PROVEN")
                if not _three_successes(evidence.get("successful_restores")):
                    reasons.append("THREE_RESTORES_REQUIRED")
            cost = evidence.get("cost") or {}
            value = cost.get("milliseconds")
            measured = (
                cost.get("measured") is True
                and cost.get("frontier_id") == frontier_id
                and type(value) in (int, float)
                and value >= 0
                and (type(value) is int or isfinite(value))
            )
            candidates[name] = {
                "ready": not reasons,
                "reasons": reasons,
                "cost_status": "MEASURED" if measured else "UNKNOWN",
                "cost_ms": value if measured else None,
            }
        measured_ready = [name for name in SUBSTRATES
                          if candidates[name]["ready"]
                          and candidates[name]["cost_status"] == "MEASURED"]
        selected = min(measured_ready, key=lambda name: candidates[name]["cost_ms"]) \
            if measured_ready else "FULL_NATIVE_CLIENT"
        return {
            "frontier_id": frontier_id,
            "selected": selected,
            "ready": candidates[selected]["ready"],
            "execution_status": "READY" if candidates[selected]["ready"] else "BLOCKED_EXECUTION",
            "reason": "CHEAPEST_VALID_MEASURED" if measured_ready else "FULL_NATIVE_FALLBACK",
            "cost_status": candidates[selected]["cost_status"],
            "cost_ms": candidates[selected]["cost_ms"],
            "candidates": candidates,
        }


def _three_successes(value):
    return type(value) is int and value >= 3
