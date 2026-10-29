# Stock valuation models

A Python project that fetches company data with yfinance, calculates four valuation estimates, and plots the per-share results against the latest share price.

## Run

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Run and type a ticker when prompted:

```bash
python valuation_models.py
```

Or pass a ticker directly:

```bash
python valuation_models.py AAPL
```

Optional assumptions can be supplied on the command line. Rates are decimals, so 0.05 means 5%.

```bash
python valuation_models.py AAPL --growth 0.05 --wacc 0.09 --terminal-growth 0.025 --peers MSFT GOOGL META
```

The calculation results print in the terminal, and a chart such as `AAPL_valuation.png` is saved in the current folder.

## How the models work

### Discounted cash flow (DCF)

DCF estimates the present value of future operating cash flows. This project uses free cash flow to the firm:

```text
FCFF = operating income × (1 - tax rate)
       + depreciation and amortization
       - capital expenditures
       - change in net working capital
```

Each year's FCFF is discounted using WACC. The terminal value approximates cash flows after the forecast period:

```text
Terminal value = final forecast FCFF × (1 + terminal growth) / (WACC - terminal growth)
Enterprise value = present value of forecast FCFF + present value of terminal value
Equity value = enterprise value + cash - debt
Value per share = equity value / diluted shares
```

The forecast details include revenue, total expenses, operating income, taxes, cash flow, discount factors, and present values so the math can be inspected.

### Dividend discount (DDM)

This version uses the Gordon growth model:

```text
Share value = next year's dividend per share / (cost of equity - perpetual dividend growth)
```

It only runs when the company has a recent dividend history. Constant dividend growth may not fit companies with irregular or no dividends.

### Asset based

The asset method starts with adjusted net asset value:

```text
Equity value = book assets - book liabilities
Value per share = equity value / diluted shares
```

It uses the reported book values as-is in this version. The model can be more informative for asset-heavy companies; book value may differ from what assets could be sold for.

### Comparable companies

This uses the median peer EV/EBITDA multiple:

```text
Peer EV/EBITDA = peer enterprise value / peer EBITDA
Implied enterprise value = median peer multiple × target EBITDA
Implied equity value = implied enterprise value + target cash - target debt
Value per share = implied equity value / diluted shares
```

Choose companies with similar businesses, growth, risk, and currency. The default peers are examples; provide more suitable tickers using `--peers`.

## Files

- `valuation_models.py`: command-line entry point; asks for a ticker and displays the chart.
- `stock_valuation/data.py`: yfinance data retrieval and shared validation.
- `stock_valuation/dcf.py`: FCFF discounted cash flow model.
- `stock_valuation/dividend_discount.py`: dividend discount model.
- `stock_valuation/asset_based.py`: adjusted net asset value model.
- `stock_valuation/comparable_companies.py`: peer multiple model.
- `stock_valuation/app.py`: combines the models and draws the chart.

## Assumptions and limits

Yahoo Finance provides historical and quote data, not reliable future assumptions. Defaults are illustrative: 5% revenue growth per year, latest reported operating margin held constant, latest reported tax rate (or 21% if unavailable), latest D&A and capex held constant, and zero change in working capital. Review and adjust assumptions before relying on any estimate. DCF requires WACC above terminal growth.

Yahoo Finance values follow the reported currency and scale. This project is for learning and research, not investment advice. Review yfinance and Yahoo Finance terms for data use.
