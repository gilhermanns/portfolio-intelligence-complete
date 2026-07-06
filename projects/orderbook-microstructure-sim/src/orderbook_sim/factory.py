from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .agents import LiquidityProvider, MomentumTrader, NoiseTrader
from .engine import SimulationConfig
from .orderbook import LimitOrderBook, Side


@dataclass
class AgentPopulationConfig:
    n_lp: int = 1
    lp_rate: float = 1.0
    lp_half_spread: float = 0.05
    lp_quote_size: float = 10.0
    lp_inventory_skew: float = 0.002

    n_momentum: int = 3
    momentum_rate: float = 0.5
    momentum_lookback: float = 5.0
    momentum_threshold: float = 0.0004
    momentum_size: float = 4.0

    n_noise: int = 8
    noise_rate: float = 1.2
    noise_limit_prob: float = 0.5
    noise_size_mean: float = 3.0
    noise_offset_std: float = 0.10


def build_background_agents(pop: AgentPopulationConfig, config: SimulationConfig) -> List:
    agents = []
    for i in range(pop.n_lp):
        agents.append(
            LiquidityProvider(
                agent_id=f"LP_{i}",
                rate=pop.lp_rate,
                half_spread=pop.lp_half_spread,
                quote_size=pop.lp_quote_size,
                inventory_skew=pop.lp_inventory_skew,
                tick_size=config.tick_size,
            )
        )
    for i in range(pop.n_momentum):
        agents.append(
            MomentumTrader(
                agent_id=f"MOM_{i}",
                rate=pop.momentum_rate,
                lookback=pop.momentum_lookback,
                threshold=pop.momentum_threshold,
                order_size=pop.momentum_size,
            )
        )
    for i in range(pop.n_noise):
        agents.append(
            NoiseTrader(
                agent_id=f"NOISE_{i}",
                rate=pop.noise_rate,
                limit_prob=pop.noise_limit_prob,
                size_mean=pop.noise_size_mean,
                offset_std=pop.noise_offset_std,
                tick_size=config.tick_size,
            )
        )
    return agents


def seed_book(book: LimitOrderBook, config: SimulationConfig, half_spread: float, depth_levels: int, size: float) -> None:
    mid = config.initial_mid_price
    for lvl in range(1, depth_levels + 1):
        bid_price = round(mid - half_spread - lvl * config.tick_size * 4, 2)
        ask_price = round(mid + half_spread + lvl * config.tick_size * 4, 2)
        book.add_limit_order(Side.BUY, bid_price, size, 0.0, "SEED")
        book.add_limit_order(Side.SELL, ask_price, size, 0.0, "SEED")
