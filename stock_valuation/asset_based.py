"""Adjusted net asset value valuation."""
from .data import require_finite_number


def calculate_asset_based_value(*, total_assets: float, total_liabilities: float, diluted_shares_outstanding: float, asset_value_adjustments: float = 0.0, liability_value_adjustments: float = 0.0) -> dict[str, float | str]:
    """Calculate adjusted net assets; adjustments are estimated fair value less book value."""
    total_assets = require_finite_number("total_assets", total_assets)
    total_liabilities = require_finite_number("total_liabilities", total_liabilities)
    diluted_shares_outstanding = require_finite_number("diluted_shares_outstanding", diluted_shares_outstanding)
    asset_value_adjustments = require_finite_number("asset_value_adjustments", asset_value_adjustments)
    liability_value_adjustments = require_finite_number("liability_value_adjustments", liability_value_adjustments)
    if total_assets < 0 or total_liabilities < 0:
        raise ValueError("Total assets and liabilities cannot be negative.")
    if diluted_shares_outstanding <= 0:
        raise ValueError("diluted_shares_outstanding must be positive.")
    adjusted_assets = total_assets + asset_value_adjustments
    adjusted_liabilities = total_liabilities + liability_value_adjustments
    equity_value = adjusted_assets - adjusted_liabilities
    return {
        "method": "Adjusted net asset value",
        "formula": "(book assets + asset adjustments) − (book liabilities + liability adjustments)",
        "total_assets": total_assets,
        "asset_value_adjustments": asset_value_adjustments,
        "adjusted_assets": adjusted_assets,
        "total_liabilities": total_liabilities,
        "liability_value_adjustments": liability_value_adjustments,
        "adjusted_liabilities": adjusted_liabilities,
        "equity_value": equity_value,
        "diluted_shares_outstanding": diluted_shares_outstanding,
        "intrinsic_value_per_share": equity_value / diluted_shares_outstanding,
    }
