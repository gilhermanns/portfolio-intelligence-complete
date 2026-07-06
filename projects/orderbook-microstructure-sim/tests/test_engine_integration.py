from orderbook_sim.agents import PureTaker
from orderbook_sim.engine import Engine, SimulationConfig
from orderbook_sim.factory import AgentPopulationConfig, build_background_agents, seed_book
from orderbook_sim.orderbook import LimitOrderBook


def _run_small_sim(seed=1, total_time=120.0):
    config = SimulationConfig(total_time=total_time, seed=seed, sampling_dt=1.0)
    pop = AgentPopulationConfig(n_lp=1, n_momentum=2, n_noise=4)
    book = LimitOrderBook()
    seed_book(book, config, pop.lp_half_spread, depth_levels=5, size=pop.lp_quote_size)
    agents = build_background_agents(pop, config)
    taker = PureTaker(agent_id="TAKER_0", rate=0.3, order_size=5.0)
    agents.append(taker)
    engine = Engine(config, agents, book)
    engine.run()
    return engine, agents, taker


def test_simulation_runs_and_produces_trades():
    engine, agents, taker = _run_small_sim()
    assert len(engine.book.trade_tape) > 0
    assert len(engine.sampler.t) > 0


def test_book_never_crossed_at_end_of_sim():
    engine, agents, taker = _run_small_sim()
    bb, ba = engine.book.best_bid, engine.book.best_ask
    if bb is not None and ba is not None:
        assert bb < ba


def test_deterministic_with_fixed_seed():
    engine1, _, _ = _run_small_sim(seed=5)
    engine2, _, _ = _run_small_sim(seed=5)
    assert len(engine1.book.trade_tape) == len(engine2.book.trade_tape)
    assert engine1.sampler.mid == engine2.sampler.mid
    for t1, t2 in zip(engine1.book.trade_tape, engine2.book.trade_tape):
        assert t1.price == t2.price
        assert t1.qty == t2.qty


def test_different_seeds_produce_different_paths():
    engine1, _, _ = _run_small_sim(seed=1)
    engine2, _, _ = _run_small_sim(seed=2)
    assert engine1.sampler.mid != engine2.sampler.mid


def test_lp_inventory_and_cash_are_consistent_with_fills():
    engine, agents, _ = _run_small_sim(seed=3, total_time=200.0)
    lp = next(a for a in agents if a.agent_type == "LP")
    signed_qty = 0.0
    signed_cash = 0.0
    for tr in engine.book.trade_tape:
        if tr.resting_agent_id == lp.agent_id:
            resting_side_is_buy = tr.aggressor_side.name == "SELL"
            if resting_side_is_buy:
                signed_qty += tr.qty
                signed_cash -= tr.qty * tr.price
            else:
                signed_qty -= tr.qty
                signed_cash += tr.qty * tr.price
        if tr.incoming_agent_id == lp.agent_id:
            if tr.aggressor_side.name == "BUY":
                signed_qty += tr.qty
                signed_cash -= tr.qty * tr.price
            else:
                signed_qty -= tr.qty
                signed_cash += tr.qty * tr.price
    assert lp.inventory == signed_qty
    assert lp.cash == signed_cash


def test_sampler_tracks_pnl_for_all_agents():
    engine, agents, taker = _run_small_sim()
    for agent in agents:
        assert agent.agent_id in engine.sampler.agent_pnl
        assert len(engine.sampler.agent_pnl[agent.agent_id]) == len(engine.sampler.t)
