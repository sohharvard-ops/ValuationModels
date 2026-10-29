"""Shared yfinance data retrieval and input validation."""
from __future__ import annotations
from typing import Any, Sequence
import math
import pandas as pd
import yfinance as yf


def require_finite_number(variable_name: str, value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{variable_name} must be a finite number.")
    try:
        number = float(value)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{variable_name} must be a finite number; received {value!r}.") from error
    if not math.isfinite(number):
        raise ValueError(f"{variable_name} must be finite; received {value!r}.")
    return number


def latest_statement_value(statement: pd.DataFrame, row_names: Sequence[str]) -> float | None:
    """Return the latest available value matching one of the statement row names."""
    if statement is None or statement.empty:
        return None
    wanted_names = {name.casefold() for name in row_names}
    for row_name in statement.index:
        if str(row_name).casefold() in wanted_names:
            for value in statement.loc[row_name].tolist():
                try:
                    number = float(value)
                except (TypeError, ValueError):
                    continue
                if math.isfinite(number):
                    return number
    return None


def info_number(info: dict[str, Any], field_name: str) -> float | None:
    value = info.get(field_name)
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def fetch_company_data(ticker_symbol: str) -> dict[str, Any]:
    """Get quote, annual statements, and dividend history from Yahoo Finance."""
    ticker_symbol = ticker_symbol.strip().upper()
    if not ticker_symbol:
        raise ValueError("ticker_symbol cannot be blank.")
    ticker = yf.Ticker(ticker_symbol)
    company_info = ticker.get_info()
    income_statement = ticker.income_stmt
    balance_sheet = ticker.balance_sheet
    cash_flow = ticker.cashflow

    profit_revenue = latest_statement_value(income_statement, ["Total Revenue", "Operating Revenue"])
    profit_operating_income = latest_statement_value(income_statement, ["Operating Income"])
    tax_provision = latest_statement_value(income_statement, ["Tax Provision"])
    pretax_income = latest_statement_value(income_statement, ["Pretax Income", "Income Before Tax"])
    historical_tax_rate = tax_provision / pretax_income if tax_provision is not None and pretax_income not in (None, 0) else None
    total_expenses = profit_revenue - profit_operating_income if profit_revenue is not None and profit_operating_income is not None else None

    dividend_history = ticker.dividends
    trailing_dividend_per_share = None
    if dividend_history is not None and not dividend_history.empty:
        dividend_history.index = pd.to_datetime(dividend_history.index, utc=True)
        one_year_ago = pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=365)
        trailing_dividend_per_share = float(dividend_history[dividend_history.index >= one_year_ago].sum())

    return {
        "ticker_symbol": ticker_symbol,
        "currency": company_info.get("currency"),
        "current_price": info_number(company_info, "currentPrice") or info_number(company_info, "regularMarketPrice"),
        "market_cap": info_number(company_info, "marketCap"),
        "enterprise_value": info_number(company_info, "enterpriseValue"),
        "diluted_shares_outstanding": info_number(company_info, "impliedSharesOutstanding") or info_number(company_info, "sharesOutstanding"),
        "cash_and_cash_equivalents": info_number(company_info, "totalCash") or latest_statement_value(balance_sheet, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"]),
        "total_debt": info_number(company_info, "totalDebt") or latest_statement_value(balance_sheet, ["Total Debt", "Long Term Debt And Capital Lease Obligation"]),
        "total_assets": latest_statement_value(balance_sheet, ["Total Assets"]),
        "total_liabilities": latest_statement_value(balance_sheet, ["Total Liabilities Net Minority Interest", "Total Liabilities"]),
        "profit_revenue": profit_revenue,
        "profit_operating_income": profit_operating_income,
        "total_expenses": total_expenses,
        "historical_tax_rate": historical_tax_rate,
        "depreciation_amortization": latest_statement_value(cash_flow, ["Depreciation And Amortization", "Depreciation Amortization Depletion"]),
        "capital_expenditures": latest_statement_value(cash_flow, ["Capital Expenditure", "Capital Expenditures"]),
        "ebitda": info_number(company_info, "ebitda"),
        "trailing_dividend_per_share": trailing_dividend_per_share,
    }
