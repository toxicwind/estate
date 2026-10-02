import pytest
from src.python.lottery.ev_calculator import (
    CASINO_CASH_CHIPS,
    JUMBO_BUCKS_CROSSWORD,
    ROCKY_MTN_CUBE_BINGO,
    MAD_MONEY,
)


def test_casino_cash_chips_positive_ev():
    g = CASINO_CASH_CHIPS
    assert g.dynamic_ev() > g.price  # jackpot lag anomaly
    assert g.house_edge() < 0.0


def test_jumbo_bucks_neutral():
    g = JUMBO_BUCKS_CROSSWORD
    ev = g.dynamic_ev()
    assert 0.0 < ev < g.price
    assert g.house_edge() > 0.0


def test_mad_money_negative():
    g = MAD_MONEY
    assert g.dynamic_ev() < g.price
    assert g.house_edge() > 0.35


def test_top_equity_zero_when_exhausted():
    g = CASINO_CASH_CHIPS
    exhausted = g.__class__(
        name=g.name,
        game_number=g.game_number,
        price=g.price,
        total_tickets=g.total_tickets,
        top_prize=g.top_prize,
        top_prizes_total=g.top_prizes_total,
        top_prizes_remaining=0,
        payout_pct=g.payout_pct,
        overall_odds=g.overall_odds,
    )
    assert exhausted.top_equity_per_ticket() == 0.0
