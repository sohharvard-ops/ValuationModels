"""Comparable-company EV/EBITDA valuation."""
from statistics import median
from typing import Any
from .data import require_finite_number


def calculate_comparable_company_value(*, target_ebitda: float, target_cash: float, target_debt: float, target_diluted_shares: float, peer_data: dict[str, dict[str, float | None]]) -> dict[str, Any]:
    """Apply median peer EV/EBITDA to target EBITDA, then convert EV to equity value."""
    target_ebitda = require_finite_number("target_ebitda", target_ebitda)
    target_cash = require_finite_number("target_cash", target_cash)
    target_debt = require_finite_number("target_debt", target_debt)
    target_diluted_shares = require_finite_number("target_diluted_shares", target_diluted_shares)
    if target_ebitda <= 0 or target_diluted_shares <= 0 or target_cash < 0 or target_debt < 0:
        raise ValueError("EBITDA and shares must be positive; cash and debt must be nonnegative.")
    peer_multiples = []
    for peer_ticker, peer_metrics in peer_data.items():
        enterprise_value = peer_metrics.get("enterprise_value")
        peer_ebitda = peer_metrics.get("ebitda")
        if enterprise_value is None or peer_ebitda is None or enterprise_value <= 0 or peer_ebitda <= 0:
            continue
        peer_multiples.append({"ticker_symbol": peer_ticker, "enterprise_value": enterprise_value,
                               "ebitda": peer_ebitda, "ev_to_ebitda": enterprise_value / peer_ebitda})
    if not peer_multiples:
        raise ValueError("No peers have positive enterprise value and EBITDA data.")
    median_peer_ev_to_ebitda = median(peer["ev_to_ebitda"] for peer in peer_multiples)
    implied_enterprise_value = median_peer_ev_to_ebitda * target_ebitda
    implied_equity_value = implied_enterprise_value + target_cash - target_debt
    return {
        "method": "Comparable companies (EV/EBITDA)",
        "formula": "Median peer EV/EBITDA × target EBITDA = implied enterprise value",
        "peer_multiples": peer_multiples,
        "median_peer_ev_to_ebitda": median_peer_ev_to_ebitda,
        "target_ebitda": target_ebitda,
        "implied_enterprise_value": implied_enterprise_value,
        "cash_and_cash_equivalents": target_cash,
        "total_debt": target_debt,
        "implied_equity_value": implied_equity_value,
        "diluted_shares_outstanding": target_diluted_shares,
        "implied_value_per_share": implied_equity_value / target_diluted_shares,
    }
