import re
from io import StringIO
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf
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
    <span class="small-muted">FCF and CFO trend checks are removed. Cash conversion is strictly latest annual CFO from cash flow divided by latest annual PAT from P&L.</span>
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

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Summary", "🛡️ Conservative", "🚀 Aggressive", "🔍 Deep Check"])

    with tab1:
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

    with tab2:
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

    with tab3:
        st.subheader("🚀 Aggressive Allocation — momentum first, always invested")
        st.warning("This mode always allocates 100%. It follows momentum more than valuation, so it can be riskier.")
        aggr_show = make_display_df(df.copy())
        st.dataframe(
            aggr_show[["Stock", "Score", "Signal", "PE", "PEG", "Momentum6M", "EarningsYield", "Aggressive Allocation %"]],
            use_container_width=True,
            hide_index=True,
        )
        st.bar_chart(df.set_index("Stock")["Aggressive Allocation %"].sort_values(ascending=False))

    with tab4:
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
