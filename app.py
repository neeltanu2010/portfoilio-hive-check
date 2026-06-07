import re
import html as html_lib
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    :root {
        --bee-ink: #171A1F;
        --bee-muted: #5C6674;
        --bee-soft: #FFF9E8;
        --bee-card: rgba(255,255,255,0.94);
        --bee-yellow: #F5C542;
        --bee-gold: #E6A400;
        --bee-amber: #F59E0B;
        --bee-blue: #3B82F6;
        --bee-green: #16A34A;
        --bee-red: #DC2626;
        --bee-purple: #7C3AED;
        --bee-border: rgba(23,26,31,0.10);
        --bee-shadow: 0 22px 65px rgba(23,26,31,0.10);
    }

    html, body, [class*="css"] {
        font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background-color: #FFFEFA;
        background-image:
            radial-gradient(circle at 7% 8%, rgba(245,197,66,0.18), transparent 15rem),
            radial-gradient(circle at 88% 10%, rgba(124,58,237,0.08), transparent 18rem),
            radial-gradient(circle at 50% 100%, rgba(245,158,11,0.13), transparent 24rem),
            url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='230' height='200' viewBox='0 0 230 200'%3E%3Cg fill='none' stroke='%23E6C35A' stroke-width='1.5' stroke-opacity='0.15'%3E%3Cpolygon points='58,14 90,32 90,68 58,86 26,68 26,32'/%3E%3Cpolygon points='150,14 182,32 182,68 150,86 118,68 118,32'/%3E%3Cpolygon points='104,98 136,116 136,152 104,170 72,152 72,116'/%3E%3C/g%3E%3Cg fill='none' stroke='%23D7B55A' stroke-width='2' stroke-linecap='round' stroke-opacity='0.10'%3E%3Cpath d='M28 176 C62 144, 90 170, 122 142' stroke-dasharray='2 9'/%3E%3Cpath d='M145 162 C168 137, 190 153, 214 128' stroke-dasharray='2 9'/%3E%3C/g%3E%3C/svg%3E"),
            linear-gradient(180deg, #FFFEFA 0%, #FFF9EA 54%, #FFF4D7 100%);
        background-size: auto, auto, auto, 310px 265px, auto;
        background-repeat: no-repeat, no-repeat, no-repeat, repeat, no-repeat;
        background-position: left top, right top, center bottom, 0 0, center;
        background-attachment: fixed, fixed, fixed, fixed, fixed;
    }

    .main { background: transparent; }
    .block-container {
        padding-top: 3.2rem;
        padding-bottom: 4rem;
        max-width: 1380px;
    }

    h1, h2, h3 {
        color: var(--bee-ink);
        letter-spacing: -0.035em;
    }

    .main-title {
        display: block;
        font-size: 3.05rem;
        font-weight: 950;
        margin-top: 0.75rem;
        margin-bottom: 0.35rem;
        padding-top: 0.35rem;
        padding-bottom: 0.25rem;
        letter-spacing: -0.045em;
        line-height: 1.18;
        color: var(--bee-ink);
        overflow: visible;
    }

    .sub-title {
        font-size: 1.08rem;
        color: var(--bee-muted);
        margin-top: 0.65rem;
        margin-bottom: 1.6rem;
        line-height: 1.7;
        max-width: 900px;
    }

    section[data-testid="stSidebar"] {
        background:
            radial-gradient(circle at 20% 8%, rgba(245,197,66,0.24), transparent 10rem),
            linear-gradient(180deg, #171A1F 0%, #24211A 54%, #382900 100%);
        border-right: 1px solid rgba(255,255,255,0.12);
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] .stCaption {
        color: rgba(255,255,255,0.93) !important;
    }

    section[data-testid="stSidebar"] textarea,
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] [data-baseweb="checkbox"] * {
        color: #171A1F !important;
    }

    section[data-testid="stSidebar"] textarea {
        background: rgba(255,255,255,0.96) !important;
        border-radius: 18px !important;
        border: 1px solid rgba(245,197,66,0.28) !important;
        box-shadow: 0 12px 36px rgba(0,0,0,0.18);
    }

    .bee-box {
        background:
            radial-gradient(circle at 97% 10%, rgba(245,197,66,0.15), transparent 12rem),
            linear-gradient(135deg, rgba(255,255,255,0.97), rgba(255,248,221,0.94));
        border: 1px solid rgba(230,164,0,0.20);
        border-radius: 30px;
        padding: 26px 28px;
        margin-bottom: 22px;
        box-shadow: var(--bee-shadow);
        color: var(--bee-ink);
        line-height: 1.72;
    }

    .bee-box b { color: #111827; }

    .mode-box {
        background: rgba(255,255,255,0.94);
        border: 1px solid var(--bee-border);
        border-radius: 28px;
        padding: 24px 25px;
        box-shadow: 0 18px 48px rgba(23,26,31,0.08);
        min-height: 175px;
        backdrop-filter: blur(10px);
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }
    .mode-box:hover {
        transform: translateY(-3px);
        box-shadow: 0 25px 70px rgba(23,26,31,0.12);
    }
    .mode-box h4 {
        margin-top: 0;
        margin-bottom: 0.8rem;
        color: #111827;
        font-size: 1.25rem;
        font-weight: 900;
        letter-spacing: -0.025em;
    }

    .small-muted {
        color: #667085;
        font-size: 0.92rem;
        line-height: 1.65;
    }

    .pill {
        display: inline-block;
        padding: 7px 12px;
        border-radius: 999px;
        background: #FFF3BF;
        color: #7A5600;
        border: 1px solid rgba(230,164,0,0.20);
        font-size: 0.82rem;
        font-weight: 900;
        margin-right: 8px;
        margin-bottom: 8px;
        letter-spacing: 0.02em;
    }

    .premium-hero {
        position: relative;
        overflow: hidden;
        border-radius: 36px;
        padding: 32px 34px;
        margin: 10px 0 26px 0;
        border: 1px solid rgba(230,164,0,0.18);
        background:
            radial-gradient(circle at 87% 20%, rgba(245,197,66,0.18), transparent 15rem),
            radial-gradient(circle at 9% 13%, rgba(59,130,246,0.08), transparent 14rem),
            linear-gradient(135deg, rgba(255,255,255,0.98), rgba(255,249,232,0.96));
        box-shadow: var(--bee-shadow);
    }
    .premium-hero h2 {
        margin: 0;
        font-size: 2rem;
        font-weight: 950;
        color: #111827;
        letter-spacing: -0.05em;
    }
    .premium-hero p {
        margin: 0.75rem 0 0 0;
        color: #4B5563;
        line-height: 1.72;
        max-width: 880px;
    }

    .dialogue-card {
        border-radius: 24px;
        padding: 18px 20px;
        margin: 14px 0 20px 0;
        border: 1px solid var(--bee-border);
        background: rgba(255,255,255,0.94);
        box-shadow: 0 14px 38px rgba(23,26,31,0.06);
        line-height: 1.65;
    }
    .dialogue-card.info {
        background: linear-gradient(135deg, rgba(234,244,255,0.98), rgba(255,255,255,0.98));
        border-left: 7px solid var(--bee-blue);
    }
    .dialogue-card.warn {
        background: linear-gradient(135deg, rgba(255,247,237,0.98), rgba(255,255,255,0.98));
        border-left: 7px solid var(--bee-amber);
    }
    .dialogue-card.good {
        background: linear-gradient(135deg, rgba(240,253,244,0.98), rgba(255,255,255,0.98));
        border-left: 7px solid var(--bee-green);
    }
    .dialogue-title {
        font-weight: 950;
        color: #111827;
        margin-bottom: 0.35rem;
        letter-spacing: -0.02em;
    }
    .dialogue-body { color: #4B5563; }

    div[data-testid="stMetric"] {
        background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(255,251,240,0.96));
        border: 1px solid var(--bee-border);
        padding: 18px 19px;
        border-radius: 24px;
        box-shadow: 0 16px 44px rgba(23,26,31,0.08);
    }
    div[data-testid="stMetricLabel"] {
        color: #667085 !important;
        font-weight: 850;
    }
    div[data-testid="stMetricValue"] {
        color: #111827 !important;
        font-weight: 950;
        letter-spacing: -0.04em;
    }

    div.stButton > button,
    div.stDownloadButton > button {
        border-radius: 16px !important;
        min-height: 3rem;
        font-weight: 950 !important;
        border: 1px solid rgba(23,26,31,0.10) !important;
        box-shadow: 0 12px 28px rgba(23,26,31,0.10);
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #F5C542 0%, #F59E0B 100%) !important;
        color: #171A1F !important;
        border: none !important;
    }
    div.stDownloadButton > button {
        background: #171A1F !important;
        color: white !important;
        border: none !important;
    }

    .backtest-hero {
        background:
            radial-gradient(circle at 88% 18%, rgba(245,197,66,0.15), transparent 16rem),
            linear-gradient(135deg, rgba(255,255,255,0.98), rgba(255,249,232,0.96));
        color: #111827;
        border: 1px solid rgba(230,164,0,0.18);
        border-radius: 30px;
        padding: 28px 30px;
        margin: 10px 0 22px 0;
        box-shadow: var(--bee-shadow);
    }
    .backtest-hero h2 {
        margin: 0 0 9px 0;
        font-size: 2rem;
        font-weight: 950;
        color: #111827;
    }
    .backtest-hero p {
        margin: 0;
        color: #4B5563;
        font-size: 1rem;
        line-height: 1.7;
    }

    .info-card {
        background: linear-gradient(135deg, rgba(234,244,255,0.98), rgba(255,255,255,0.98));
        border: 1px solid #dce7ff;
        border-left: 7px solid #3b82f6;
        border-radius: 24px;
        padding: 20px 22px;
        margin: 14px 0 20px 0;
        box-shadow: 0 12px 32px rgba(59,130,246,0.08);
        line-height: 1.65;
    }
    .info-card h4 {margin: 0 0 8px 0; color: #1e3a8a; font-weight: 950;}

    .warning-card {
        background: linear-gradient(135deg, rgba(255,247,237,0.98), rgba(255,255,255,0.98));
        border: 1px solid #fed7aa;
        border-left: 7px solid #f97316;
        border-radius: 24px;
        padding: 18px 20px;
        margin: 14px 0 20px 0;
        line-height: 1.65;
    }

    .period-chip {
        display: inline-block;
        background: #171A1F;
        color: #FFF3BF;
        padding: 7px 13px;
        border-radius: 999px;
        font-weight: 900;
        font-size: 0.82rem;
        margin-right: 8px;
    }

    .compare-card {
        border-radius: 24px;
        padding: 18px 18px;
        min-height: 112px;
        color: #111827;
        box-shadow: 0 14px 36px rgba(23,26,31,0.08);
        border: 1px solid rgba(255,255,255,0.82);
        margin-bottom: 10px;
    }
    .compare-card h4 {margin: 0 0 8px 0; font-size: 1.05rem; font-weight: 950;}
    .compare-card p {margin: 0; color: #4B5563; font-size: 0.86rem; line-height:1.5;}

    .nav-radio-card {
        background: linear-gradient(135deg, rgba(255,243,191,0.96), rgba(255,255,255,0.96));
        border: 1px solid rgba(230,164,0,0.20);
        border-radius: 24px;
        padding: 15px 18px;
        margin: 18px 0 14px 0;
        box-shadow: 0 14px 34px rgba(23,26,31,0.06);
    }

    div[data-testid="stRadio"] label {
        font-weight: 800;
    }

    .premium-table-wrap {
        border-radius: 26px;
        overflow: auto;
        border: 1px solid rgba(23,26,31,0.09);
        box-shadow: 0 18px 50px rgba(23,26,31,0.08);
        background: rgba(255,255,255,0.96);
        margin: 14px 0 28px 0;
        max-height: 660px;
    }
    table.premium-table {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        font-size: 0.92rem;
        color: #17212B;
    }
    table.premium-table thead th {
        position: sticky;
        top: 0;
        z-index: 1;
        background: linear-gradient(135deg, #FFF3BF, #FFF8E1);
        color: #171A1F;
        text-align: left;
        padding: 16px 17px;
        font-weight: 950;
        border-bottom: 2px solid rgba(230,164,0,0.32);
        white-space: nowrap;
        letter-spacing: -0.01em;
    }
    table.premium-table tbody td {
        padding: 15px 17px;
        border-bottom: 1px solid rgba(23,26,31,0.06);
        vertical-align: top;
        line-height: 1.48;
        background: rgba(255,255,255,0.86);
        color: #1F2937;
    }
    table.premium-table tbody tr:nth-child(even) td {
        background: rgba(255,251,240,0.86);
    }
    table.premium-table tbody tr:hover td {
        background: #FFF7DE;
    }

    .badge {
        display:inline-flex;
        align-items:center;
        justify-content:center;
        padding: 6px 11px;
        border-radius: 999px;
        font-weight: 950;
        font-size: 0.78rem;
        letter-spacing: 0.01em;
        white-space: nowrap;
    }
    .badge-pass { background:#EAFBF0; color:#107B3D; border:1px solid rgba(16,123,61,0.16); }
    .badge-fail { background:#FFF1F1; color:#B42318; border:1px solid rgba(180,35,24,0.16); }
    .badge-watch { background:#FFF8DB; color:#9A6700; border:1px solid rgba(154,103,0,0.16); }
    .badge-info { background:#EAF4FF; color:#1D4ED8; border:1px solid rgba(29,78,216,0.14); }
    .badge-dark { background:#171A1F; color:#FFF3BF; border:1px solid rgba(23,26,31,0.10); }

    div[data-testid="stDataFrame"],
    div[data-testid="stTable"] {
        border-radius: 24px !important;
        overflow: hidden !important;
        box-shadow: 0 18px 50px rgba(23,26,31,0.07);
    }

    div[data-testid="stAlert"] {
        border-radius: 20px !important;
        border: 1px solid rgba(23,26,31,0.08);
        box-shadow: 0 12px 32px rgba(23,26,31,0.05);
    }

    hr {
        border-color: rgba(23,26,31,0.08) !important;
        margin: 2rem 0 !important;
    }
    
    div[data-testid="stTextArea"] textarea {
        background: rgba(255,255,255,0.97) !important;
        border-radius: 20px !important;
        border: 1px solid rgba(230,164,0,0.26) !important;
        box-shadow: 0 12px 34px rgba(23,26,31,0.06) !important;
        color: #171A1F !important;
        font-weight: 650 !important;
    }

    
    /* Title clipping safety fix */
    .main-title,
    .premium-title {
        line-height: 1.18 !important;
        padding-top: 0.35rem !important;
        padding-bottom: 0.25rem !important;
        overflow: visible !important;
    }

    div[data-testid="stAppViewContainer"] > .main .block-container {
        padding-top: 3.2rem !important;
    }

    @media (max-width: 1200px) {
        .main-title,
        .premium-title {
            font-size: 2.45rem !important;
            line-height: 1.22 !important;
            letter-spacing: -0.035em !important;
        }
        div[data-testid="stAppViewContainer"] > .main .block-container {
            padding-top: 2.8rem !important;
        }
    }

    @media (max-width: 800px) {
        .main-title,
        .premium-title {
            font-size: 2.05rem !important;
            line-height: 1.25 !important;
        }
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
st.markdown(
    '''
    <div class="premium-hero">
        <span class="pill">Quality</span><span class="pill">Valuation</span><span class="pill">Allocation</span><span class="pill">Backtester</span>
        <h2>Premium Money Bees Portfolio Console</h2>
        <p>Run your portfolio through quality, valuation, CFO/PAT, momentum, allocation and backtesting checks in a cleaner, more breathable dashboard.</p>
    </div>
    ''',
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


def _premium_badge(value):
    text = str(value)
    escaped = html_lib.escape(text)

    lower = text.lower()
    if "✅" in text or "pass" in lower or "strong" in lower or "sweet" in lower or "eligible" in lower:
        return f"<span class='badge badge-pass'>{escaped}</span>"
    if "❌" in text or "fail" in lower or "hornet" in lower or "expensive" in lower or "cash preferred" in lower or "data error" in lower:
        return f"<span class='badge badge-fail'>{escaped}</span>"
    if "decent" in lower or "fair" in lower or "weak" in lower or "missing" in lower or "warning" in lower or "check" in lower:
        return f"<span class='badge badge-watch'>{escaped}</span>"
    if "allocation" in lower or "portfolio" in lower or "nifty" in lower or "sensex" in lower:
        return f"<span class='badge badge-info'>{escaped}</span>"
    return escaped


def premium_table(df, height=None):
    """Render a clean premium HTML table while preserving the dataframe content."""
    if df is None or getattr(df, "empty", False):
        st.info("No table data available.")
        return

    show = df.copy()
    show = show.reset_index(drop=True)

    html = ["<div class='premium-table-wrap'>", "<table class='premium-table'>", "<thead><tr>"]
    for col in show.columns:
        html.append(f"<th>{html_lib.escape(str(col))}</th>")
    html.append("</tr></thead><tbody>")

    for _, row in show.iterrows():
        html.append("<tr>")
        for col in show.columns:
            val = row[col]
            if pd.isna(val):
                cell = "NA"
            else:
                cell = _premium_badge(val)
            html.append(f"<td>{cell}</td>")
        html.append("</tr>")

    html.append("</tbody></table></div>")
    st.markdown("".join(html), unsafe_allow_html=True)


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

def render_dashboard():
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
            st.markdown("<div class=\"dialogue-card good\"><div class=\"dialogue-title\">Portfolio Hive Summary</div><div class=\"dialogue-body\">A cleaner summary view of score, signal, valuation, growth, return quality, cash conversion and momentum.</div></div>", unsafe_allow_html=True)
            st.subheader("📊 Portfolio Hive Summary")
            show = make_display_df(df)
            cols = [
                "Stock", "Company", "Score", "Signal", "BuyingZone", "PE", "PEG", "LatestEPSGrowth", "EPSSource",
                "SalesCAGR", "PATCAGR", "ROCEAvg", "ROEAvg", "ROESource", "DEAnalytical", "CashConversion",
                "LatestAnnualPAT", "LatestAnnualCFO", "Momentum6M", "Issue"
            ]
            premium_table(show[[c for c in cols if c in show.columns]])

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
            st.markdown("<div class=\"dialogue-card info\"><div class=\"dialogue-title\">Conservative Allocation</div><div class=\"dialogue-body\">Valuation discipline first. This page can keep cash instead of forcing allocation into weak or expensive stocks.</div></div>", unsafe_allow_html=True)
            st.subheader("🛡️ Conservative Allocation — valuation first, cash allowed")
            st.info("Rule: score ≥ 60, PE < 25, PEG < 1.5, and latest annual CFO/PAT > 1. Stocks failing this are not forced into allocation.")
            cons_show = make_display_df(df.copy())
            premium_table(cons_show[["Stock", "Score", "Signal", "BuyingZone", "PE", "PEG", "CashConversion", "Conservative Status", "Conservative Allocation %"]])
            chart_data = df.set_index("Stock")["Conservative Allocation %"].sort_values(ascending=False)
            if cash_pct > 0:
                chart_data.loc["CASH / WAIT"] = cash_pct
            st.bar_chart(chart_data)

        if page_choice == "🚀 Aggressive":
            st.markdown("<div class=\"dialogue-card warn\"><div class=\"dialogue-title\">Aggressive Allocation</div><div class=\"dialogue-body\">Momentum-led and always invested. The dashboard looks sweeter, but this mode can buzz louder with risk.</div></div>", unsafe_allow_html=True)
            st.subheader("🚀 Aggressive Allocation — momentum first, always invested")
            st.warning("This mode always allocates 100%. It follows momentum more than valuation, so it can be riskier.")
            aggr_show = make_display_df(df.copy())
            premium_table(aggr_show[["Stock", "Score", "Signal", "PE", "PEG", "Momentum6M", "EarningsYield", "Aggressive Allocation %"]])
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
                premium_table(display_metrics)

                csv_bt = metrics_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="Download Backtest Metrics CSV",
                    data=csv_bt,
                    file_name=f"portfolio_hive_backtest_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="download_backtest_csv",
                )

        if page_choice == "🔍 Deep Check":
            st.markdown("<div class=\"dialogue-card info\"><div class=\"dialogue-title\">Stock-wise Deep Check</div><div class=\"dialogue-body\">Open any stock and inspect the exact checks, score components, valuation ratios and cash conversion details.</div></div>", unsafe_allow_html=True)
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
                premium_table(checks_df)

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

# -----------------------------
# MAIN PAGE INPUT + DASHBOARD STAGE
# -----------------------------
if "hive_stage" not in st.session_state:
    st.session_state["hive_stage"] = "landing"
if "hive_results" not in st.session_state:
    st.session_state["hive_results"] = None
if "hive_last_tickers" not in st.session_state:
    st.session_state["hive_last_tickers"] = ", ".join(DEFAULT_TICKERS)
if "hive_last_consolidated" not in st.session_state:
    st.session_state["hive_last_consolidated"] = True


def run_hive_from_main_page(raw_tickers, consolidated):
    tickers = [clean_ticker(x) for x in re.split(r"[,\n]+", raw_tickers) if clean_ticker(x)]
    tickers = list(dict.fromkeys(tickers))
    if not tickers:
        st.error("Please enter at least one ticker.")
        return

    st.session_state["hive_last_tickers"] = raw_tickers
    st.session_state["hive_last_consolidated"] = consolidated

    results = []
    progress = st.progress(0)
    status = st.empty()

    for i, ticker in enumerate(tickers):
        status.info(f"Checking hive for {ticker}...")
        results.append(analyse_stock(ticker, consolidated=consolidated))
        progress.progress((i + 1) / len(tickers))

    status.success("Hive check completed. The bees have returned with data.")
    st.session_state["hive_results"] = results
    st.session_state["hive_stage"] = "dashboard"
    st.rerun()


def render_landing_page():
    st.markdown(
        """
        <div class="dialogue-card good">
            <div class="dialogue-title">Main page workflow</div>
            <div class="dialogue-body">Put all portfolio input here first. After clicking <b>Run Hive Check & Enter Dashboard</b>, the second page becomes results and analysis only.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

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

    st.markdown(
        """
        <div class="premium-hero">
            <span class="pill">Input Console</span><span class="pill">No Sidebar Dashboard</span><span class="pill">Results Only Inside</span>
            <h2>Feed the hive here. Analyse inside.</h2>
            <p>Enter your NSE tickers and data preference on this first page only. The dashboard page will not show the sidebar input console.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([0.68, 0.32], gap="large")
    with left:
        raw_tickers = st.text_area(
            "Enter NSE tickers",
            value=st.session_state.get("hive_last_tickers", ", ".join(DEFAULT_TICKERS)),
            height=230,
            help="Use Screener symbols without .NS. Example: INFY, NTPC, ARE&M, ZYDUSLIFE",
        )
    with right:
        st.markdown(
            """
            <div class="dialogue-card info">
                <div class="dialogue-title">Input note</div>
                <div class="dialogue-body">Use comma or line-separated tickers. The tool will clean duplicates and run the same Portfolio Hive Check logic.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        consolidated = st.checkbox(
            "Prefer consolidated data",
            value=st.session_state.get("hive_last_consolidated", True),
        )
        st.caption("Educational screening only. Not investment advice. Bees can sting. Markets can too.")

    b1, b2 = st.columns([0.35, 0.65])
    with b1:
        run_button = st.button("🐝 Run Hive Check & Enter Dashboard", type="primary", use_container_width=True)
    with b2:
        if st.session_state.get("hive_results"):
            open_dashboard = st.button("Open Last Dashboard", use_container_width=True)
            if open_dashboard:
                st.session_state["hive_stage"] = "dashboard"
                st.rerun()

    if run_button:
        run_hive_from_main_page(raw_tickers, consolidated)


def render_dashboard_header():
    top_l, top_r = st.columns([0.76, 0.24], gap="large")
    with top_l:
        st.markdown(
            """
            <div class="dialogue-card good">
                <div class="dialogue-title">Dashboard console</div>
                <div class="dialogue-body">This page is results and analysis only. All portfolio input is handled on the first main page.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with top_r:
        if st.button("← Back to Input Page", use_container_width=True):
            st.session_state["hive_stage"] = "landing"
            st.rerun()



if st.session_state.get("hive_stage") != "dashboard":
    render_landing_page()
    st.stop()

if not st.session_state.get("hive_results"):
    st.session_state["hive_stage"] = "landing"
    st.warning("No saved hive results found. Please run the check from the main input page.")
    st.stop()

render_dashboard_header()
render_dashboard()
