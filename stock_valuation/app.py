"""Ticker analysis, model orchestration, chart, and command-line interface."""
from __future__ import annotations
from typing import Any, Sequence
import json
from .data import fetch_company_data, fetch_price_history
from .dcf import calculate_dcf
from .dividend_discount import calculate_dividend_discount
from .asset_based import calculate_asset_based_value
from .comparable_companies import calculate_comparable_company_value


def analyze_ticker(ticker_symbol: str, *, peer_tickers: Sequence[str] = (), forecast_years: int = 5, annual_profit_revenue_growth: float = 0.05, wacc: float = 0.09, terminal_growth_rate: float = 0.025, dividend_growth_rate: float = 0.03, cost_of_equity: float = 0.09) -> dict[str, Any]:
    """Fetch company data and calculate available valuation models."""
    if forecast_years < 1:
        raise ValueError("forecast_years must be at least 1.")
    company_data = fetch_company_data(ticker_symbol)
    profit_revenue = company_data["profit_revenue"]
    profit_operating_income = company_data["profit_operating_income"]
    if profit_revenue is None or profit_revenue <= 0 or profit_operating_income is None:
        raise ValueError(f"Could not retrieve revenue and operating income for {ticker_symbol}.")
    diluted_shares_outstanding = company_data["diluted_shares_outstanding"]
    cash_and_cash_equivalents = company_data["cash_and_cash_equivalents"]
    total_debt = company_data["total_debt"]
    if diluted_shares_outstanding is None or diluted_shares_outstanding <= 0:
        raise ValueError("Yahoo Finance did not provide positive diluted shares outstanding.")
    if cash_and_cash_equivalents is None or total_debt is None:
        raise ValueError("Yahoo Finance is missing cash or total debt. Confirm those inputs before calculating the value.")

    operating_margin = profit_operating_income / profit_revenue
    tax_rate = company_data["historical_tax_rate"]
    if tax_rate is None or not 0 <= tax_rate <= 1:
        tax_rate = 0.21
    depreciation_amortization = company_data["depreciation_amortization"]
    capital_expenditures = company_data["capital_expenditures"]
    if depreciation_amortization is None or capital_expenditures is None:
        raise ValueError("Yahoo Finance is missing depreciation/amortization or capital expenditure data.")
    depreciation_amortization = abs(depreciation_amortization)
    capital_expenditures = abs(capital_expenditures)

    profit_revenue_forecast = []
    forecast_profit_revenue = profit_revenue
    for _ in range(forecast_years):
        forecast_profit_revenue *= 1 + annual_profit_revenue_growth
        profit_revenue_forecast.append(forecast_profit_revenue)

    dcf_result = calculate_dcf(
        profit_revenue_forecast=profit_revenue_forecast,
        operating_margin_forecast=[operating_margin] * forecast_years,
        tax_rate_forecast=[tax_rate] * forecast_years,
        depreciation_amortization_forecast=[depreciation_amortization] * forecast_years,
        capital_expenditures_forecast=[capital_expenditures] * forecast_years,
        change_in_net_working_capital_forecast=[0.0] * forecast_years,
        wacc=wacc,
        terminal_growth_rate=terminal_growth_rate,
        cash_and_cash_equivalents=cash_and_cash_equivalents,
        total_debt=total_debt,
        diluted_shares_outstanding=diluted_shares_outstanding,
    )

    dividend_result = None
    trailing_dividend_per_share = company_data["trailing_dividend_per_share"]
    if trailing_dividend_per_share is not None and trailing_dividend_per_share > 0:
        dividend_result = calculate_dividend_discount(
            next_year_dividend_per_share=trailing_dividend_per_share * (1 + dividend_growth_rate),
            cost_of_equity=cost_of_equity,
            dividend_growth_rate=dividend_growth_rate,
            diluted_shares_outstanding=diluted_shares_outstanding,
        )

    asset_result = None
    if company_data["total_assets"] is not None and company_data["total_liabilities"] is not None:
        asset_result = calculate_asset_based_value(
            total_assets=company_data["total_assets"],
            total_liabilities=company_data["total_liabilities"],
            diluted_shares_outstanding=diluted_shares_outstanding,
        )

    peer_data = {}
    for peer_ticker in peer_tickers:
        if peer_ticker.strip().upper() == ticker_symbol.strip().upper():
            continue
        peer_company_data = fetch_company_data(peer_ticker)
        peer_data[peer_company_data["ticker_symbol"]] = {
            "enterprise_value": peer_company_data["enterprise_value"],
            "ebitda": peer_company_data["ebitda"],
        }
    comps_result = None
    if company_data["ebitda"] is not None and company_data["ebitda"] > 0 and peer_data:
        comps_result = calculate_comparable_company_value(
            target_ebitda=company_data["ebitda"],
            target_cash=cash_and_cash_equivalents,
            target_debt=total_debt,
            target_diluted_shares=diluted_shares_outstanding,
            peer_data=peer_data,
        )

    return {
        "company_data": company_data,
        "assumptions": {
            "forecast_years": forecast_years,
            "annual_profit_revenue_growth": annual_profit_revenue_growth,
            "operating_margin_based_on_latest_report": operating_margin,
            "tax_rate_used": tax_rate,
            "depreciation_amortization_forecast": depreciation_amortization,
            "capital_expenditures_forecast": capital_expenditures,
            "change_in_net_working_capital_forecast": 0.0,
            "wacc": wacc,
            "terminal_growth_rate": terminal_growth_rate,
            "dividend_growth_rate": dividend_growth_rate,
            "cost_of_equity": cost_of_equity,
            "peer_tickers": list(peer_tickers),
        },
        "valuations": {
            "dcf": dcf_result,
            "dividend_discount": dividend_result,
            "asset_based": asset_result,
            "comparable_companies": comps_result,
        },
        "assumption_note": "Illustrative baseline: constant annual revenue growth and operating margin; latest reported D&A, capex, and historical tax rate; zero working-capital investment. Review assumptions before relying on any estimate.",
    }


def plot_valuation_chart(valuation_report: dict[str, Any], chart_path: str) -> str:
    """Draw daily candlesticks and horizontal lines for available price estimates."""
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    company_data = valuation_report["company_data"]
    valuation_results = valuation_report["valuations"]
    price_history = fetch_price_history(company_data["ticker_symbol"], period="1y", interval="1d")
    date_numbers = mdates.date2num(price_history.index.to_pydatetime())

    figure, axis = plt.subplots(figsize=(13, 7))
    up_color = "#16a34a"
    down_color = "#dc2626"
    candle_width_days = 0.65
    for date_number, (_, price_row) in zip(date_numbers, price_history.iterrows()):
        open_price = float(price_row["Open"])
        high_price = float(price_row["High"])
        low_price = float(price_row["Low"])
        close_price = float(price_row["Close"])
        candle_color = up_color if close_price >= open_price else down_color
        axis.vlines(date_number, low_price, high_price, color=candle_color, linewidth=0.8, zorder=2)
        candle_body_bottom = min(open_price, close_price)
        candle_body_height = abs(close_price - open_price)
        if candle_body_height == 0:
            candle_body_height = max(abs(open_price) * 0.0005, 0.001)
        axis.add_patch(Rectangle(
            (date_number - candle_width_days / 2, candle_body_bottom),
            candle_width_days, candle_body_height,
            facecolor=candle_color, edgecolor=candle_color, linewidth=0.7, zorder=3,
        ))

    line_colors = {
        "Market price": "#334155",
        "DCF estimate": "#2563eb",
        "Dividend discount": "#16a34a",
        "Asset based": "#f59e0b",
        "Comparable companies": "#9333ea",
    }
    latest_market_price = company_data["current_price"] or float(price_history["Close"].iloc[-1])
    price_levels = [("Market price", latest_market_price)]
    for line_label, model_key, value_key in [
        ("DCF estimate", "dcf", "intrinsic_value_per_share"),
        ("Dividend discount", "dividend_discount", "intrinsic_value_per_share"),
        ("Asset based", "asset_based", "intrinsic_value_per_share"),
        ("Comparable companies", "comparable_companies", "implied_value_per_share"),
    ]:
        model_result = valuation_results[model_key]
        if model_result is not None:
            price_levels.append((line_label, model_result[value_key]))
    for line_label, price_level in price_levels:
        axis.axhline(
            price_level, color=line_colors[line_label], linestyle="--", linewidth=1.2,
            label=f"{line_label}: {price_level:,.2f}", zorder=1,
        )

    axis.set_title(f"{company_data['ticker_symbol']} daily candlesticks and valuation estimates (1 year)")
    axis.set_ylabel(f"Adjusted share price ({company_data['currency'] or 'reported currency'})")
    axis.set_xlabel("Date")
    axis.xaxis_date()
    axis.xaxis.set_major_locator(mdates.AutoDateLocator())
    axis.xaxis.set_major_formatter(mdates.ConciseDateFormatter(axis.xaxis.get_major_locator()))
    axis.grid(axis="y", alpha=0.22)
    axis.legend(loc="best", fontsize=8, framealpha=0.9)
    figure.tight_layout()
    figure.savefig(chart_path, dpi=160, bbox_inches="tight")
    plt.show()
    plt.close(figure)
    return chart_path


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Calculate and plot company valuation estimates from a stock ticker.")
    parser.add_argument("ticker", nargs="?", help="Ticker such as AAPL; leave blank to be prompted")
    parser.add_argument("--peers", nargs="*", default=["MSFT", "GOOGL", "META"], help="Comparable-company tickers")
    parser.add_argument("--years", type=int, default=5, help="DCF forecast years")
    parser.add_argument("--growth", type=float, default=0.05, help="Annual revenue growth assumption as a decimal")
    parser.add_argument("--wacc", type=float, default=0.09, help="WACC as a decimal")
    parser.add_argument("--terminal-growth", type=float, default=0.025, help="Terminal growth rate as a decimal")
    parser.add_argument("--dividend-growth", type=float, default=0.03, help="Dividend growth assumption as a decimal")
    parser.add_argument("--cost-of-equity", type=float, default=0.09, help="Required equity return as a decimal")
    arguments = parser.parse_args()
    ticker_symbol = (arguments.ticker or input("Enter a stock ticker (for example AAPL): ")).strip().upper()
    if not ticker_symbol:
        parser.error("A stock ticker is required.")
    report = analyze_ticker(
        ticker_symbol,
        peer_tickers=arguments.peers,
        forecast_years=arguments.years,
        annual_profit_revenue_growth=arguments.growth,
        wacc=arguments.wacc,
        terminal_growth_rate=arguments.terminal_growth,
        dividend_growth_rate=arguments.dividend_growth,
        cost_of_equity=arguments.cost_of_equity,
    )
    print(json.dumps(report, indent=2, default=str))
    chart_path = f"{ticker_symbol}_valuation.png"
    plot_valuation_chart(report, chart_path)
    print(f"Chart saved to {chart_path}")
