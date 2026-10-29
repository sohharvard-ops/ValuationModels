"""Gordon growth dividend discount valuation."""
from .data import require_finite_number


def calculate_dividend_discount(*, next_year_dividend_per_share: float, cost_of_equity: float, dividend_growth_rate: float, diluted_shares_outstanding: float) -> dict[str, float | str]:
    """Value a dividend-paying share with constant perpetual dividend growth."""
    next_year_dividend_per_share = require_finite_number("next_year_dividend_per_share", next_year_dividend_per_share)
    cost_of_equity = require_finite_number("cost_of_equity", cost_of_equity)
    dividend_growth_rate = require_finite_number("dividend_growth_rate", dividend_growth_rate)
    diluted_shares_outstanding = require_finite_number("diluted_shares_outstanding", diluted_shares_outstanding)
    if next_year_dividend_per_share < 0:
        raise ValueError("next_year_dividend_per_share cannot be negative.")
    if cost_of_equity <= dividend_growth_rate:
        raise ValueError("cost_of_equity must be greater than dividend_growth_rate.")
    if diluted_shares_outstanding <= 0:
        raise ValueError("diluted_shares_outstanding must be positive.")
    intrinsic_value_per_share = next_year_dividend_per_share / (cost_of_equity - dividend_growth_rate)
    return {
        "method": "Gordon growth dividend discount model",
        "formula": "Share value = next year's dividend / (cost of equity − perpetual dividend growth)",
        "next_year_dividend_per_share": next_year_dividend_per_share,
        "cost_of_equity": cost_of_equity,
        "dividend_growth_rate": dividend_growth_rate,
        "intrinsic_value_per_share": intrinsic_value_per_share,
        "equity_value": intrinsic_value_per_share * diluted_shares_outstanding,
        "diluted_shares_outstanding": diluted_shares_outstanding,
    }
