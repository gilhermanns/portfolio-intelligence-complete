import pytest

from orderbook_sim.agents import LiquidityProvider, MomentumTrader, ParentOrderExecutor, round_to_tick
from orderbook_sim.engine import Engine, SimulationConfig
from orderbook_sim.orderbook import LimitOrderBook, Side


def test_round_to_tick_rounds_to_nearest_grid_point():
    assert round_to_tick(100.2345, 0.01) == pytest.approx(100.23)
    assert round_to_tick(100.238, 0.05) == pytest.approx(100.25)


def test_round_to_tick_rounds_up_and_down_across_a_cent():
    assert round_to_tick(99.999, 0.01) == pytest.approx(100.0)
    assert round_to_tick(100.001, 0.01) == pytest.approx(100.0)


def test_lp_widens_ask_when_rounding_would_cross_the_book():
    # With a half-spread smaller than half a tick, rounding both quotes to the
    # tick grid can collapse them onto the same price. The LP must detect
    # that and bump the ask up by a tick rather than post a self-crossing
    # (or locked) quote.
    config = SimulationConfig(tick_size=0.01, initial_mid_price=100.0)
    lp = LiquidityProvider(
        agent_id="LP", rate=1.0, half_spread=0.001, quote_size=5.0,
        inventory_skew=0.0, tick_size=0.01,
    )
    book = LimitOrderBook()
    engine = Engine(config, [lp], book)

    lp.act(engine, 0.0)

    assert book.best_bid == pytest.approx(100.0)
    assert book.best_ask == pytest.approx(100.01)
    assert book.best_bid < book.best_ask


def test_lp_requote_cancels_previous_resting_orders():
    config = SimulationConfig(tick_size=0.01, initial_mid_price=100.0)
    lp = LiquidityProvider(
        agent_id="LP", rate=1.0, half_spread=0.05, quote_size=5.0,
        inventory_skew=0.0, tick_size=0.01,
    )
    book = LimitOrderBook()
    engine = Engine(config, [lp], book)

    lp.act(engine, 0.0)
    first_bid_id, first_ask_id = lp.active_bid_id, lp.active_ask_id
    lp.act(engine, 1.0)

    assert lp.active_bid_id != first_bid_id
    assert lp.active_ask_id != first_ask_id
    # exactly one resting order per side survives the requote
    assert sum(len(level) for level in book.bids.values()) == 1
    assert sum(len(level) for level in book.asks.values()) == 1


def test_momentum_trader_buys_on_sufficient_upward_move():
    config = SimulationConfig(tick_size=0.01, initial_mid_price=100.0)
    mom = MomentumTrader(agent_id="MOM", rate=1.0, lookback=5.0, threshold=0.001, order_size=2.0)
    book = LimitOrderBook()
    book.add_limit_order(Side.SELL, 101.0, 10, 0.0, "MAKER")
    engine = Engine(config, [mom], book)
    engine.mid_history.append((0.0, 100.0))
    engine.mid_history.append((5.0, 100.5))  # +0.5% over the lookback window

    mom.act(engine, 5.0)

    assert mom.qty_sent == 2.0
    assert len(book.trade_tape) == 1
    assert book.trade_tape[0].aggressor_side is Side.BUY
    assert book.trade_tape[0].resting_agent_id == "MAKER"


def test_momentum_trader_sells_on_sufficient_downward_move():
    config = SimulationConfig(tick_size=0.01, initial_mid_price=100.0)
    mom = MomentumTrader(agent_id="MOM", rate=1.0, lookback=5.0, threshold=0.001, order_size=2.0)
    book = LimitOrderBook()
    book.add_limit_order(Side.BUY, 99.0, 10, 0.0, "MAKER")
    engine = Engine(config, [mom], book)
    engine.mid_history.append((0.0, 100.0))
    engine.mid_history.append((5.0, 99.5))  # -0.5% over the lookback window

    mom.act(engine, 5.0)

    assert mom.qty_sent == 2.0
    assert len(book.trade_tape) == 1
    assert book.trade_tape[0].aggressor_side is Side.SELL
    assert book.trade_tape[0].resting_agent_id == "MAKER"


def test_momentum_trader_stays_flat_within_threshold():
    config = SimulationConfig(tick_size=0.01, initial_mid_price=100.0)
    mom = MomentumTrader(agent_id="MOM", rate=1.0, lookback=5.0, threshold=0.01, order_size=2.0)
    book = LimitOrderBook()
    book.add_limit_order(Side.SELL, 101.0, 10, 0.0, "MAKER")
    book.add_limit_order(Side.BUY, 99.0, 10, 0.0, "MAKER2")
    engine = Engine(config, [mom], book)
    engine.mid_history.append((0.0, 100.0))
    engine.mid_history.append((5.0, 100.05))  # +0.05%, inside the 1% threshold

    mom.act(engine, 5.0)

    assert mom.qty_sent == 0.0
    assert book.trade_tape == []


def test_parent_order_aggressive_ignores_requested_slice_count():
    parent = ParentOrderExecutor(
        agent_id="P", side=Side.BUY, total_qty=100.0, entry_time=10.0,
        strategy="aggressive", n_slices=5, slice_interval=2.0,
    )
    assert parent.n_slices == 1
    assert parent._times == [10.0]
    assert parent.schedule_next(rng=None, t_now=0.0) == 10.0


def test_parent_order_twap_builds_evenly_spaced_slice_schedule():
    parent = ParentOrderExecutor(
        agent_id="P", side=Side.SELL, total_qty=40.0, entry_time=3.0,
        strategy="twap", n_slices=4, slice_interval=1.5,
    )
    assert parent.n_slices == 4
    assert parent._times == pytest.approx([3.0, 4.5, 6.0, 7.5])


def test_parent_order_arrival_mid_is_captured_once_on_first_slice():
    config = SimulationConfig(tick_size=0.01, initial_mid_price=100.0)
    book = LimitOrderBook()
    book.add_limit_order(Side.BUY, 99.0, 100, 0.0, "SEED_BID")
    book.add_limit_order(Side.SELL, 101.0, 100, 0.0, "SEED_ASK")
    parent = ParentOrderExecutor(
        agent_id="P", side=Side.BUY, total_qty=20.0, entry_time=0.0,
        strategy="twap", n_slices=2, slice_interval=1.0,
    )
    engine = Engine(config, [parent], book)

    parent.act(engine, 0.0)
    first_arrival_mid = parent.arrival_mid
    assert first_arrival_mid == pytest.approx(100.0)

    # book has moved (bid lifted higher) by the time the second slice fires;
    # arrival_mid must not be overwritten by the later, moved price.
    book.add_limit_order(Side.BUY, 100.5, 5, 0.5, "MOVER")
    parent.act(engine, 1.0)

    assert parent.arrival_mid == first_arrival_mid
