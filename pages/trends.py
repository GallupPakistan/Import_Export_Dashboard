import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_utils import *

def period_banner(label, period, color='#10d9a0', note=''):
    note_html = f'<span style="color:#64748b;font-size:0.72rem;margin-left:0.6rem;">{note}</span>' if note else ''
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0.6rem;
                padding:0.45rem 0.9rem;margin-bottom:0.5rem;
                background:rgba(13,21,38,0.7);border:1px solid rgba(99,130,202,0.15);
                border-left:3px solid {color};border-radius:0 8px 8px 0;">
        <span style="font-size:0.7rem;font-weight:700;text-transform:uppercase;
                     letter-spacing:0.1em;color:#64748b;">{label}</span>
        <span style="font-family:'Space Grotesk',sans-serif;font-size:0.82rem;
                     font-weight:700;color:{color};">{period}</span>
        {note_html}
    </div>""", unsafe_allow_html=True)

def render():
    min_yr, max_yr, latest_m = get_date_range()
    data_period    = f"{min_yr} – {latest_m} {max_yr}"
    full_yr_period = f"{min_yr} – {max_yr}"

    st.markdown(f"""
    <div class="page-header"><div>
        <div class="section-badge">Trends & Patterns</div>
        <div class="page-title">📈 Advanced Trade Analytics</div>
        <div class="page-subtitle">Seasonality, growth momentum, rolling averages & structural patterns · {data_period}</div>
    </div></div>""", unsafe_allow_html=True)

    exp, imp = load_data()
    ann      = get_annual_totals()
    monthly  = get_monthly_totals()

    if 'date' not in monthly.columns:
        monthly = monthly.sort_values(['Year','Month_Num']).reset_index(drop=True)
        monthly['date'] = pd.to_datetime(
            monthly['Year'].astype(str) + '-' +
            monthly['Month_Num'].astype(str).str.zfill(2) + '-01')

    # ── Pre-compute everything ONCE outside tabs ──────────────────────────
    total_years = monthly['Year'].nunique()

    # Month-level year counts (to distinguish full vs partial months)
    month_counts = (monthly.groupby('Month')['Year']
                    .count()
                    .reset_index()
                    .rename(columns={'Year': 'n_years'}))

    # Seasonality aggregates
    seas_e = (monthly.groupby('Month')
              .agg(avg=('DOLLARS_exp', 'mean'), std=('DOLLARS_exp', 'std'))
              .reset_index())
    seas_e['MC'] = pd.Categorical(seas_e['Month'], categories=MONTH_ORDER, ordered=True)
    seas_e = (seas_e.sort_values('MC')
              .merge(month_counts, on='Month', how='left')
              .reset_index(drop=True))
    seas_e['avg_m'] = seas_e['avg'] / 1e3
    seas_e['std_m'] = seas_e['std'] / 1e3
    seas_e['idx']   = seas_e['avg'] / seas_e['avg'].mean() * 100

    seas_i = (monthly.groupby('Month')
              .agg(avg=('DOLLARS_imp', 'mean'), std=('DOLLARS_imp', 'std'))
              .reset_index())
    seas_i['MC'] = pd.Categorical(seas_i['Month'], categories=MONTH_ORDER, ordered=True)
    seas_i = (seas_i.sort_values('MC')
              .merge(month_counts, on='Month', how='left')
              .reset_index(drop=True))
    seas_i['avg_m'] = seas_i['avg'] / 1e3
    seas_i['std_m'] = seas_i['std'] / 1e3
    seas_i['idx']   = seas_i['avg'] / seas_i['avg'].mean() * 100

    partial_mask_e = seas_e['n_years'] < total_years
    partial_mask_i = seas_i['n_years'] < total_years
    partial_months_short = seas_e[partial_mask_e]['Month'].str[:3].tolist()

    # YoY growth
    monthly_s = monthly.sort_values('date').copy().reset_index(drop=True)
    monthly_s['exp_yoy'] = monthly_s.groupby('Month')['DOLLARS_exp'].pct_change() * 100
    monthly_s['imp_yoy'] = monthly_s.groupby('Month')['DOLLARS_imp'].pct_change() * 100

    # Rolling averages
    mr = monthly.sort_values('date').copy().reset_index(drop=True)
    mr['exp_ma3'] = mr['DOLLARS_exp'].rolling(3).mean()
    mr['exp_ma6'] = mr['DOLLARS_exp'].rolling(6).mean()
    mr['imp_ma6'] = mr['DOLLARS_imp'].rolling(6).mean()
    mr['bal_ma3'] = mr['balance'].rolling(3).mean()

    # Annual growth
    ann2 = ann.copy()
    ann2['exp_g'] = ann2['exports'].pct_change() * 100
    ann2['imp_g'] = ann2['imports'].pct_change() * 100
    ann2 = ann2.dropna().reset_index(drop=True)

    # ── Tabs ──────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["🌊 Seasonality", "📉 Growth Momentum", "🔭 Rolling Analytics"])

    # ═══════════════════════════════════════════════════════════
    with tab1:
        partial_note = (f"Jan–{latest_m} = {total_years} yrs · "
                        f"Apr–Dec = {total_years-1} yrs ({min_yr}–{max_yr-1} only, "
                        f"{max_yr} stops at {latest_m})")
        period_banner("Seasonality Data Period", data_period, '#10d9a0',
                      f"Monthly averages calculated across all {total_years} years of data")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="chart-card"><div class="chart-title">🌊 Export Seasonality — Monthly Average ± 1σ</div>', unsafe_allow_html=True)
            fig = go.Figure()
            for m in partial_months_short:
                fig.add_vrect(x0=m, x1=m, fillcolor='rgba(245,158,11,0.06)', line_width=0, layer='below')
            fig.add_trace(go.Scatter(x=seas_e['Month'].str[:3], y=seas_e['avg_m']+seas_e['std_m'],
                fill=None, mode='lines', line=dict(color='rgba(0,0,0,0)'), showlegend=False))
            fig.add_trace(go.Scatter(x=seas_e['Month'].str[:3], y=seas_e['avg_m']-seas_e['std_m'],
                fill='tonexty', mode='lines', fillcolor='rgba(16,217,160,0.08)',
                line=dict(color='rgba(0,0,0,0)'), name='±1σ band', showlegend=True))
            fig.add_trace(go.Scatter(
                x=seas_e[~partial_mask_e]['Month'].str[:3], y=seas_e[~partial_mask_e]['avg_m'],
                mode='lines+markers', name=f'Avg ({total_years} yrs)',
                line=dict(color='#10d9a0', width=3),
                marker=dict(size=11, color='#10d9a0', symbol='circle'),
                hovertemplate='<b>%{x}</b>: $%{y:.0f}M avg (' + str(total_years) + ' years)<extra></extra>'))
            if partial_mask_e.any():
                fig.add_trace(go.Scatter(
                    x=seas_e[partial_mask_e]['Month'].str[:3], y=seas_e[partial_mask_e]['avg_m'],
                    mode='markers', name=f'Avg ({total_years-1} yrs · {max_yr} N/A)',
                    marker=dict(size=12, color='#f59e0b', symbol='diamond',
                                line=dict(color='#f59e0b', width=2)),
                    hovertemplate='<b>%{x}</b>: $%{y:.0f}M avg<br>⚠ ' + str(total_years-1) + f' years only ({min_yr}–{max_yr-1})<extra></extra>'))
            fig.update_layout(**pl(315, yaxis=dict(title='USD Millions'),
                legend=dict(orientation='h', y=1.05, bgcolor='rgba(0,0,0,0)', font=dict(color='#64748b', size=10))))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="chart-card"><div class="chart-title">🌊 Import Seasonality — Monthly Average ± 1σ</div>', unsafe_allow_html=True)
            fig2 = go.Figure()
            for m in partial_months_short:
                fig2.add_vrect(x0=m, x1=m, fillcolor='rgba(245,158,11,0.06)', line_width=0, layer='below')
            fig2.add_trace(go.Scatter(x=seas_i['Month'].str[:3], y=seas_i['avg_m']+seas_i['std_m'],
                fill=None, mode='lines', line=dict(color='rgba(0,0,0,0)'), showlegend=False))
            fig2.add_trace(go.Scatter(x=seas_i['Month'].str[:3], y=seas_i['avg_m']-seas_i['std_m'],
                fill='tonexty', mode='lines', fillcolor='rgba(244,63,94,0.08)',
                line=dict(color='rgba(0,0,0,0)'), name='±1σ band', showlegend=True))
            fig2.add_trace(go.Scatter(
                x=seas_i[~partial_mask_i]['Month'].str[:3], y=seas_i[~partial_mask_i]['avg_m'],
                mode='lines+markers', name=f'Avg ({total_years} yrs)',
                line=dict(color='#f43f5e', width=3),
                marker=dict(size=11, color='#f43f5e', symbol='circle'),
                hovertemplate='<b>%{x}</b>: $%{y:.0f}M avg (' + str(total_years) + ' years)<extra></extra>'))
            if partial_mask_i.any():
                fig2.add_trace(go.Scatter(
                    x=seas_i[partial_mask_i]['Month'].str[:3], y=seas_i[partial_mask_i]['avg_m'],
                    mode='markers', name=f'Avg ({total_years-1} yrs · {max_yr} N/A)',
                    marker=dict(size=12, color='#f59e0b', symbol='diamond',
                                line=dict(color='#f59e0b', width=2)),
                    hovertemplate='<b>%{x}</b>: $%{y:.0f}M avg<br>⚠ ' + str(total_years-1) + f' years only ({min_yr}–{max_yr-1})<extra></extra>'))
            fig2.update_layout(**pl(315, yaxis=dict(title='USD Millions'),
                legend=dict(orientation='h', y=1.05, bgcolor='rgba(0,0,0,0)', font=dict(color='#64748b', size=10))))
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        # Seasonal Index
        period_banner("Seasonal Index Period", data_period, '#f59e0b',
                      f"Index = monthly avg ÷ annual avg × 100  |  ⚠ Hatched = {total_years-1} yrs only (Apr–Dec, {max_yr} missing)")
        st.markdown('<div class="chart-card"><div class="chart-title">📊 Seasonal Index — Export & Import (Annual Average = 100)</div>', unsafe_allow_html=True)
        fig3 = go.Figure()
        fig3.add_hline(y=100, line=dict(color='rgba(255,255,255,0.2)', dash='dot', width=1.5),
            annotation_text='Baseline = 100', annotation_font=dict(color='#64748b', size=9))
        for df_s, base_color, name_prefix in [(seas_e, '#10d9a0', 'Export'), (seas_i, '#f43f5e', 'Import')]:
            pm = df_s['n_years'] < total_years
            if (~pm).any():
                fig3.add_trace(go.Bar(
                    x=df_s[~pm]['Month'].str[:3], y=df_s[~pm]['idx'],
                    name=f'{name_prefix} ({total_years} yrs)', marker_color=base_color, opacity=0.88,
                    hovertemplate='<b>%{x}</b> ' + name_prefix + ' Index: %{y:.1f}<br>' + str(total_years) + ' years<extra></extra>'))
            if pm.any():
                fig3.add_trace(go.Bar(
                    x=df_s[pm]['Month'].str[:3], y=df_s[pm]['idx'],
                    name=f'{name_prefix} ({total_years-1} yrs · {max_yr} N/A)',
                    marker=dict(color=base_color, opacity=0.45,
                                pattern=dict(shape='/', size=6, solidity=0.4)),
                    hovertemplate=('<b>%{x}</b> ' + name_prefix + ' Index: %{y:.1f}<br>'
                                   '⚠ ' + str(total_years-1) + f' years only ({min_yr}–{max_yr-1})<extra></extra>')))
        fig3.add_annotation(x=0.99, y=1.1, xref='paper', yref='paper',
            text=f'⚠ Hatched bars = Apr–Dec based on {total_years-1} years ({min_yr}–{max_yr-1} only)',
            showarrow=False, font=dict(size=10, color='#f59e0b'), align='right')
        fig3.update_layout(**pl(315, yaxis=dict(title='Seasonal Index'), barmode='group',
            legend=dict(orientation='h', y=-0.25, bgcolor='rgba(0,0,0,0)', font=dict(color='#64748b', size=10))))
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

        # YoY overlay
        period_banner("Year-Over-Year Overlay", data_period, '#60a5fa',
                      f"Each line = one year's monthly exports  |  {max_yr} highlighted as solid line")
        st.markdown('<div class="chart-card"><div class="chart-title">🔄 Year-Over-Year Monthly Export Overlay — All Years</div>', unsafe_allow_html=True)
        all_years = sorted(monthly['Year'].unique())
        year_pal  = ['#475569', '#64748b', '#a78bfa', '#60a5fa', '#f59e0b', '#10d9a0', '#f43f5e', '#2dd4bf']
        fig4 = go.Figure()
        for i, yr in enumerate(all_years):
            d = monthly[monthly['Year'] == yr].sort_values('Month_Num')
            is_latest = yr == max_yr
            fig4.add_trace(go.Scatter(
                x=d['Month'].str[:3], y=d['DOLLARS_exp'] / 1e3,
                mode='lines+markers', name=str(yr),
                line=dict(color=year_pal[i % len(year_pal)], width=3 if is_latest else 1.5,
                          dash='solid' if is_latest else 'dot'),
                marker=dict(size=8 if is_latest else 5),
                hovertemplate=f'<b>%{{x}} {yr}</b>: $%{{y:.0f}}M<extra></extra>'))
        fig4.update_layout(**pl(315, yaxis=dict(title='USD Millions'),
            legend=dict(orientation='h', y=1.05, bgcolor='rgba(0,0,0,0)', font=dict(color='#64748b'))))
        st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════
    with tab2:
        period_banner("YoY Growth Period", data_period, '#60a5fa',
                      "Compares each month against same month in previous year")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="chart-card"><div class="chart-title">📈 Monthly Export YoY Growth (%)</div>', unsafe_allow_html=True)
            d = monthly_s.dropna(subset=['exp_yoy'])
            fig5 = go.Figure()
            fig5.add_hline(y=0, line=dict(color='rgba(255,255,255,0.15)', width=1))
            fig5.add_trace(go.Bar(x=d['date'], y=d['exp_yoy'],
                marker_color=['#10d9a0' if x >= 0 else '#f43f5e' for x in d['exp_yoy']],
                hovertemplate='<b>%{x|%b %Y}</b>: %{y:+.1f}%<extra></extra>'))
            fig5.update_layout(**pl(290,
                xaxis=dict(tickformat='%b %Y', dtick='M6', tickangle=-30),
                yaxis=dict(title='YoY %'), showlegend=False))
            st.plotly_chart(fig5, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="chart-card"><div class="chart-title">📉 Monthly Import YoY Growth (%)</div>', unsafe_allow_html=True)
            d2 = monthly_s.dropna(subset=['imp_yoy'])
            fig6 = go.Figure()
            fig6.add_hline(y=0, line=dict(color='rgba(255,255,255,0.15)', width=1))
            fig6.add_trace(go.Bar(x=d2['date'], y=d2['imp_yoy'],
                marker_color=['#f43f5e' if x >= 0 else '#10d9a0' for x in d2['imp_yoy']],
                hovertemplate='<b>%{x|%b %Y}</b>: %{y:+.1f}%<extra></extra>'))
            fig6.update_layout(**pl(290,
                xaxis=dict(tickformat='%b %Y', dtick='M6', tickangle=-30),
                yaxis=dict(title='YoY %'), showlegend=False))
            st.plotly_chart(fig6, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        period_banner("Annual Growth Period", full_yr_period, '#a78bfa',
                      "Year-on-year change in total annual trade values")
        st.markdown('<div class="chart-card"><div class="chart-title">📊 Annual Growth Rates — Exports vs Imports (%)</div>', unsafe_allow_html=True)
        fig7 = go.Figure()
        fig7.add_hline(y=0, line=dict(color='rgba(255,255,255,0.15)', width=1))
        fig7.add_trace(go.Bar(x=ann2['Year'], y=ann2['exp_g'], name='Export Growth',
            marker_color='#10d9a0', opacity=0.9,
            text=[f"{v:+.1f}%" for v in ann2['exp_g']], textposition='outside',
            textfont=dict(color='#10d9a0', size=11),
            hovertemplate='<b>Export Growth %{x}</b>: %{y:+.1f}%<extra></extra>'))
        fig7.add_trace(go.Bar(x=ann2['Year'], y=ann2['imp_g'], name='Import Growth',
            marker_color='#f43f5e', opacity=0.9,
            text=[f"{v:+.1f}%" for v in ann2['imp_g']], textposition='outside',
            textfont=dict(color='#f43f5e', size=11),
            hovertemplate='<b>Import Growth %{x}</b>: %{y:+.1f}%<extra></extra>'))
        fig7.update_layout(**pl(310, yaxis=dict(title='YoY Growth (%)'), barmode='group',
            legend=dict(orientation='h', y=1.05, bgcolor='rgba(0,0,0,0)', font=dict(color='#64748b'))))
        st.plotly_chart(fig7, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════
    with tab3:
        period_banner("Rolling Averages Period", data_period, '#2dd4bf',
                      "3M and 6M trailing moving averages smooth short-term volatility")

        st.markdown('<div class="chart-card"><div class="chart-title">📈 Rolling 3M & 6M Moving Averages — Exports (USD Millions)</div>', unsafe_allow_html=True)
        fig8 = go.Figure()
        fig8.add_trace(go.Scatter(x=mr['date'], y=mr['DOLLARS_exp'] / 1e3,
            mode='lines', name='Monthly', line=dict(color='rgba(16,217,160,0.25)', width=1),
            hovertemplate='<b>%{x|%b %Y}</b>: $%{y:.0f}M<extra></extra>'))
        fig8.add_trace(go.Scatter(x=mr['date'], y=mr['exp_ma3'] / 1e3,
            mode='lines', name='3M MA', line=dict(color='#10d9a0', width=2.5),
            hovertemplate='<b>3M MA %{x|%b %Y}</b>: $%{y:.0f}M<extra></extra>'))
        fig8.add_trace(go.Scatter(x=mr['date'], y=mr['exp_ma6'] / 1e3,
            mode='lines', name='6M MA', line=dict(color='#f59e0b', width=2.5, dash='dot'),
            hovertemplate='<b>6M MA %{x|%b %Y}</b>: $%{y:.0f}M<extra></extra>'))
        fig8.update_layout(**pl(310,
            xaxis=dict(tickformat='%b %Y', dtick='M6', tickangle=-30),
            yaxis=dict(title='USD Millions'),
            legend=dict(orientation='h', y=1.05, bgcolor='rgba(0,0,0,0)', font=dict(color='#64748b'))))
        st.plotly_chart(fig8, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="chart-card"><div class="chart-title">📉 6M Rolling Import Average</div>', unsafe_allow_html=True)
            fig9 = go.Figure()
            fig9.add_trace(go.Scatter(x=mr['date'], y=mr['DOLLARS_imp'] / 1e3,
                mode='lines', name='Monthly', line=dict(color='rgba(244,63,94,0.25)', width=1),
                hovertemplate='<b>%{x|%b %Y}</b>: $%{y:.0f}M<extra></extra>'))
            fig9.add_trace(go.Scatter(x=mr['date'], y=mr['imp_ma6'] / 1e3,
                mode='lines', name='6M MA', line=dict(color='#f43f5e', width=3),
                hovertemplate='<b>6M MA %{x|%b %Y}</b>: $%{y:.0f}M<extra></extra>'))
            fig9.update_layout(**pl(290,
                xaxis=dict(tickformat='%b %Y', dtick='M6', tickangle=-30),
                yaxis=dict(title='USD Millions'),
                legend=dict(orientation='h', y=1.05, bgcolor='rgba(0,0,0,0)', font=dict(color='#64748b'))))
            st.plotly_chart(fig9, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="chart-card"><div class="chart-title">⚖️ Rolling 3M Balance Average</div>', unsafe_allow_html=True)
            fig10 = go.Figure()
            fig10.add_hline(y=0, line=dict(color='rgba(255,255,255,0.15)', width=1))
            fig10.add_trace(go.Scatter(x=mr['date'], y=mr['bal_ma3'] / 1e3,
                mode='lines', fill='tozeroy', fillcolor='rgba(244,63,94,0.08)',
                line=dict(color='#f59e0b', width=2.5),
                hovertemplate='<b>3M MA %{x|%b %Y}</b>: $%{y:.0f}M<extra></extra>'))
            fig10.update_layout(**pl(290,
                xaxis=dict(tickformat='%b %Y', dtick='M6', tickangle=-30),
                yaxis=dict(title='USD Millions'), showlegend=False))
            st.plotly_chart(fig10, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        period_banner("Correlation Matrix Period", full_yr_period, '#a78bfa',
                      "Annual USD values  |  +1.0 = perfect co-movement  |  -1.0 = inverse movement")
        st.markdown('<div class="chart-card"><div class="chart-title">🔗 Export Category Correlation Matrix (Annual)</div>', unsafe_allow_html=True)
        ec_piv = (exp.groupby(['Year', 'CATEGORY'])['DOLLARS'].sum()
                  .reset_index()
                  .pivot_table(index='Year', columns='CATEGORY', values='DOLLARS')
                  .fillna(0))
        corr = ec_piv.corr()
        fig11 = go.Figure(go.Heatmap(
            z=corr.values, x=list(corr.columns), y=list(corr.index),
            colorscale=[[0, '#f43f5e'], [0.5, '#1a2236'], [1, '#10d9a0']],
            zmid=0, zmin=-1, zmax=1,
            text=[[f"{v:.2f}" for v in row] for row in corr.values],
            texttemplate='%{text}', textfont=dict(size=10, color='#e2e8f0'),
            colorbar=dict(tickfont=dict(color='#64748b'), outlinecolor='rgba(0,0,0,0)')))
        fig11.update_layout(**pl(290,
            xaxis=dict(tickfont=dict(size=9), tickangle=-20),
            yaxis=dict(tickfont=dict(size=9))))
        st.plotly_chart(fig11, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)
