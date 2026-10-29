"""Discounted cash flow valuation using annual FCFF."""
from __future__ import annotations
from typing import Any, Sequence
from .data import require_finite_number


def calculate_dcf(*, profit_revenue_forecast: Sequence[float], operating_margin_forecast: Sequence[float], tax_rate_forecast: Sequence[float], depreciation_amortization_forecast: Sequence[float], capital_expenditures_forecast: Sequence[float], change_in_net_working_capital_forecast: Sequence[float], wacc: float, terminal_growth_rate: float, cash_and_cash_equivalents: float, total_debt: float, diluted_shares_outstanding: float) -> dict[str, Any]:
    """Calculate FCFF, present values, terminal value, and per-share equity value."""
    forecast_inputs = {
        "profit_revenue_forecast": profit_revenue_forecast,
        "operating_margin_forecast": operating_margin_forecast,
        "tax_rate_forecast": tax_rate_forecast,
        "depreciation_amortization_forecast": depreciation_amortization_forecast,
        "capital_expenditures_forecast": capital_expenditures_forecast,
        "change_in_net_working_capital_forecast": change_in_net_working_capital_forecast,
    }
    converted_forecasts = {}
    for variable_name, forecast_values in forecast_inputs.items():
        converted_forecasts[variable_name] = tuple(require_finite_number(f"{variable_name}[{year}]", value) for year, value in enumerate(forecast_values, 1))
        if not converted_forecasts[variable_name]:
            raise ValueError(f"{variable_name} cannot be empty.")
    forecast_lengths = {len(values) for values in converted_forecasts.values()}
    if len(forecast_lengths) != 1:
        raise ValueError("All DCF forecasts must have the same number of years.")

    wacc = require_finite_number("wacc", wacc)
    terminal_growth_rate = require_finite_number("terminal_growth_rate", terminal_growth_rate)
    cash_and_cash_equivalents = require_finite_number("cash_and_cash_equivalents", cash_and_cash_equivalents)
    total_debt = require_finite_number("total_debt", total_debt)
    diluted_shares_outstanding = require_finite_number("diluted_shares_outstanding", diluted_shares_outstanding)
    if wacc <= terminal_growth_rate:
        raise ValueError("wacc must be greater than terminal_growth_rate.")
    if wacc <= -1 or terminal_growth_rate <= -1:
        raise ValueError("wacc and terminal_growth_rate must each be greater than -1.")
    if cash_and_cash_equivalents < 0 or total_debt < 0 or diluted_shares_outstanding <= 0:
        raise ValueError("Cash and debt must be nonnegative; diluted shares must be positive.")

    forecast_year_details = []
    for year, values in enumerate(zip(*converted_forecasts.values()), start=1):
        profit_revenue, operating_margin, tax_rate, depreciation_amortization, capital_expenditures, change_in_net_working_capital = values
        if profit_revenue < 0 or depreciation_amortization < 0 or capital_expenditures < 0:
            raise ValueError(f"Revenue, D&A, and capex must be nonnegative in forecast year {year}.")
        if not 0 <= tax_rate <= 1:
            raise ValueError(f"Tax rate for year {year} must be between 0 and 1.")
        profit_operating_income = profit_revenue * operating_margin
        total_expenses = profit_revenue - profit_operating_income
        after_tax_operating_income = profit_operating_income * (1 - tax_rate)
        free_cash_flow_to_firm = after_tax_operating_income + depreciation_amortization - capital_expenditures - change_in_net_working_capital
        discount_factor = 1 / (1 + wacc) ** year
        forecast_year_details.append({
            "year": year,
            "profit_revenue": profit_revenue,
            "operating_margin": operating_margin,
            "total_expenses": total_expenses,
            "profit_operating_income": profit_operating_income,
            "tax_rate": tax_rate,
            "after_tax_operating_income": after_tax_operating_income,
            "depreciation_amortization": depreciation_amortization,
            "capital_expenditures": capital_expenditures,
            "change_in_net_working_capital": change_in_net_working_capital,
            "free_cash_flow_to_firm": free_cash_flow_to_firm,
            "discount_factor": discount_factor,
            "present_value_of_fcff": free_cash_flow_to_firm * discount_factor,
        })
    terminal_year_fcff = forecast_year_details[-1]["free_cash_flow_to_firm"] * (1 + terminal_growth_rate)
    terminal_value = terminal_year_fcff / (wacc - terminal_growth_rate)
    present_value_of_forecast_fcff = sum(year["present_value_of_fcff"] for year in forecast_year_details)
    present_value_of_terminal_value = terminal_value * forecast_year_details[-1]["discount_factor"]
    enterprise_value = present_value_of_forecast_fcff + present_value_of_terminal_value
    equity_value = enterprise_value + cash_and_cash_equivalents - total_debt
    return {
        "method": "FCFF discounted cash flow",
        "formula": "FCFF = EBIT × (1 − tax rate) + D&A − capital expenditures − change in net working capital",
        "forecast_years": forecast_year_details,
        "terminal_year_fcff": terminal_year_fcff,
        "terminal_value": terminal_value,
        "present_value_of_forecast_fcff": present_value_of_forecast_fcff,
        "present_value_of_terminal_value": present_value_of_terminal_value,
        "enterprise_value": enterprise_value,
        "cash_and_cash_equivalents": cash_and_cash_equivalents,
        "total_debt": total_debt,
        "equity_value": equity_value,
        "diluted_shares_outstanding": diluted_shares_outstanding,
        "intrinsic_value_per_share": equity_value / diluted_shares_outstanding,
        "wacc": wacc,
        "terminal_growth_rate": terminal_growth_rate,
    }
