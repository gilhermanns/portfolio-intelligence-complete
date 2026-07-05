"""Runs the full simulation + execution-cost experiment and writes the
report artifacts (reports/summary.json, reports/shortfall_trials.json,
reports/*.svg) used by the README."""

from pathlib import Path

from orderbook_sim.plotting import (
    plot_book_ladder,
    plot_execution_shortfall,
    plot_imbalance_vs_return,
    plot_mid_spread,
    plot_pnl_comparison,
)
from orderbook_sim.simulate import main

REPORTS_DIR = Path(__file__).resolve().parents[1] / "reports"


def run():
    engine, agents, pure_taker, summary, shortfall_results = main()
    lp = next(a for a in agents if a.agent_type == "LP")

    plot_mid_spread(engine, REPORTS_DIR / "mid_spread.svg")
    plot_imbalance_vs_return(engine, REPORTS_DIR / "imbalance_vs_return.svg")
    plot_pnl_comparison(engine, lp.agent_id, pure_taker.agent_id, REPORTS_DIR / "pnl_comparison.svg")
    plot_execution_shortfall(shortfall_results, REPORTS_DIR / "execution_shortfall.svg")
    plot_book_ladder(engine, REPORTS_DIR / "book_ladder.svg")

    print("Wrote report artifacts to", REPORTS_DIR)
    return summary


if __name__ == "__main__":
    import json

    s = run()
    print(json.dumps(s, indent=2, default=float))
