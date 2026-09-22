import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_utils import *

def render():
    min_yr, max_yr, latest_m = get_date_range()
    data_period = f"{min_yr} – {latest_m} {max_yr}"

    st.markdown(f"""
    <div class="page-header">
        <div>
            <div class="section-badge">Command Center</div>
            <div class="page-title">Pakistan Trade Intelligence Hub</div>
            <div class="page-subtitle">External trade statistics {data_period} · Pakistan Bureau of Statistics</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    ann     = get_annual_totals()
    monthly = get_monthly_totals()

    # ── Defensive date column ──────────────────────────────────────────────
    if 'date' not in monthly.columns:
        monthly = monthly.sort_values(['Year','Month_Num']).reset_index(drop=True)
        monthly['date'] = pd.to_datetime(
            monthly['Year'].astype(str) + '-' +
            monthly['Month_Num'].astype(str).str.zfill(2) + '-01'
        )

    # ── Dynamic KPI reference years ────────────────────────────────────────
    latest_full_yr = ann[ann['Year'] < max_yr]['Year'].max()   # last complete year
    latest_row = ann[ann['Year'] == latest_full_yr].iloc[0]
    prev_row   = ann[ann['Year'] == latest_full_yr - 1].iloc[0] if latest_full_yr - 1 in ann['Year'].values else latest_row

    exp_delta = (latest_row['exports'] - prev_row['exports']) / prev_row['exports'] * 100
    imp_delta = (latest_row['imports'] - prev_row['imports']) / prev_row['imports'] * 100

    total_exp    = ann['exports'].sum()
    total_imp    = ann['imports'].sum()
    total_deficit= ann['balance'].sum()
    best_exp_row = ann.loc[ann['exports'].idxmax()]

    def kpi(col, label, value, sub, delta=None, color='green'):
        vc = {'green':'#10d9a0','red':'#f43f5e','gold':'#f59e0b',
              'blue':'#60a5fa','purple':'#a78bfa','teal':'#2dd4bf'}.get(color,'#e2e8f0')
        dhtml = ""
        if delta is not None:
            cls   = "delta-pos" if delta >= 0 else "delta-neg"
            arrow = "▲" if delta >= 0 else "▼"
            dhtml = f'<div class="metric-delta {cls}">{arrow} {abs(delta):.1f}% YoY</div>'
        col.markdown(f"""<div class="metric-card {color}">
        <div class="metric-label">{label}</div>
        <div class="metric-value" style="color:{vc};">{value}</div>
        <div class="metric-sub">{sub}</div>{dhtml}
        </div>""", unsafe_allow_html=True)

    # Row 1 — latest full year
    c1,c2,c3,c4,c5 = st.columns(5)
    kpi(c1, f"📤 Exports ({latest_full_yr})",  fmt_usd(latest_row['exports']),  "USD Thousands", exp_delta, 'green')
    kpi(c2, f"📥 Imports ({latest_full_yr})",  fmt_usd(latest_row['imports']),  "USD Thousands", imp_delta, 'red')
    kpi(c3, f"⚖️ Deficit ({latest_full_yr})",  fmt_usd(abs(latest_row['balance'])), "Trade Deficit", None, 'gold')
    kpi(c4, "📊 Coverage Ratio", f"{latest_row['coverage_ratio']}%", f"Exports÷Imports {latest_full_yr}", None, 'blue')
    kpi(c5, "🔁 Trade Volume",   fmt_usd(latest_row['trade_volume']), f"{latest_full_yr} total", None, 'purple')

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # Row 2 — cumulative
    c1,c2,c3,c4 = st.columns(4)
    kpi(c1, f"📦 Total Exports ({min_yr}–{max_yr})", fmt_usd(total_exp),   "Cumulative",  None, 'green')
    kpi(c2, f"🛒 Total Imports ({min_yr}–{max_yr})", fmt_usd(total_imp),   "Cumulative",  None, 'red')
    kpi(c3, "💸 Cumulative Deficit",                 fmt_usd(abs(total_deficit)), f"{min_yr}–{max_yr}", None, 'gold')
    kpi(c4, "🏆 Best Export Year", str(int(best_exp_row['Year'])), fmt_usd(best_exp_row['exports']), None, 'teal')

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

    # ── Monthly timeline ────────────────────────────────────────────────────
    col1, col2 = st.columns([3,2])
    with col1:
        st.markdown('<div class="chart-card"><div class="chart-title">📈 Monthly Trade Flows — Full Timeline (USD Millions)</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=monthly['date'], y=monthly['DOLLARS_imp']/1e3,
            fill=None, mode='lines', line=dict(color='rgba(0,0,0,0)'), showlegend=False, hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=monthly['date'], y=monthly['DOLLARS_exp']/1e3,
            fill='tonexty', mode='lines', fillcolor='rgba(244,63,94,0.07)',
            line=dict(color='rgba(0,0,0,0)'), showlegend=False, hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=monthly['date'], y=monthly['DOLLARS_imp']/1e3,
            mode='lines', name='Imports', line=dict(color='#f43f5e', width=2.5),
            hovertemplate='<b>Imports %{x|%b %Y}</b>: $%{y:.0f}M<extra></extra>'))
        fig.add_trace(go.Scatter(x=monthly['date'], y=monthly['DOLLARS_exp']/1e3,
            mode='lines', name='Exports', line=dict(color='#10d9a0', width=2.5),
            hovertemplate='<b>Exports %{x|%b %Y}</b>: $%{y:.0f}M<extra></extra>'))
        fig.update_layout(**pl(320,
            xaxis=dict(tickformat='%b %Y', dtick='M6', tickangle=-30),
            yaxis=dict(title='USD Millions'),
            legend=dict(orientation='h', y=1.05, bgcolor='rgba(0,0,0,0)', font=dict(color='#64748b'))
        ))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card"><div class="chart-title">📊 Annual Trade Summary (USD Billions)</div>', unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=ann['Year'], y=ann['imports']/1e6, name='Imports', marker_color='#f43f5e',
            hovertemplate='<b>Imports %{x}</b>: $%{y:.2f}B<extra></extra>'))
        fig2.add_trace(go.Bar(x=ann['Year'], y=ann['exports']/1e6, name='Exports', marker_color='#10d9a0',
            hovertemplate='<b>Exports %{x}</b>: $%{y:.2f}B<extra></extra>'))
        fig2.update_layout(**pl(320, yaxis=dict(title='USD Billions'), barmode='group',
            legend=dict(orientation='h', y=1.05, bgcolor='rgba(0,0,0,0)', font=dict(color='#64748b'))))
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Balance + Coverage + Volume ──────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="chart-card"><div class="chart-title">⚖️ Annual Trade Balance (USD Billions)</div>', unsafe_allow_html=True)
        fig3 = go.Figure(go.Bar(
            x=ann['Year'], y=ann['balance']/1e6,
            marker_color=['#f43f5e' if x<0 else '#10d9a0' for x in ann['balance']],
            text=[fmt_usd(v) for v in ann['balance']], textposition='outside',
            textfont=dict(color='#64748b', size=10),
            hovertemplate='<b>Balance %{x}</b>: $%{y:.2f}B<extra></extra>'
        ))
        fig3.update_layout(**pl(280, yaxis=dict(title='USD Billions'), showlegend=False))
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card"><div class="chart-title">📐 Export Coverage Ratio (%)</div>', unsafe_allow_html=True)
        fig4 = go.Figure()
        fig4.add_shape(type='line', x0=ann['Year'].min()-0.5, x1=ann['Year'].max()+0.5,
            y0=100, y1=100, line=dict(color='rgba(255,255,255,0.15)', dash='dot', width=1.5))
        fig4.add_trace(go.Scatter(x=ann['Year'], y=ann['coverage_ratio'],
            mode='lines+markers+text', line=dict(color='#60a5fa', width=3),
            marker=dict(size=10, color='#60a5fa'),
            text=[f"{v}%" for v in ann['coverage_ratio']],
            textposition='top center', textfont=dict(color='#60a5fa', size=11),
            hovertemplate='<b>%{x}</b>: %{y}% coverage<extra></extra>'))
        fig4.update_layout(**pl(280, yaxis=dict(title='%', range=[0, max(ann['coverage_ratio'])+20]), showlegend=False))
        st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="chart-card"><div class="chart-title">🔁 Trade Volume (USD Billions)</div>', unsafe_allow_html=True)
        fig5 = go.Figure(go.Scatter(x=ann['Year'], y=ann['trade_volume']/1e6,
            mode='lines+markers', fill='tozeroy', fillcolor='rgba(167,139,250,0.08)',
            line=dict(color='#a78bfa', width=2.5), marker=dict(size=8),
            hovertemplate='<b>Volume %{x}</b>: $%{y:.2f}B<extra></extra>'))
        fig5.update_layout(**pl(280, yaxis=dict(title='USD Billions'), showlegend=False))
        st.plotly_chart(fig5, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Category donuts ────────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    exp_cat = get_category_annual('export')
    imp_cat = get_category_annual('import')

    with col1:
        st.markdown('<div class="chart-card"><div class="chart-title">🏭 Export Mix by Category (All Years)</div>', unsafe_allow_html=True)
        ec = exp_cat.groupby('CATEGORY')['DOLLARS'].sum().reset_index().sort_values('DOLLARS', ascending=False)
        ec = ec[ec['DOLLARS']>0]
        fig6 = go.Figure(go.Pie(
            labels=ec['CATEGORY'], values=ec['DOLLARS']/1e6, hole=0.55,
            marker=dict(colors=[CATEGORY_COLORS_EXP.get(c,'#64748b') for c in ec['CATEGORY']],
                        line=dict(color='#0a0e1a', width=2)),
            textinfo='label+percent', textfont=dict(size=10, color='#e2e8f0'),
            hovertemplate='<b>%{label}</b><br>$%{value:.1f}B · %{percent}<extra></extra>'
        ))
        fig6.update_layout(**pl(300,
            annotations=[dict(text='Exports',x=0.5,y=0.5,font=dict(size=14,color='#e2e8f0',family='Space Grotesk'),showarrow=False)]))
        st.plotly_chart(fig6, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card"><div class="chart-title">🛒 Import Mix by Category (All Years)</div>', unsafe_allow_html=True)
        ic = imp_cat.groupby('CATEGORY')['DOLLARS'].sum().reset_index().sort_values('DOLLARS', ascending=False)
        ic = ic[ic['DOLLARS']>0]
        fig7 = go.Figure(go.Pie(
            labels=ic['CATEGORY'], values=ic['DOLLARS']/1e6, hole=0.55,
            marker=dict(colors=[CATEGORY_COLORS_IMP.get(c,'#64748b') for c in ic['CATEGORY']],
                        line=dict(color='#0a0e1a', width=2)),
            textinfo='label+percent', textfont=dict(size=10, color='#e2e8f0'),
            hovertemplate='<b>%{label}</b><br>$%{value:.1f}B · %{percent}<extra></extra>'
        ))
        fig7.update_layout(**pl(300,
            annotations=[dict(text='Imports',x=0.5,y=0.5,font=dict(size=14,color='#e2e8f0',family='Space Grotesk'),showarrow=False)]))
        st.plotly_chart(fig7, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Seasonality heatmap ────────────────────────────────────────────────
    st.markdown('<div class="chart-card"><div class="chart-title">🌡️ Monthly Trade Balance Heatmap — Seasonality Pattern (USD Millions)</div>', unsafe_allow_html=True)
    pvt = monthly.pivot_table(index='Year', columns='Month', values='balance', aggfunc='sum') / 1e3
    pvt = pvt.reindex(columns=[m for m in MONTH_ORDER if m in pvt.columns])
    fig8 = go.Figure(go.Heatmap(
        z=pvt.values, x=[m[:3] for m in pvt.columns], y=[str(y) for y in pvt.index],
        colorscale=[[0,'#f43f5e'],[0.5,'#1a2236'],[1,'#10d9a0']], zmid=0,
        text=[[f"${v:.0f}M" for v in row] for row in pvt.values],
        texttemplate='%{text}', textfont=dict(size=10, color='#e2e8f0'),
        hovertemplate='<b>%{y} %{x}</b>: $%{z:.0f}M<extra></extra>',
        colorbar=dict(tickfont=dict(color='#64748b'), outlinecolor='rgba(0,0,0,0)')
    ))
    fig8.update_layout(**pl(max(200, len(pvt)*38), yaxis=dict(autorange='reversed')))
    st.plotly_chart(fig8, use_container_width=True, config={'displayModeBar':False})
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Insights ───────────────────────────────────────────────────────────
    st.markdown("<div class='section-badge' style='margin-top:0.5rem;'>🔍 Key Insights</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    bm  = monthly.loc[monthly['DOLLARS_exp'].idxmax()]
    wb  = monthly.loc[monthly['balance'].idxmin()]
    avg = monthly['balance'].mean() / 1e3

    with col1:
        st.markdown(f"""<div class="insight-box"><strong style="color:#10d9a0;">📤 Peak Export Month</strong><br>
        <b>{bm['Month']} {int(bm['Year'])}</b> — highest single-month exports at <strong>{fmt_usd(bm['DOLLARS_exp'])}</strong>.</div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="insight-box" style="background:linear-gradient(135deg,rgba(244,63,94,0.07),rgba(244,63,94,0.02));border-color:rgba(244,63,94,0.2);">
        <strong style="color:#f43f5e;">📉 Largest Deficit Month</strong><br>
        <b>{wb['Month']} {int(wb['Year'])}</b> — highest monthly deficit: <strong>{fmt_usd(abs(wb['balance']))}</strong>.</div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="insight-box" style="background:linear-gradient(135deg,rgba(245,158,11,0.07),rgba(245,158,11,0.02));border-color:rgba(245,158,11,0.2);">
        <strong style="color:#f59e0b;">📊 Average Monthly Deficit</strong><br>
        Avg monthly deficit: <strong>${abs(avg):.0f}M</strong> over the full {data_period} period.</div>""", unsafe_allow_html=True)
