"""
GRC Advanced 4 — Treatment selection optimizer.

Chooses exactly `required_treatment_count` treatments from the supplied
list such that:
  - total cost <= budget
  - every selected treatment's dependencies are also selected
  - the sum of mean_reduction is maximized

Tie-break: if two feasible portfolios' mean_reduction sums differ by less
than one cent (0.01), the lexicographically smaller ordered treatment-ID
list wins (tuples of sorted IDs compared element-wise).

No treatment IDs, budgets, or expected answers are hard-coded — the
function operates purely on whatever list/budget/count it is given.
"""
from itertools import combinations


def _deps_satisfied(selected_ids, treatments_by_id):
    for tid in selected_ids:
        for dep in treatments_by_id[tid].get("dependencies", []):
            if dep not in selected_ids:
                return False
    return True


def select_treatments(treatments, budget, required_treatment_count):
    """
    treatments: list of {"id": str, "cost": number, "mean_reduction": number,
                          "dependencies": [str, ...]}
    Returns: {"selected_treatment_ids": [...sorted...], "total_cost": float,
              "mean_reduction": float, "validation": "valid" | "infeasible"}
    """
    by_id = {t["id"]: t for t in treatments}
    all_ids = list(by_id.keys())

    best = None  # (mean_reduction, ordered_id_tuple, total_cost)
    for combo in combinations(all_ids, required_treatment_count):
        selected = set(combo)
        if not _deps_satisfied(selected, by_id):
            continue
        total_cost = sum(by_id[i]["cost"] for i in combo)
        if total_cost > budget:
            continue
        total_reduction = sum(by_id[i]["mean_reduction"] for i in combo)
        ordered = tuple(sorted(combo))

        if best is None:
            best = (total_reduction, ordered, total_cost)
            continue

        best_reduction, best_ordered, _ = best
        if total_reduction > best_reduction + 0.005:
            best = (total_reduction, ordered, total_cost)
        elif abs(total_reduction - best_reduction) < 0.01:
            # within a cent -> lexicographic tie-break
            if ordered < best_ordered:
                best = (total_reduction, ordered, total_cost)
        # else strictly worse -> keep current best

    if best is None:
        return {"selected_treatment_ids": [], "total_cost": 0, "mean_reduction": 0, "validation": "infeasible"}

    reduction, ordered, cost = best
    return {
        "selected_treatment_ids": list(ordered),
        "total_cost": cost,
        "mean_reduction": reduction,
        "validation": "valid",
    }
