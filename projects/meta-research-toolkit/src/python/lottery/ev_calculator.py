"""Finite-population scratch-off EV calculator.

Implements the without-replacement model from the Colorado Lottery analysis.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Game:
    name: str
    game_number: int
    price: float
    total_tickets: int
    top_prize: float
    top_prizes_total: int
    top_prizes_remaining: int
    payout_pct: float
    overall_odds: float
    # Remaining unsold tickets when known (audit snapshot). None = unknown,
    # conservative fallback to the full print run (no assumed sell-through).
    tickets_remaining: int | None = None

    def top_equity_per_ticket(self) -> float:
        """Current top-prize equity in the remaining pool."""
        if self.top_prizes_remaining <= 0:
            return 0.0
        remaining = self.tickets_remaining if self.tickets_remaining else self.total_tickets
        return (self.top_prizes_remaining * self.top_prize) / remaining

    def baseline_ev(self) -> float:
        """Statutory EV before top-prize lag adjustment."""
        return self.price * self.payout_pct

    def dynamic_ev(self) -> float:
        """EV with top-prize lag surplus/deficit."""
        launch_top_equity = (self.top_prizes_total * self.top_prize) / self.total_tickets
        current_top_equity = self.top_equity_per_ticket()
        surplus = current_top_equity - launch_top_equity
        return self.baseline_ev() + surplus

    def house_edge(self) -> float:
        return 1.0 - (self.dynamic_ev() / self.price)


# Colorado games from September 2026 audit
CASINO_CASH_CHIPS = Game(
    name="Casino Ca$h Chips",
    game_number=280,
    price=20.0,
    total_tickets=2_160_000,
    top_prize=1_000_000.0,
    top_prizes_total=2,
    top_prizes_remaining=2,
    payout_pct=0.745,
    overall_odds=1 / 3.29,
    tickets_remaining=300_000,  # jackpot lag anomaly: both M tops alive deep into the run
)

JUMBO_BUCKS_CROSSWORD = Game(
    name="$250,000 Jumbo Bucks Crossword",
    game_number=390,
    price=10.0,
    total_tickets=4_560_000,
    top_prize=250_000.0,
    top_prizes_total=9,
    top_prizes_remaining=7,
    payout_pct=0.71,
    overall_odds=1 / 3.29,
    tickets_remaining=3_546_667,  # ~proportional sell-through: neutral lag
)

ROCKY_MTN_CUBE_BINGO = Game(
    name="Rocky Mountain Cube Bingo",
    game_number=371,
    price=5.0,
    total_tickets=2_400_000,  # inferred from odds
    top_prize=140_000.0,
    top_prizes_total=8,
    top_prizes_remaining=5,
    payout_pct=0.685,
    overall_odds=1 / 3.50,
)

MAD_MONEY = Game(
    name="$1,000 Mad Money",
    game_number=424,
    price=1.0,
    total_tickets=720_000,  # inferred
    top_prize=1_000.0,
    top_prizes_total=145,
    top_prizes_remaining=109,
    payout_pct=0.60,
    overall_odds=1 / 4.89,
)
