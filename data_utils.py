"""
data_utils.py
─────────────
Single source of truth for all data loading, cleaning and shared constants.
Drop new Export.csv / Import.csv with any date range → everything updates automatically.
"""
import pandas as pd
import numpy as np
import streamlit as st

MONTH_ORDER = [
    'January','February','March','April','May','June',
    'July','August','September','October','November','December'
]

# ── Colour palette ────────────────────────────────────────────────────────────
COLORS = {
    'export':       '#10d9a0',
    'import':       '#f43f5e',
    'balance_neg':  '#f59e0b',
    'balance_pos':  '#10d9a0',
    'blue':         '#60a5fa',
    'purple':       '#a78bfa',
    'orange':       '#fb923c',
    'teal':         '#2dd4bf',
    'pink':         '#f472b6',
    'yellow':       '#fcd34d',
}

CATEGORY_COLORS_EXP = {
    'TEXTILE GROUP':            '#10d9a0',
    'FOOD GROUP':               '#f59e0b',
    'OTHER MANUFACTURES GROUP': '#60a5fa',
    'PETROLEUM GROUP & COAL':   '#f43f5e',
}

CATEGORY_COLORS_IMP = {
    'PETROLEUM GROUP':                        '#f43f5e',
    'MACHINERY GROUP':                        '#60a5fa',
    'TRANSPORT GROUP':                        '#a78bfa',
    'FOOD GROUP':                             '#f59e0b',
    'TEXTILE GROUP':                          '#10d9a0',
    'AGRICULTURAL AND OTHER CHEMICALS GROUP': '#2dd4bf',
    'METAL GROUP':                            '#fb923c',
    'MISCELLANEOUS GROUP':                    '#f472b6',
}

# ── Plotly base layout ────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(family='Plus Jakarta Sans', color='#64748b', size=12),
    hoverlabel=dict(
        bgcolor='#0d1526',
        bordercolor='rgba(99,130,202,0.35)',
        font=dict(color='#e2e8f0', size=13, family='Plus Jakarta Sans')
    ),
    margin=dict(l=10, r=10, t=40, b=10),
    legend=dict(
        bgcolor='rgba(0,0,0,0)',
        bordercolor='rgba(99,130,202,0.15)',
        font=dict(color='#64748b', family='Plus Jakarta Sans')
    )
)

AXIS_STYLE = dict(
    gridcolor='rgba(99,130,202,0.08)',
    linecolor='rgba(99,130,202,0.15)',
    tickcolor='rgba(99,130,202,0.15)',
    tickfont=dict(color='#475569', size=11),
    title_font=dict(color='#64748b', size=11),
    zerolinecolor='rgba(99,130,202,0.15)',
)

def pl(height=300, xaxis=None, yaxis=None, **kwargs):
    """Return a clean update_layout dict — no duplicate axis keys."""
    x = {**AXIS_STYLE, **(xaxis or {})}
    y = {**AXIS_STYLE, **(yaxis or {})}
    return {**PLOTLY_LAYOUT, 'height': height, 'xaxis': x, 'yaxis': y, **kwargs}


# ── Data loading ──────────────────────────────────────────────────────────────
def _remove_subtotals_and_duplicates(df):
    """
    The PBS CSV (especially 2025+) contains:
    1. Category subtotal rows (NaN PRODUCT or PRODUCT containing 'GROUP')
    2. Quarterly cumulative duplicates — same CATEGORY+PRODUCT appears twice in a
       month: once with the true monthly value and once with the quarter-to-date
       cumulative. The SMALLER value is always the correct monthly figure.
    3. System-transition notes (SOME DIFFERENCE..., THE DATA SOURCE...)
    This function removes all three types.
    """
    prod_raw = df['PRODUCT']

    # Step 1: Remove non-product / summary rows
    keep = (
        ~prod_raw.isna() &                                                        # float NaN
        prod_raw.astype(str).str.strip().ne('') &                                # blank
        prod_raw.astype(str).str.strip().ne('nan') &                             # string nan
        ~prod_raw.astype(str).str.strip().str.upper()
               .str.contains(r'\bGROUP\b', na=False) &                         # subtotal label
        ~prod_raw.astype(str).str.strip().str.upper()
               .str.startswith('SOME DIFFERENCE', na=False) &                    # note row
        ~prod_raw.astype(str).str.strip().str.upper()
               .str.startswith('THE DATA SOURCE', na=False)                      # note row
    )
    df = df[keep].copy()

    # Step 2: Strip leading/trailing whitespace from key columns
    df['PRODUCT']    = df['PRODUCT'].astype(str).str.strip()
    df['CATEGORY']   = df['CATEGORY'].astype(str).str.strip().str.upper().str.replace(r'\s+', ' ', regex=True)
    df['CLASS TYPE'] = df['CLASS TYPE'].astype(str).str.strip()

    # Step 3: Normalise variant category names
    df['CATEGORY'] = (df['CATEGORY']
        .str.replace('AGRICULTURAL & OTHER\n CHEMICALS GROUP',
                     'AGRICULTURAL AND OTHER CHEMICALS GROUP', regex=False)
        .str.replace('AGRICULTURAL & OTHER CHEMICALS GROUP',
                     'AGRICULTURAL AND OTHER CHEMICALS GROUP', regex=False))

    # Step 4: Remove quarterly cumulative duplicates.
    # Within each Year+Month, the SAME CATEGORY+PRODUCT may appear twice.
    # The SMALLER DOLLARS value = genuine monthly figure.
    # The LARGER DOLLARS value = quarter-to-date cumulative (must be excluded).
    df = (df.sort_values('DOLLARS', ascending=True)
            .drop_duplicates(subset=['YEAR', 'MONTH', 'CATEGORY', 'PRODUCT'], keep='first')
            .reset_index(drop=True))

    return df


@st.cache_data
def load_data():
    exp = pd.read_csv('Export.csv')
    imp = pd.read_csv('Import.csv')

    result = []
    for df in [exp, imp]:
        for col in ['QUANTITY', 'RUPEES', 'DOLLARS', '% QUANTITY', '% RUPEES', '% DOLLARS']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df['Month_Num'] = df['MONTH'].apply(
            lambda m: MONTH_ORDER.index(m) + 1 if m in MONTH_ORDER else 0
        )
        df = _remove_subtotals_and_duplicates(df)
        result.append(df)

    return result[0], result[1]


@st.cache_data
def get_date_range():
    """Return (min_year, max_year, latest_month_label) from the actual data."""
    exp, imp = load_data()
    all_years  = sorted(set(exp['YEAR'].unique()) | set(imp['YEAR'].unique()))
    max_year   = max(all_years)
    min_year   = min(all_years)
    # Latest month in latest year
    latest_months = exp[exp['YEAR']==max_year]['Month_Num'].max()
    latest_month_name = MONTH_ORDER[latest_months - 1] if latest_months > 0 else 'N/A'
    return min_year, max_year, latest_month_name


@st.cache_data
def get_monthly_totals():
    exp, imp = load_data()
    e = exp.groupby(['YEAR','MONTH','Month_Num'])['DOLLARS'].sum().reset_index()
    i = imp.groupby(['YEAR','MONTH','Month_Num'])['DOLLARS'].sum().reset_index()
    merged = e.merge(i, on=['YEAR','MONTH','Month_Num'], suffixes=('_exp','_imp'))
    merged['balance'] = merged['DOLLARS_exp'] - merged['DOLLARS_imp']
    merged['Month_Cat'] = pd.Categorical(merged['MONTH'], categories=MONTH_ORDER, ordered=True)
    merged = merged.sort_values(['YEAR','Month_Cat']).reset_index(drop=True)
    merged['date'] = pd.to_datetime(
        merged['YEAR'].astype(str) + '-' +
        merged['Month_Num'].astype(str).str.zfill(2) + '-01'
    )
    return merged


@st.cache_data
def get_annual_totals():
    exp, imp = load_data()
    e = exp.groupby('YEAR')['DOLLARS'].sum().reset_index().rename(columns={'DOLLARS':'exports'})
    i = imp.groupby('YEAR')['DOLLARS'].sum().reset_index().rename(columns={'DOLLARS':'imports'})
    df = e.merge(i, on='YEAR')
    df['balance']        = df['exports'] - df['imports']
    df['trade_volume']   = df['exports'] + df['imports']
    df['coverage_ratio'] = (df['exports'] / df['imports'] * 100).round(1)
    return df.sort_values('YEAR').reset_index(drop=True)


@st.cache_data
def get_category_annual(side='export'):
    exp, imp = load_data()
    df = exp if side == 'export' else imp
    return df.groupby(['YEAR','CATEGORY'])['DOLLARS'].sum().reset_index()


@st.cache_data
def get_product_annual(side='export'):
    exp, imp = load_data()
    df = exp if side == 'export' else imp
    return df.groupby(['YEAR','CATEGORY','PRODUCT'])['DOLLARS'].sum().reset_index()


# ── Formatting helpers ────────────────────────────────────────────────────────
def fmt_usd(val, decimals=2):
    """Format USD-thousands to a human-readable string."""
    val_b = val / 1_000_000        # thousands → billions
    if abs(val_b) >= 1:
        return f"${val_b:.{decimals}f}B"
    val_m = val / 1_000
    return f"${val_m:.{decimals}f}M"
