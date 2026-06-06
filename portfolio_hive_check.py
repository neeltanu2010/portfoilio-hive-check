import re
from io import StringIO
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from bs4 import BeautifulSoup

# ============================================================
# PORTFOLIO HIVE CHECK
# Streamlit app for Financify / Undoing the Madness of Money Bees
# ============================================================

st.set_page_config(
    page_title="Portfolio Hive Check",
    page_icon="🐝",
    layout="wide",
)

# -----------------------------
# STYLE
# -----------------------------
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; padding-bottom: 2rem;}
    .main-title {
        font-size: 44px;
        font-weight: 950;
        margin-bottom: 0px;
        letter-spacing: -1px;
    }
    .sub-title {
        font-size: 17px;
        color: #5f6368;
        margin-top: 2px;
        margin-bottom: 22px;
    }
    .bee-box {
        background: linear-gradient(135deg, #fff7cc 0%, #fffdf2 48%, #f4fff3 100%);
        border: 1px solid #f1d56d;
        border-radius: 18px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 4px 18px rgba(0,0,0,0.05);
    }
    .mode-box {
        background: white;
        border: 1px solid #ececec;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.045);
        min-height: 145px;
    }
    .small-muted {color: #777; font-size: 13px;}
    .pill {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 999px;
        background: #fff3b0;
        border: 1px solid #ead36a;
        font-size: 13px;
        font-weight: 700;
        margin-right: 7px;
    }
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #ececec;
        padding: 14px;
        border-radius: 16px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.04);
    }

    .backtest-hero {
        background: linear-gradient(135deg, #1f2937 0%, #111827 45%, #4b2e00 100%);
        color: white;
        border-radius: 22px;
        padding: 22px 24px;
        margin: 8px 0 18px 0;
        box-shadow: 0 10px 28px rgba(0,0,0,0.16);
    }
    .backtest-hero h2 {margin: 0 0 8px 0; font-size: 30px; font-weight: 900;}
    .backtest-hero p {margin: 0; color: #f7e8b3; font-size: 15px;}
    .info-card {
        background: linear-gradient(135deg, #f8fbff 0%, #ffffff 100%);
        border: 1px solid #dce7ff;
        border-left: 7px solid #3b82f6;
        border-radius: 18px;
        padding: 18px 20px;
        margin: 12px 0 18px 0;
        box-shadow: 0 5px 16px rgba(59,130,246,0.08);
    }
    .info-card h4 {margin: 0 0 8px 0; color: #1e3a8a;}
    .warning-card {
        background: linear-gradient(135deg, #fff7ed 0%, #fffdf7 100%);
        border: 1px solid #fed7aa;
        border-left: 7px solid #f97316;
        border-radius: 18px;
        padding: 16px 18px;
        margin: 12px 0;
    }
    .period-chip {
        display: inline-block;
        background: #111827;
        color: #fff7cc;
        padding: 6px 12px;
        border-radius: 999px;
        font-weight: 800;
        font-size: 13px;
        margin-right: 8px;
    }
    .compare-card {
        border-radius: 18px;
        padding: 14px 16px;
        min-height: 92px;
        color: #111827;
        box-shadow: 0 8px 22px rgba(0,0,0,0.09);
        border: 1px solid rgba(255,255,255,0.75);
        margin-bottom: 8px;
    }
    .compare-card h4 {margin: 0 0 6px 0; font-size: 17px; font-weight: 900;}
    .compare-card p {margin: 0; color: #374151; font-size: 13px;}
    .nav-radio-card {
        background: linear-gradient(135deg, #fff7cc 0%, #f5fbff 100%);
        border: 1px solid #f1d56d;
        border-radius: 18px;
        padding: 12px 16px;
        margin: 10px 0 18px 0;
        box-shadow: 0 4px 16px rgba(0,0,0,0.05);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="main-title">🐝 Portfolio Hive Check</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">A clean portfolio checker for money bees who want honey, not financial hornets.</div>',
    unsafe_allow_html=True,
)

# -----------------------------
# DEFAULT STOCK LIST
# -----------------------------
DEFAULT_TICKERS = [
    "ZYDUSLIFE", "DRREDDY", "OFSS", "INFY", "NTPC", "ACE", "GODFRYPHLP",
    "ASIANPAINT", "PIDILITIND", "GRAVITA", "PETRONET", "CRISIL", "POLYCAB",
    "SCHAEFFLER", "CUMMINSIND", "CHAMBLFERT", "DHANUKA", "KIRLOSENG",
    "ARE&M", "JKCEMENT"
]

# -----------------------------
# HELPERS
# -----------------------------
def clean_ticker(raw: str) -> str:
    ticker = str(raw).strip().upper()
    ticker = ticker.replace(".NS", "")
    ticker = ticker.replace(" ", "")
    return ticker


def yf_symbol(ticker: str) -> str:
    return f"{clean_ticker(ticker)}.NS"


def parse_number(value):
    """Convert Screener-like text values into float. Returns np.nan if unavailable."""
    if value is None:
        return np.nan
    text = str(value).strip()
    if text in ["", "-", "--", "nan", "None", "NaN"]:
        return np.nan

    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]

    text = (
        text.replace(",", "")
        .replace("%", "")
        .replace("₹", "")
        .replace("Cr.", "")
        .replace("Cr", "")
        .replace("x", "")
        .replace("+", "")
        .strip()
    )
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return np.nan
    try:
        val = float(match.group(0))
        return -val if negative else val
    except Exception:
        return np.nan


def safe_mean(values):
    arr = pd.Series(values, dtype="float64").replace([np.inf, -np.inf], np.nan).dropna()
    return float(arr.mean()) if len(arr) else np.nan


def safe_min(values):
    arr = pd.Series(values, dtype="float64").replace([np.inf, -np.inf], np.nan).dropna()
    return float(arr.min()) if len(arr) else np.nan


def latest_value(values):
    arr = pd.Series(values, dtype="float64").replace([np.inf, -np.inf], np.nan).dropna()
    return float(arr.iloc[-1]) if len(arr) else np.nan


def cagr(values):
    arr = pd.Series(values, dtype="float64").replace([np.inf, -np.inf], np.nan).dropna().tolist()
    if len(arr) < 2:
        return np.nan
    start = arr[0]
    end = arr[-1]
    years = len(arr) - 1
    if start <= 0 or end <= 0 or years <= 0:
        return np.nan
    try:
        return ((end / start) ** (1 / years)) - 1
    except Exception:
        return np.nan


def latest_growth(values):
    """Latest YoY growth using the last two available annual values."""
    arr = pd.Series(values, dtype="float64").replace([np.inf, -np.inf], np.nan).dropna().tolist()
    if len(arr) < 2:
        return np.nan
    prev, curr = arr[-2], arr[-1]
    if prev == 0 or pd.isna(prev) or pd.isna(curr):
        return np.nan
    return (curr - prev) / abs(prev)


def normalize_label(text):
    return re.sub(r"\s+", " ", str(text).strip().lower())


def clean_table(df):
    """Clean dataframe returned by pandas.read_html."""
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how="all")
    return df


def get_section_table(soup, section_ids):
    """Target Screener sections directly: profit-loss, balance-sheet, cash-flow, ratios."""
    for section_id in section_ids:
        section = soup.find("section", id=section_id)
        if section is None:
            continue
        table = section.find("table")
        if table is None:
            continue
        try:
            frames = pd.read_html(StringIO(str(table)))
            if frames:
                return clean_table(frames[0])
        except Exception:
            pass
    return pd.DataFrame()


def table_row_values(df, possible_names, last_n=5, exclude_ttm=True, exact=False):
    """Return last N annual row values from a specific table only."""
    if df is None or df.empty or df.shape[1] < 2:
        return []

    possible_names = [normalize_label(x) for x in possible_names]
    first_col = df.columns[0]

    for _, row in df.iterrows():
        label = normalize_label(row[first_col])
        if exact:
            matched = any(label == name for name in possible_names)
        else:
            matched = any(name in label for name in possible_names)

        if not matched:
            continue

        values = []
        for col in df.columns[1:]:
            col_text = str(col).strip().lower()
            if exclude_ttm and "ttm" in col_text:
                continue
            val = parse_number(row[col])
            if not pd.isna(val):
                values.append(val)
        return values[-last_n:]

    return []


def find_metric_from_text(html, labels):
    """Find top-ratio values such as Stock P/E from Screener HTML text."""
    soup = BeautifulSoup(html, "html.parser")
    text = re.sub(r"\s+", " ", soup.get_text(" "))
    for label in labels:
        pattern = rf"{re.escape(label)}\s*(-?\d+(?:\.\d+)?)"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return parse_number(match.group(1))
    return np.nan


@st.cache_data(ttl=60 * 60)
def fetch_screener_data(ticker, consolidated=True):
    ticker = clean_ticker(ticker)
    urls = []
    if consolidated:
        urls.append(f"https://www.screener.in/company/{ticker}/consolidated/")
    urls.append(f"https://www.screener.in/company/{ticker}/")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125 Safari/537.36"
    }

    last_error = None
    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code != 200:
                last_error = f"HTTP {response.status_code}"
                continue

            html = response.text
            soup = BeautifulSoup(html, "html.parser")

            profit_loss = get_section_table(soup, ["profit-loss"])
            balance_sheet = get_section_table(soup, ["balance-sheet"])
            cash_flow = get_section_table(soup, ["cash-flow"])
            ratios = get_section_table(soup, ["ratios"])

            all_tables = []
            try:
                all_tables = [clean_table(t) for t in pd.read_html(StringIO(html))]
            except Exception:
                all_tables = []

            if profit_loss.empty and balance_sheet.empty and cash_flow.empty and not all_tables:
                last_error = "No financial tables found"
                continue

            company_name = ticker
            h1 = soup.find("h1")
            if h1:
                company_name = h1.get_text(" ", strip=True)

            return {
                "ticker": ticker,
                "company_name": company_name,
                "url": url,
                "html": html,
                "tables": all_tables,
                "profit_loss": profit_loss,
                "balance_sheet": balance_sheet,
                "cash_flow": cash_flow,
                "ratios": ratios,
                "error": None,
            }
        except Exception as e:
            last_error = str(e)

    return {
        "ticker": ticker,
        "company_name": ticker,
        "url": "",
        "html": "",
        "tables": [],
        "profit_loss": pd.DataFrame(),
        "balance_sheet": pd.DataFrame(),
        "cash_flow": pd.DataFrame(),
        "ratios": pd.DataFrame(),
        "error": last_error or "Unknown error",
    }


@st.cache_data(ttl=60 * 60)
def fetch_yfinance_data(ticker):
    """Fallback data from yfinance: PE and momentum mainly."""
    symbol = yf_symbol(ticker)
    out = {"pe": np.nan, "eps_growth": np.nan, "momentum_6m": np.nan, "momentum_12m": np.nan, "issue": ""}
    try:
        tk = yf.Ticker(symbol)
        try:
            info = tk.info or {}
            out["pe"] = parse_number(info.get("trailingPE", np.nan))
            out["eps_growth"] = parse_number(info.get("earningsQuarterlyGrowth", np.nan))
        except Exception:
            pass

        hist = tk.history(period="1y", auto_adjust=True)
        if hist is not None and not hist.empty and "Close" in hist.columns:
            close = hist["Close"].dropna()
            if len(close) > 126:
                out["momentum_6m"] = (close.iloc[-1] / close.iloc[-126]) - 1
            if len(close) > 250:
                out["momentum_12m"] = (close.iloc[-1] / close.iloc[0]) - 1
    except Exception as e:
        out["issue"] = str(e)
    return out


def calculate_roe_yearly_from_pat_and_networth(pat_values, equity_values, reserves_values, total_equity_values=None):
    """
    ROE fix requested:
    - Do not use a single PAT/net-worth fallback number.
    - Take PAT and net worth for last 5 years separately.
    - Calculate yearly ROE separately = PAT / Net Worth * 100.
    - Then take average ROE.
    """
    pat5 = pd.Series(pat_values, dtype="float64").replace([np.inf, -np.inf], np.nan).dropna().tolist()[-5:]

    if total_equity_values:
        networth5 = pd.Series(total_equity_values, dtype="float64").replace([np.inf, -np.inf], np.nan).dropna().tolist()[-5:]
    else:
        equity5 = pd.Series(equity_values, dtype="float64").replace([np.inf, -np.inf], np.nan).dropna().tolist()[-5:]
        reserves5 = pd.Series(reserves_values, dtype="float64").replace([np.inf, -np.inf], np.nan).dropna().tolist()[-5:]
        n0 = min(len(equity5), len(reserves5))
        equity5 = equity5[-n0:]
        reserves5 = reserves5[-n0:]
        networth5 = [e + r for e, r in zip(equity5, reserves5)]

    n = min(len(pat5), len(networth5))
    if n == 0:
        return [], np.nan

    pat5 = pat5[-n:]
    networth5 = networth5[-n:]

    yearly_roe = []
    for p, nw in zip(pat5, networth5):
        if not pd.isna(p) and not pd.isna(nw) and nw > 0:
            yearly_roe.append((p / nw) * 100)

    return yearly_roe, safe_mean(yearly_roe)


def analyse_stock(ticker, consolidated=True):
    fetched = fetch_screener_data(ticker, consolidated=consolidated)
    yfdata = fetch_yfinance_data(ticker)

    if fetched["error"]:
        return {
            "Stock": clean_ticker(ticker), "Company": clean_ticker(ticker), "Score": 0,
            "Signal": "DATA ERROR", "BuyingZone": "⚠️ CHECK MANUALLY", "PE": yfdata.get("pe", np.nan),
            "PEG": np.nan, "LatestEPSGrowth": yfdata.get("eps_growth", np.nan), "Momentum6M": yfdata.get("momentum_6m", np.nan),
            "ROEAvg": np.nan, "CashConversion": np.nan, "Issue": fetched["error"], "Checks": [], "URL": ""
        }

    html = fetched["html"]
    pl = fetched["profit_loss"]
    bs = fetched["balance_sheet"]
    cf = fetched["cash_flow"]
    ratios_table = fetched["ratios"]

    # -----------------------------
    # STRICT ANNUAL TARGETING FIX
    # -----------------------------
    # PAT must come only from latest annual P&L statement on Screener.
    sales = table_row_values(pl, ["sales", "revenue from operations", "revenue"], last_n=5, exclude_ttm=True)
    pat = table_row_values(pl, ["net profit", "profit after tax", "profit for the period"], last_n=5, exclude_ttm=True)
    eps = table_row_values(pl, ["eps in rs", "eps", "earning per share", "earnings per share"], last_n=5, exclude_ttm=True)

    # CFO must come only from annual Cash Flow statement on Screener.
    cfo = table_row_values(cf, ["cash from operating activity", "cash from operations", "net cash from operating activities"], last_n=5, exclude_ttm=True)

    # Balance sheet values for D/E and yearly ROE calculation.
    borrowings = table_row_values(bs, ["borrowings", "debt"], last_n=5, exclude_ttm=True)
    equity = table_row_values(bs, ["equity capital", "equity share capital", "share capital"], last_n=5, exclude_ttm=True)
    reserves = table_row_values(bs, ["reserves", "other equity"], last_n=5, exclude_ttm=True)
    total_equity = table_row_values(bs, ["total equity", "shareholders funds", "shareholder funds"], last_n=5, exclude_ttm=True)

    # ROCE/ROE from ratios section, if Screener provides it.
    roce = table_row_values(ratios_table, ["roce", "return on capital employed"], last_n=5, exclude_ttm=True)
    screener_roe = table_row_values(ratios_table, ["roe", "return on equity"], last_n=5, exclude_ttm=True)

    pe = find_metric_from_text(html, ["Stock P/E", "P/E"])
    if pd.isna(pe) or pe <= 0:
        pe = yfdata.get("pe", np.nan)

    sales_cagr = cagr(sales)
    pat_cagr = cagr(pat)

    # PEG: latest EPS growth first, then yfinance earnings growth, then latest PAT growth.
    eps_growth = latest_growth(eps)
    eps_source = "Screener annual EPS growth"
    if pd.isna(eps_growth):
        eps_growth = yfdata.get("eps_growth", np.nan)
        eps_source = "YFinance earnings growth fallback"
    if pd.isna(eps_growth):
        eps_growth = latest_growth(pat)
        eps_source = "Annual PAT growth fallback"

    peg = pe / (eps_growth * 100) if not pd.isna(pe) and not pd.isna(eps_growth) and eps_growth > 0 else np.nan

    roce_avg = safe_mean(roce)
    roce_min = safe_min(roce)

    # -----------------------------
    # ROE FIX
    # -----------------------------
    # First use Screener ROE if available. If missing, calculate yearly ROE from annual PAT and annual net worth.
    roe_avg = safe_mean(screener_roe)
    roe_min = safe_min(screener_roe)
    roe_source = "Screener ROE"
    calculated_roe_values = []

    if pd.isna(roe_avg):
        calculated_roe_values, roe_avg = calculate_roe_yearly_from_pat_and_networth(
            pat_values=pat,
            equity_values=equity,
            reserves_values=reserves,
            total_equity_values=total_equity,
        )
        roe_min = safe_min(calculated_roe_values)
        roe_source = "Calculated yearly: PAT / Net Worth, then 5Y average"

    latest_borrowings = latest_value(borrowings)
    latest_equity = latest_value(equity)
    latest_reserves = latest_value(reserves)
    latest_total_equity = latest_value(total_equity)

    if not pd.isna(latest_total_equity) and latest_total_equity > 0:
        net_worth = latest_total_equity
    else:
        net_worth = 0
        if not pd.isna(latest_equity):
            net_worth += latest_equity
        if not pd.isna(latest_reserves):
            net_worth += latest_reserves

    de_analytical = latest_borrowings / net_worth if net_worth > 0 and not pd.isna(latest_borrowings) else np.nan

    # -----------------------------
    # CASH CONVERSION FIX
    # -----------------------------
    # Latest annual CFO from Cash Flow / Latest annual PAT from P&L only.
    latest_pat = latest_value(pat)
    latest_cfo = latest_value(cfo)
    cash_conversion = latest_cfo / latest_pat if not pd.isna(latest_cfo) and not pd.isna(latest_pat) and latest_pat != 0 else np.nan

    earnings_yield = 1 / pe if not pd.isna(pe) and pe > 0 else np.nan
    momentum_6m = yfdata.get("momentum_6m", np.nan)
    momentum_12m = yfdata.get("momentum_12m", np.nan)

    # -----------------------------
    # SCORECARD
    # -----------------------------
    score = 0
    checks = []

    def add_check(name, passed, points, value, target):
        nonlocal score
        if passed:
            score += points
        checks.append({
            "Metric": name,
            "Value": value,
            "Target": target,
            "Status": "✅ Pass" if passed else "❌ Fail",
            "Points": points if passed else 0,
        })

    add_check("Sales CAGR", sales_cagr > 0.10 if not pd.isna(sales_cagr) else False, 10, sales_cagr, "> 10%")
    add_check("PAT CAGR", pat_cagr > 0.10 if not pd.isna(pat_cagr) else False, 10, pat_cagr, "> 10%")
    add_check("ROCE Average", roce_avg > 20 if not pd.isna(roce_avg) else False, 10, roce_avg, "> 20%")
    add_check("ROCE Minimum", roce_min > 15 if not pd.isna(roce_min) else False, 10, roce_min, "> 15%")
    add_check("ROE Average", roe_avg > 20 if not pd.isna(roe_avg) else False, 10, roe_avg, "> 20%")
    add_check("ROE Minimum", roe_min > 15 if not pd.isna(roe_min) else False, 10, roe_min, "> 15%")
    add_check("D/E Analytical Ratio", de_analytical < 0.20 if not pd.isna(de_analytical) else False, 10, de_analytical, "< 0.20")
    add_check("Cash Conversion Ratio", cash_conversion > 1 if not pd.isna(cash_conversion) else False, 15, cash_conversion, "Latest annual CFO / latest annual PAT > 1")
    add_check("PE", pe < 25 if not pd.isna(pe) else False, 5, pe, "< 25")
    add_check("PEG", peg < 1.5 if not pd.isna(peg) else False, 10, peg, "< 1.5")

    if score >= 80:
        signal = "🟢 STRONG HIVE"
    elif score >= 60:
        signal = "🟡 DECENT HIVE"
    elif score >= 40:
        signal = "🟠 WEAK HIVE"
    else:
        signal = "🔴 HORNET ZONE"

    if not pd.isna(pe) and pe < 25 and not pd.isna(peg) and peg < 1.5:
        buying_zone = "🟢 Sweet Honey Zone"
    elif not pd.isna(pe) and pe < 25 and score >= 60:
        buying_zone = "🟡 Fair Honey Zone"
    elif not pd.isna(pe) and pe >= 25:
        buying_zone = "🔴 Expensive Buzz"
    else:
        buying_zone = "⚠️ Valuation Missing"

    issue = ""
    if pd.isna(pe):
        issue += "PE missing. "
    if pd.isna(peg):
        issue += "PEG missing due to EPS growth missing/negative. "
    if pd.isna(roe_avg):
        issue += "ROE missing because PAT/net worth annual data was unavailable. "
    if pd.isna(cash_conversion):
        issue += "Cash conversion missing because latest annual CFO or PAT was unavailable. "

    return {
        "Stock": clean_ticker(ticker),
        "Company": fetched["company_name"],
        "Score": score,
        "Signal": signal,
        "BuyingZone": buying_zone,
        "PE": pe,
        "PEG": peg,
        "LatestEPSGrowth": eps_growth,
        "EPSSource": eps_source,
        "EarningsYield": earnings_yield,
        "SalesCAGR": sales_cagr,
        "PATCAGR": pat_cagr,
        "ROCEAvg": roce_avg,
        "ROEMin": roe_min,
        "ROEAvg": roe_avg,
        "ROESource": roe_source,
        "DEAnalytical": de_analytical,
        "CashConversion": cash_conversion,
        "LatestAnnualPAT": latest_pat,
        "LatestAnnualCFO": latest_cfo,
        "Momentum6M": momentum_6m,
        "Momentum12M": momentum_12m,
        "URL": fetched["url"],
        "Issue": issue.strip(),
        "Checks": checks,
    }


def format_percent(x):
    if pd.isna(x):
        return "NA"
    return f"{x * 100:.2f}%"


def format_number(x):
    if pd.isna(x):
        return "NA"
    return f"{x:.2f}"


def make_display_df(df):
    show = df.copy()
    for col in ["EarningsYield", "SalesCAGR", "PATCAGR", "LatestEPSGrowth", "Momentum6M", "Momentum12M"]:
        if col in show.columns:
            show[col] = show[col].apply(format_percent)
    for col in ["PE", "PEG", "ROCEAvg", "ROEAvg", "ROEMin", "DEAnalytical", "CashConversion", "LatestAnnualPAT", "LatestAnnualCFO"]:
        if col in show.columns:
            show[col] = show[col].apply(format_number)
    return show


def conservative_allocation(df):
    """Strict valuation mode: can keep cash if stocks do not qualify."""
    out = df.copy()
    eligible = (
        (out["Score"] >= 60) &
        (out["PE"].notna()) & (out["PE"] < 25) &
        (out["PEG"].notna()) & (out["PEG"] < 1.5) &
        (out["CashConversion"].notna()) & (out["CashConversion"] > 1)
    )
    out["Eligible"] = eligible
    out["ValuationDiscipline"] = np.where(eligible, "Eligible", "Cash preferred")
    out["RawWeight"] = 0.0
    out.loc[eligible, "RawWeight"] = (
        out.loc[eligible, "Score"].clip(lower=0) * 0.55 +
        (1 / out.loc[eligible, "PE"].replace(0, np.nan)).fillna(0) * 100 * 0.25 +
        (1 / out.loc[eligible, "PEG"].replace(0, np.nan)).fillna(0) * 10 * 0.20
    )

    invested_pct = min(100, max(0, len(out[eligible]) * 12.5))
    total_raw = out["RawWeight"].sum()
    if total_raw > 0:
        out["Conservative Allocation %"] = out["RawWeight"] / total_raw * invested_pct
    else:
        out["Conservative Allocation %"] = 0.0

    cash = max(0, 100 - out["Conservative Allocation %"].sum())
    out.drop(columns=["RawWeight"], inplace=True)
    return out, cash


def aggressive_allocation(df):
    """Momentum mode: always invested with minimum allocation."""
    out = df.copy()
    n = len(out)
    if n == 0:
        out["Aggressive Allocation %"] = []
        return out

    score_norm = out["Score"].fillna(0) / max(out["Score"].max(), 1)
    momentum = out["Momentum6M"].fillna(0)
    if momentum.max() == momentum.min():
        momentum_norm = pd.Series([1 / n] * n, index=out.index)
    else:
        momentum_norm = (momentum - momentum.min()) / (momentum.max() - momentum.min())
    ey_norm = out["EarningsYield"].fillna(0)
    if ey_norm.max() > 0:
        ey_norm = ey_norm / ey_norm.max()

    raw = 0.25 * score_norm + 0.60 * momentum_norm + 0.15 * ey_norm
    raw = raw.replace([np.inf, -np.inf], np.nan).fillna(0)
    if raw.sum() <= 0:
        out["Aggressive Allocation %"] = 100 / n
        return out

    weights = raw / raw.sum()
    min_alloc = min(0.02, 1 / n)
    weights = weights.clip(lower=min_alloc)
    weights = weights / weights.sum()
    out["Aggressive Allocation %"] = weights * 100
    return out



# -----------------------------
# BACKTESTER HELPERS
# -----------------------------
BACKTEST_PERIODS = {
    "2008 Recession": ("2008-01-01", "2009-03-09"),
    "Covid-19 Crash": ("2020-02-01", "2020-04-30"),
    "Custom Date Range": (None, None),
}

BENCHMARKS = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "Nifty Midcap 100": "^CNXMCAP",
    "Nifty Smallcap 100": "^CNXSC",
}

BENCHMARK_CARD_STYLES = {
    "Nifty 50": "linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%)",
    "Sensex": "linear-gradient(135deg, #fee2e2 0%, #fff7ed 100%)",
    "Nifty Midcap 100": "linear-gradient(135deg, #dcfce7 0%, #f0fdf4 100%)",
    "Nifty Smallcap 100": "linear-gradient(135deg, #f3e8ff 0%, #faf5ff 100%)",
}

PLOT_COLORS = ["#f59e0b", "#2563eb", "#ef4444", "#10b981", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"]


def get_adjusted_close(downloaded):
    """Robustly extract adjusted/close prices from yfinance output."""
    if downloaded is None or downloaded.empty:
        return pd.DataFrame()
    if isinstance(downloaded.columns, pd.MultiIndex):
        first_level = list(downloaded.columns.get_level_values(0).unique())
        if "Adj Close" in first_level:
            return downloaded["Adj Close"].copy()
        if "Close" in first_level:
            return downloaded["Close"].copy()
    if "Adj Close" in downloaded.columns:
        return downloaded[["Adj Close"]].rename(columns={"Adj Close": "Close"})
    if "Close" in downloaded.columns:
        return downloaded[["Close"]]
    return pd.DataFrame()


@st.cache_data(ttl=60 * 60)
def download_backtest_prices(symbols, start_date, end_date):
    """Download prices for portfolio stocks plus benchmarks."""
    symbols = list(dict.fromkeys([s for s in symbols if s]))
    try:
        data = yf.download(
            symbols,
            start=start_date,
            end=end_date,
            auto_adjust=False,
            progress=False,
            group_by="column",
            threads=True,
        )
        prices = get_adjusted_close(data)
        if isinstance(prices, pd.Series):
            prices = prices.to_frame(symbols[0])
        prices = prices.ffill().dropna(how="all")
        return prices
    except Exception:
        return pd.DataFrame()


def calculate_backtest_metrics(series):
    series = pd.Series(series, dtype="float64").dropna()
    if len(series) < 3:
        return {"Return %": np.nan, "Sharpe Ratio": np.nan, "Max Drawdown %": np.nan, "Final Value": np.nan}

    returns = series.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
    total_return = (series.iloc[-1] / series.iloc[0] - 1) * 100
    volatility = returns.std()
    sharpe = (returns.mean() / volatility) * np.sqrt(252) if volatility and volatility > 0 else np.nan
    roll_max = series.cummax()
    max_dd = ((series / roll_max) - 1).min() * 100

    return {
        "Return %": total_return,
        "Sharpe Ratio": sharpe,
        "Max Drawdown %": max_dd,
        "Final Value": series.iloc[-1],
    }


def build_weight_series(df, allocation_column):
    weights = df[["Stock", allocation_column]].copy()
    weights["Symbol"] = weights["Stock"].apply(yf_symbol)
    weights["Weight"] = pd.to_numeric(weights[allocation_column], errors="coerce").fillna(0) / 100
    weights = weights[weights["Weight"] > 0]
    return weights.set_index("Symbol")["Weight"]


def run_portfolio_backtest(df, allocation_column, start_date, end_date, selected_benchmarks, initial_value=100):
    """Backtest current allocation weights against user-selected benchmarks."""
    stock_weights = build_weight_series(df, allocation_column)
    if stock_weights.empty:
        return pd.DataFrame(), pd.DataFrame(), "No eligible stock weights found for this allocation mode."

    selected_benchmarks = selected_benchmarks or []
    benchmark_symbols = [BENCHMARKS[b] for b in selected_benchmarks if b in BENCHMARKS]
    symbols = stock_weights.index.tolist() + benchmark_symbols
    prices = download_backtest_prices(symbols, start_date, end_date)
    if prices.empty:
        return pd.DataFrame(), pd.DataFrame(), "Could not download price data from yfinance for this period."

    missing = [s for s in stock_weights.index if s not in prices.columns]
    usable_weights = stock_weights.drop(index=missing, errors="ignore")
    if usable_weights.empty:
        return pd.DataFrame(), pd.DataFrame(), "None of the selected portfolio stocks had usable price data for this period."

    usable_weights = usable_weights / usable_weights.sum()
    stock_prices = prices[usable_weights.index].dropna(how="all").ffill()
    daily_returns = stock_prices.pct_change().replace([np.inf, -np.inf], np.nan).dropna(how="all").fillna(0)
    if daily_returns.empty:
        return pd.DataFrame(), pd.DataFrame(), "Not enough daily price data for portfolio backtest."

    portfolio_ret = daily_returns.dot(usable_weights)
    portfolio_curve = (1 + portfolio_ret).cumprod() * initial_value
    curves = pd.DataFrame({"Portfolio": portfolio_curve})

    missing_benchmarks = []
    for benchmark_name in selected_benchmarks:
        symbol = BENCHMARKS.get(benchmark_name)
        if not symbol:
            continue
        if symbol in prices.columns:
            benchmark_series = prices[symbol].reindex(curves.index).ffill().dropna()
            if len(benchmark_series) > 2:
                curves[benchmark_name] = (benchmark_series / benchmark_series.iloc[0]) * initial_value
            else:
                missing_benchmarks.append(benchmark_name)
        else:
            missing_benchmarks.append(benchmark_name)

    curves = curves.dropna(how="all")

    metrics = []
    for name in curves.columns:
        m = calculate_backtest_metrics(curves[name])
        metrics.append({"Asset": name, **m})
    metrics_df = pd.DataFrame(metrics)

    notes = []
    if missing:
        notes.append("Missing price data ignored for: " + ", ".join([x.replace(".NS", "") for x in missing]))
    if missing_benchmarks:
        notes.append("Benchmark data unavailable or too short for: " + ", ".join(missing_benchmarks))
    return curves, metrics_df, " | ".join(notes)


def plot_backtest_curves(curves):
    fig = go.Figure()
    for i, col in enumerate(curves.columns):
        fig.add_trace(
            go.Scatter(
                x=curves.index,
                y=curves[col],
                mode="lines",
                name=col,
                line=dict(width=4 if col == "Portfolio" else 3, color=PLOT_COLORS[i % len(PLOT_COLORS)]),
                hovertemplate="%{x|%d %b %Y}<br>₹%{y:.2f}<extra>%{fullData.name}</extra>",
            )
        )
    fig.update_layout(
        title="Portfolio vs selected benchmarks",
        xaxis_title="Date",
        yaxis_title="Growth of ₹100",
        hovermode="x unified",
        template="plotly_white",
        height=500,
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(248,250,252,0.95)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=75, b=20),
        font=dict(size=13),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(148,163,184,0.20)")
    fig.update_yaxes(showgrid=True, gridcolor="rgba(148,163,184,0.20)")
    return fig


def plot_metric_bars(metrics_df, metric_col, title, suffix=""):
    fig = go.Figure()
    colors = [PLOT_COLORS[i % len(PLOT_COLORS)] for i in range(len(metrics_df))]
    fig.add_trace(
        go.Bar(
            x=metrics_df["Asset"],
            y=metrics_df[metric_col],
            text=[f"{v:.2f}{suffix}" if pd.notna(v) else "NA" for v in metrics_df[metric_col]],
            textposition="outside",
            marker=dict(color=colors, line=dict(color="rgba(17,24,39,0.15)", width=1.2)),
            hovertemplate="%{x}<br>%{y:.2f}" + suffix + "<extra></extra>",
        )
    )
    fig.update_layout(
        title=title,
        xaxis_title="",
        yaxis_title=metric_col,
        template="plotly_white",
        height=380,
        paper_bgcolor="rgba(255,255,255,0)",
        plot_bgcolor="rgba(255,251,235,0.35)",
        margin=dict(l=20, r=20, t=65, b=20),
        font=dict(size=13),
    )
    fig.update_yaxes(showgrid=True, gridcolor="rgba(148,163,184,0.20)")
    return fig

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("🐝 Hive Input")
raw_tickers = st.sidebar.text_area(
    "Enter NSE tickers",
    value=", ".join(DEFAULT_TICKERS),
    height=170,
    help="Use Screener symbols without .NS. Example: INFY, NTPC, ARE&M, ZYDUSLIFE",
)
consolidated = st.sidebar.checkbox("Prefer consolidated data", value=True)
run_button = st.sidebar.button("Run Hive Check", type="primary")

st.sidebar.markdown("---")
st.sidebar.caption("Educational screening only. Not investment advice. Bees can sting. Markets can too.")

# -----------------------------
# INTRO
# -----------------------------
st.markdown(
    """
    <div class="bee-box">
    <span class="pill">Quality</span><span class="pill">Valuation</span><span class="pill">CFO/PAT</span><span class="pill">Momentum</span><br><br>
    <b>What this tool checks:</b> Sales growth, PAT growth, ROCE, ROE, D/E analytical ratio, PE, PEG using latest EPS growth, and cash conversion ratio only.<br>
    <span class="small-muted">Cash conversion is strictly latest annual CFO from cash flow divided by latest annual PAT from P&L.</span>
    </div>
    """,
    unsafe_allow_html=True,
)

m1, m2 = st.columns(2)
with m1:
    st.markdown(
        """
        <div class="mode-box">
        <h4>🛡️ Conservative Allocation</h4>
        Follows valuation strictly. It does <b>not</b> force full investment. If stocks are expensive or weak, it keeps cash.
        <br><br><span class="small-muted">Best for: lower risk, valuation discipline, fewer honey traps.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m2:
    st.markdown(
        """
        <div class="mode-box">
        <h4>🚀 Aggressive Allocation</h4>
        Always stays invested. It gives more importance to price momentum, so risk and return can both buzz louder.
        <br><br><span class="small-muted">Best for: higher risk appetite and momentum-led portfolio action.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# SESSION STATE FIX
# -----------------------------
# Streamlit reruns the whole script whenever you change selectbox / tabs.
# Earlier, results existed only inside `if run_button:`, so Deep Check selectbox
# caused the app to reset. Now results are saved in session_state and reused.
if "hive_results" not in st.session_state:
    st.session_state["hive_results"] = None

if run_button:
    tickers = [clean_ticker(x) for x in re.split(r"[,\n]+", raw_tickers) if clean_ticker(x)]
    tickers = list(dict.fromkeys(tickers))
    if not tickers:
        st.error("Please enter at least one ticker.")
        st.stop()

    results = []
    progress = st.progress(0)
    status = st.empty()

    for i, ticker in enumerate(tickers):
        status.info(f"Checking hive for {ticker}...")
        results.append(analyse_stock(ticker, consolidated=consolidated))
        progress.progress((i + 1) / len(tickers))

    status.success("Hive check completed. The bees have returned with data.")
    st.session_state["hive_results"] = results

# Render existing results even after widgets trigger a rerun.
if st.session_state.get("hive_results"):
    results = st.session_state["hive_results"]

    df = pd.DataFrame([{k: v for k, v in r.items() if k != "Checks"} for r in results])
    df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

    cons_df, cash_pct = conservative_allocation(df)
    aggr_df = aggressive_allocation(df)

    df["Conservative Allocation %"] = cons_df["Conservative Allocation %"].round(2)
    df["Aggressive Allocation %"] = aggr_df["Aggressive Allocation %"].round(2)
    df["Conservative Status"] = cons_df["ValuationDiscipline"]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Stocks Checked", len(df))
    c2.metric("Average Score", f"{df['Score'].mean():.1f}/100")
    c3.metric("Strong Hives", int(df["Signal"].str.contains("STRONG", na=False).sum()))
    c4.metric("Avg PE", "NA" if df["PE"].dropna().empty else f"{df['PE'].mean():.1f}")
    c5.metric("Conservative Cash", f"{cash_pct:.1f}%")

    st.markdown('<div class="nav-radio-card"><b>Choose dashboard page</b></div>', unsafe_allow_html=True)
    page_choice = st.radio(
        "Choose dashboard page",
        ["📊 Summary", "🛡️ Conservative", "🚀 Aggressive", "📉 Backtester", "🔍 Deep Check"],
        horizontal=True,
        label_visibility="collapsed",
        key="active_dashboard_page",
    )

    if page_choice == "📊 Summary":
        st.subheader("📊 Portfolio Hive Summary")
        show = make_display_df(df)
        cols = [
            "Stock", "Company", "Score", "Signal", "BuyingZone", "PE", "PEG", "LatestEPSGrowth", "EPSSource",
            "SalesCAGR", "PATCAGR", "ROCEAvg", "ROEAvg", "ROESource", "DEAnalytical", "CashConversion",
            "LatestAnnualPAT", "LatestAnnualCFO", "Momentum6M", "Issue"
        ]
        st.dataframe(show[[c for c in cols if c in show.columns]], use_container_width=True, hide_index=True)

        left, right = st.columns(2)
        with left:
            st.caption("Score ranking")
            st.bar_chart(df.set_index("Stock")["Score"].sort_values(ascending=False))
        with right:
            st.caption("6-month momentum ranking")
            mom = df.set_index("Stock")["Momentum6M"].dropna().sort_values(ascending=False)
            if not mom.empty:
                st.bar_chart(mom)
            else:
                st.info("Momentum data unavailable from yfinance.")

    if page_choice == "🛡️ Conservative":
        st.subheader("🛡️ Conservative Allocation — valuation first, cash allowed")
        st.info("Rule: score ≥ 60, PE < 25, PEG < 1.5, and latest annual CFO/PAT > 1. Stocks failing this are not forced into allocation.")
        cons_show = make_display_df(df.copy())
        st.dataframe(
            cons_show[["Stock", "Score", "Signal", "BuyingZone", "PE", "PEG", "CashConversion", "Conservative Status", "Conservative Allocation %"]],
            use_container_width=True,
            hide_index=True,
        )
        chart_data = df.set_index("Stock")["Conservative Allocation %"].sort_values(ascending=False)
        if cash_pct > 0:
            chart_data.loc["CASH / WAIT"] = cash_pct
        st.bar_chart(chart_data)

    if page_choice == "🚀 Aggressive":
        st.subheader("🚀 Aggressive Allocation — momentum first, always invested")
        st.warning("This mode always allocates 100%. It follows momentum more than valuation, so it can be riskier.")
        aggr_show = make_display_df(df.copy())
        st.dataframe(
            aggr_show[["Stock", "Score", "Signal", "PE", "PEG", "Momentum6M", "EarningsYield", "Aggressive Allocation %"]],
            use_container_width=True,
            hide_index=True,
        )
        st.bar_chart(df.set_index("Stock")["Aggressive Allocation %"].sort_values(ascending=False))

    if page_choice == "📉 Backtester":
        st.markdown(
            """
            <div class="backtest-hero">
                <h2>📉 Portfolio Hive Backtester</h2>
                <p>Test your Conservative or Aggressive allocation through market storms — 2008 recession, Covid crash, or your own custom date range.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="info-card">
                <h4>What this backtester does</h4>
                It uses the allocation generated by <b>Portfolio Hive Check</b> and compares the portfolio with whichever market benchmarks you select. The chart starts at ₹100 so the comparison stays clean.
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("💡 Clean explanation: What is Sharpe Ratio?", expanded=True):
            st.markdown(
                """
                **Sharpe Ratio tells whether return was worth the risk.**

                In simple words: two portfolios may both give 20% return, but if one jumped like a mad bee every day and the other moved calmly, the calmer one usually has the better Sharpe Ratio.

                - **Higher Sharpe Ratio = better risk-adjusted return**
                - **Around 1 or above = decent**
                - **Around 2 or above = very strong**
                - **Negative Sharpe = returns were not worth the volatility**

                This tool uses daily returns and annualizes the Sharpe Ratio. It does not assume a separate risk-free rate, so treat it as a clean comparison tool, not a final investment certificate.
                """
            )

        bt_top1, bt_top2, bt_top3 = st.columns([1.1, 1.1, 1.4])
        with bt_top1:
            allocation_mode = st.radio(
                "Choose allocation style",
                ["Conservative Allocation", "Aggressive Allocation"],
                horizontal=False,
                help="Conservative uses valuation strict allocation and may hold cash. Aggressive stays fully invested and follows momentum.",
                key="backtest_allocation_mode",
            )
        with bt_top2:
            period_choice = st.radio(
                "Choose backtest period",
                ["2008 Recession", "Covid-19 Crash", "Custom Date Range"],
                horizontal=False,
                key="backtest_period_choice",
            )
        with bt_top3:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f"<span class='period-chip'>{allocation_mode}</span><span class='period-chip'>{period_choice}</span>",
                unsafe_allow_html=True,
            )
            st.caption("Backtest uses current allocation weights. It is not a historical rebalancing engine.")

        st.markdown("### 🌈 Choose comparison benchmarks")
        st.caption("Select one benchmark or many at the same time. Portfolio will always be included automatically.")
        bench_cols = st.columns(4)
        selected_benchmarks = []
        default_benchmarks = ["Nifty 50", "Sensex"]
        for idx, benchmark_name in enumerate(BENCHMARKS.keys()):
            with bench_cols[idx]:
                st.markdown(
                    f"""
                    <div class='compare-card' style='background:{BENCHMARK_CARD_STYLES.get(benchmark_name, "#ffffff")};'>
                        <h4>{benchmark_name}</h4>
                        <p>Tick this box to compare your hive with {benchmark_name}.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                checked = st.checkbox(
                    f"Compare with {benchmark_name}",
                    value=benchmark_name in default_benchmarks,
                    key=f"benchmark_{benchmark_name}",
                )
                if checked:
                    selected_benchmarks.append(benchmark_name)

        if not selected_benchmarks:
            st.info("No benchmark selected. The backtest will show only your portfolio curve.")

        if period_choice == "Custom Date Range":
            d1, d2 = st.columns(2)
            with d1:
                start_dt = st.date_input("Start date", value=pd.to_datetime("2020-02-01"), key="bt_custom_start")
            with d2:
                end_dt = st.date_input("End date", value=pd.to_datetime("2020-04-30"), key="bt_custom_end")
            start_date = str(start_dt)
            end_date = str(end_dt)
        else:
            start_date, end_date = BACKTEST_PERIODS[period_choice]
            st.success(f"Selected period: {start_date} to {end_date}")

        allocation_column = "Conservative Allocation %" if allocation_mode == "Conservative Allocation" else "Aggressive Allocation %"

        st.markdown(
            """
            <div class="warning-card">
                <b>Important:</b> This is a practical portfolio stress test. It uses present-day Portfolio Hive weights and applies them to the selected historical period. This helps compare behaviour in crashes, but it is not the same as owning the exact same portfolio in the past with all historical fundamentals.
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Run Backtest", type="primary", key="run_backtester"):
            # IMPORTANT FIX:
            # Do not write to st.session_state["active_dashboard_page"] here.
            # Streamlit does not allow modifying a session_state key after the
            # widget using that same key has already been created in this run.
            # The user is already on the Backtester page when this button is clicked,
            # and the radio widget itself will preserve this page after rerun.
            if pd.to_datetime(start_date) >= pd.to_datetime(end_date):
                st.error("Start date must be before end date.")
            else:
                with st.spinner("Backtesting the hive against market storms..."):
                    curves, metrics_df, bt_note = run_portfolio_backtest(df, allocation_column, start_date, end_date, selected_benchmarks, initial_value=100)

                if curves.empty or metrics_df.empty:
                    st.error(bt_note or "Backtest could not be completed.")
                else:
                    st.session_state["backtest_curves"] = curves
                    st.session_state["backtest_metrics"] = metrics_df
                    st.session_state["backtest_note"] = bt_note
                    benchmark_label = ", ".join(selected_benchmarks) if selected_benchmarks else "No benchmark"
                    st.session_state["backtest_title"] = f"{allocation_mode} | {period_choice} | {start_date} to {end_date} | Benchmarks: {benchmark_label}"

        if "backtest_curves" in st.session_state and "backtest_metrics" in st.session_state:
            curves = st.session_state["backtest_curves"]
            metrics_df = st.session_state["backtest_metrics"]
            st.subheader("📊 Backtester Dashboard")
            st.caption(st.session_state.get("backtest_title", "Latest backtest"))

            if st.session_state.get("backtest_note"):
                st.warning(st.session_state["backtest_note"])

            mdf = metrics_df.set_index("Asset")
            cols = st.columns(len(metrics_df))
            for idx, row in metrics_df.iterrows():
                with cols[idx]:
                    st.metric(
                        row["Asset"],
                        f"{row['Return %']:.2f}%",
                        help="Total return during selected backtest period.",
                    )
                    st.caption(f"Sharpe: {row['Sharpe Ratio']:.2f} | Max DD: {row['Max Drawdown %']:.2f}%")

            st.plotly_chart(plot_backtest_curves(curves), use_container_width=True)

            b1, b2 = st.columns(2)
            with b1:
                st.plotly_chart(plot_metric_bars(metrics_df, "Return %", "Total Returns Comparison", "%"), use_container_width=True)
            with b2:
                st.plotly_chart(plot_metric_bars(metrics_df, "Sharpe Ratio", "Sharpe Ratio Comparison", ""), use_container_width=True)

            display_metrics = metrics_df.copy()
            for col in ["Return %", "Sharpe Ratio", "Max Drawdown %", "Final Value"]:
                display_metrics[col] = display_metrics[col].apply(lambda x: "NA" if pd.isna(x) else f"{x:.2f}")
            st.dataframe(display_metrics, use_container_width=True, hide_index=True)

            csv_bt = metrics_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Backtest Metrics CSV",
                data=csv_bt,
                file_name=f"portfolio_hive_backtest_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                key="download_backtest_csv",
            )

    if page_choice == "🔍 Deep Check":
        st.subheader("🔍 Stock-wise Deep Check")

        stock_options = df["Stock"].tolist()
        if "deep_stock_selector" in st.session_state and st.session_state["deep_stock_selector"] not in stock_options:
            st.session_state["deep_stock_selector"] = stock_options[0]

        selected_stock = st.selectbox(
            "Select stock",
            stock_options,
            key="deep_stock_selector",
        )
        selected_result = next(r for r in results if r["Stock"] == selected_stock)

        a, b, c, d = st.columns(4)
        a.metric("Hive Score", f"{selected_result['Score']}/100")
        b.metric("Signal", selected_result["Signal"])
        c.metric("PE", format_number(selected_result.get("PE", np.nan)))
        d.metric("PEG", format_number(selected_result.get("PEG", np.nan)))

        e, f, g, h = st.columns(4)
        e.metric("ROE Avg", format_number(selected_result.get("ROEAvg", np.nan)))
        f.metric("CFO/PAT", format_number(selected_result.get("CashConversion", np.nan)))
        g.metric("EPS Growth", format_percent(selected_result.get("LatestEPSGrowth", np.nan)))
        h.metric("6M Momentum", format_percent(selected_result.get("Momentum6M", np.nan)))

        st.caption("Cash conversion uses latest annual CFO from Screener Cash Flow divided by latest annual PAT from Screener Profit & Loss.")
        st.caption("ROE uses Screener ROE if available. If missing, it calculates each year's ROE from annual PAT / annual net worth for up to 5 years, then averages it.")

        checks_df = pd.DataFrame(selected_result.get("Checks", []))
        if not checks_df.empty:
            def pretty_value(x):
                if isinstance(x, (float, int, np.floating, np.integer)) and not pd.isna(x):
                    if abs(x) < 2:
                        return format_percent(x)
                    return format_number(x)
                return x
            checks_df["Value"] = checks_df["Value"].apply(pretty_value)
            st.table(checks_df)

        if selected_result.get("URL"):
            st.markdown(f"[Open source page on Screener]({selected_result['URL']})")

    output = df.drop(columns=["URL"], errors="ignore")
    csv = output.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Portfolio Hive Check CSV",
        data=csv,
        file_name=f"portfolio_hive_check_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )

else:
    st.info("Enter your stocks in the sidebar and click **Run Hive Check**.")
