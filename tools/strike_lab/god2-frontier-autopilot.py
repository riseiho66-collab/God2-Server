"""Bounded planner/report entry point. No unqualified execution or promotion."""
import json
from pathlib import Path
from frontier_planner import FrontierPlanner


def report(state):
    frontier = state['frontier']
    if frontier['id'] != state['current_frontier']:
        raise ValueError('Authoritative frontier fields disagree')
    plan = FrontierPlanner().plan(frontier)
    # Readiness is not a direction observation or an accepted transition.
    return '\n'.join((
        'FRONTIER: ' + frontier['id'],
        'SELECTED_SUBSTRATE: ' + plan['selected'],
        'NEXT_DIRECTION: ' + frontier['next_direction'],
        'ITERATION_COST_MS: ' + (str(plan['cost_ms']) if plan['cost_ms'] is not None else 'NOT_MEASURED'),
        'NEXT_BLOCKER: ' + state['execution']['blocker'],
    )), plan


if __name__ == '__main__':
    path = Path(__file__).resolve().parents[2] / 'artifacts/strike/state.json'
    output, plan = report(json.loads(path.read_text(encoding='utf-8')))
    print(output)
    # This version is planning/preflight only, not the requested full solver loop.
    raise SystemExit(0 if plan['ready'] else 2)
