import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_utils import *

def render():
    min_yr, max_yr, latest_m = get_date_range()
    data_period = f"{min_yr} – {latest_m} {max_yr}"

    st.markdown(f"""
    <div class="page-header"><div>
        <div class="section-badge">Export Analysis</div>
        <div class="page-title">📦 Pakistan Exports Deep Dive</div>
        <div class="page-subtitle">Commodity-level export intelligence · {data_period}</div>
    </div></div>""", unsafe_allow_html=True)

    exp, _ = load_data()
    ann    = get_annual_totals()
    monthly= get_monthly_totals()
    years  = sorted(ann['Year'].unique(), reverse=True)

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        year_sel = st.selectbox("Focus Year", years, key='exp_year')
    with col_f2:
        compare_yr_opts = [y for y in years if y != year_sel]
        compare_year = st.selectbox("Compare Against", compare_yr_opts, key='exp_compare')
    with col_f3:
        categories = ['All Categories'] + sorted(exp['CATEGORY'].dropna().unique())
        cat_sel = st.selectbox("Category", categories, key='exp_cat')

    df_y  = exp[exp['Year']==year_sel]
    df_py = exp[exp['Year']==compare_year]
    if cat_sel != 'All Categories':
        df_y  = df_y[df_y['CATEGORY']==cat_sel]
        df_py = df_py[df_py['CATEGORY']==cat_sel]

    tot_y  = df_y['DOLLARS'].sum()
    tot_py = df_py['DOLLARS'].sum()
    yoy    = (tot_y - tot_py) / tot_py * 100 if tot_py > 0 else 0
    qty_y  = df_y['QUANTITY'].sum()
    top_p  = df_y.groupby('PRODUCT')['DOLLARS'].sum().idxmax() if len(df_y)>0 else 'N/A'

    vc = {'green':'#10d9a0','red':'#f43f5e','gold':'#f59e0b','blue':'#60a5fa','purple':'#a78bfa'}
    def kpi(col, lbl, val, sub, delta=None, color='green'):
        dhtml=""
        if delta is not None:
            cls="delta-pos" if delta>=0 else "delta-neg"
            dhtml=f'<div class="metric-delta {cls}">{"▲" if delta>=0 else "▼"} {abs(delta):.1f}%</div>'
        col.markdown(f"""<div class="metric-card {color}">
        <div class="metric-label">{lbl}</div>
        <div class="metric-value" style="color:{vc.get(color,'#e2e8f0')};">{val}</div>
        <div class="metric-sub">{sub}</div>{dhtml}</div>""", unsafe_allow_html=True)

    c1,c2,c3,c4,c5 = st.columns(5)
    kpi(c1,"Export Value",fmt_usd(tot_y),f"vs {fmt_usd(tot_py)} in {compare_year}",yoy,'green')
    kpi(c2,"YoY Growth",f"{yoy:+.1f}%",f"{year_sel} vs {compare_year}",None,'green' if yoy>=0 else 'red')
    kpi(c3,"Total Quantity",f"{qty_y/1e6:.1f}M MT","Volume exported",None,'blue')
    kpi(c4,"Top Product",str(top_p)[:18]+("…" if len(str(top_p))>18 else ""),"By USD value",None,'gold')
    kpi(c5,"Categories",str(df_y['CATEGORY'].nunique()),"Active groups",None,'purple')
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # ── Category trends ────────────────────────────────────────────────────
    col1, col2 = st.columns([3,2])
    exp_cat = get_category_annual('export')

    with col1:
        st.markdown('<div class="chart-card"><div class="chart-title">📊 Category Export Trends (Annual, USD Billions)</div>', unsafe_allow_html=True)
        ec = exp_cat.groupby(['Year','CATEGORY'])['DOLLARS'].sum().reset_index()
        fig = go.Figure()
        for cat in sorted(ec['CATEGORY'].unique()):
            d = ec[ec['CATEGORY']==cat].sort_values('Year')
            c = CATEGORY_COLORS_EXP.get(cat,'#64748b')
            fig.add_trace(go.Scatter(x=d['Year'], y=d['DOLLARS']/1e6,
                name=cat.replace(' GROUP','').title(), mode='lines+markers',
                line=dict(color=c,width=2.5), marker=dict(size=8,color=c),
                hovertemplate=f'<b>{cat}</b> %{{x}}: $%{{y:.2f}}B<extra></extra>'))
        fig.update_layout(**pl(300, yaxis=dict(title='USD Billions'),
            legend=dict(orientation='h',y=-0.28,bgcolor='rgba(0,0,0,0)',font=dict(color='#64748b',size=10))))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div class="chart-card"><div class="chart-title">📅 Monthly Exports — {year_sel} vs {compare_year}</div>', unsafe_allow_html=True)
        mon_y  = exp[exp['Year']==year_sel].groupby('Month')['DOLLARS'].sum().reset_index()
        mon_py = exp[exp['Year']==compare_year].groupby('Month')['DOLLARS'].sum().reset_index()
        for df in [mon_y, mon_py]:
            df['MC'] = pd.Categorical(df['Month'], categories=MONTH_ORDER, ordered=True)
            df.sort_values('MC', inplace=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=mon_py['Month'].str[:3], y=mon_py['DOLLARS']/1e3,
            name=str(compare_year), marker_color='rgba(255,255,255,0.1)',
            hovertemplate=f'<b>%{{x}} {compare_year}</b>: $%{{y:.0f}}M<extra></extra>'))
        fig2.add_trace(go.Bar(x=mon_y['Month'].str[:3], y=mon_y['DOLLARS']/1e3,
            name=str(year_sel), marker_color='#10d9a0',
            hovertemplate=f'<b>%{{x}} {year_sel}</b>: $%{{y:.0f}}M<extra></extra>'))
        fig2.update_layout(**pl(300, yaxis=dict(title='USD Millions'), barmode='group',
            legend=dict(orientation='h',y=1.05,bgcolor='rgba(0,0,0,0)',font=dict(color='#64748b'))))
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Top products + YoY ──────────────────────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="chart-card"><div class="chart-title">🏆 Top 15 Export Products — {year_sel}</div>', unsafe_allow_html=True)
        tp = exp[exp['Year']==year_sel].groupby('PRODUCT')['DOLLARS'].sum().reset_index()
        tp = tp[tp['PRODUCT'].notna() & (tp['PRODUCT']!='')].nlargest(15,'DOLLARS').sort_values('DOLLARS')
        fig3 = go.Figure(go.Bar(
            x=tp['DOLLARS']/1e3, y=tp['PRODUCT'], orientation='h',
            marker=dict(color=tp['DOLLARS'], colorscale=[[0,'#003d2d'],[0.5,'#00a870'],[1,'#10d9a0']], showscale=False),
            text=[fmt_usd(v) for v in tp['DOLLARS']], textposition='outside',
            textfont=dict(color='#64748b',size=10),
            hovertemplate='<b>%{y}</b>: $%{x:.0f}M<extra></extra>'
        ))
        fig3.update_layout(**pl(420,
            xaxis=dict(title='USD Millions'),
            yaxis=dict(tickfont=dict(size=10)),
            margin=dict(l=5,r=80,t=20,b=10), showlegend=False))
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div class="chart-card"><div class="chart-title">📈 YoY Growth by Product — {year_sel} vs {compare_year}</div>', unsafe_allow_html=True)
        p_y   = exp[exp['Year']==year_sel].groupby('PRODUCT')['DOLLARS'].sum()
        p_py  = exp[exp['Year']==compare_year].groupby('PRODUCT')['DOLLARS'].sum()
        gdf   = pd.DataFrame({'cur':p_y,'prev':p_py}).dropna()
        gdf   = gdf[(gdf['prev']>0) & (gdf['cur']>50000)]
        gdf['growth'] = (gdf['cur']-gdf['prev'])/gdf['prev']*100
        gdf   = gdf.sort_values('growth').tail(20)
        fig4  = go.Figure(go.Bar(
            x=gdf['growth'], y=gdf.index, orientation='h',
            marker_color=['#f43f5e' if x<0 else '#10d9a0' for x in gdf['growth']],
            text=[f"{v:+.1f}%" for v in gdf['growth']], textposition='outside',
            textfont=dict(color='#64748b',size=10),
            hovertemplate='<b>%{y}</b>: %{x:+.1f}%<extra></extra>'
        ))
        fig4.add_vline(x=0, line=dict(color='rgba(255,255,255,0.15)',width=1))
        fig4.update_layout(**pl(420,
            xaxis=dict(title='YoY Growth (%)'),
            yaxis=dict(tickfont=dict(size=10)),
            margin=dict(l=5,r=70,t=20,b=10), showlegend=False))
        st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Stacked area composition ────────────────────────────────────────────
    st.markdown('<div class="chart-card"><div class="chart-title">📦 Export Composition — Stacked Area (Monthly)</div>', unsafe_allow_html=True)
    exp_monthly_cat = exp.groupby(['Year','Month','Month_Num','CATEGORY'])['DOLLARS'].sum().reset_index()
    exp_monthly_cat['MC'] = pd.Categorical(exp_monthly_cat['Month'], categories=MONTH_ORDER, ordered=True)
    exp_monthly_cat = exp_monthly_cat.sort_values(['Year','Month_Num']).reset_index(drop=True)
    exp_monthly_cat['date'] = pd.to_datetime(
        exp_monthly_cat['Year'].astype(str)+'-'+exp_monthly_cat['Month_Num'].astype(str).str.zfill(2)+'-01')
    pivoted = exp_monthly_cat.pivot_table(index='date', columns='CATEGORY', values='DOLLARS', aggfunc='sum').fillna(0)

    def hex_to_rgba(h, a=0.75):
        h = h.lstrip('#'); r,g,b = int(h[0:2],16),int(h[2:4],16),int(h[4:6],16)
        return f'rgba({r},{g},{b},{a})'

    fig5 = go.Figure()
    for cat in pivoted.columns:
        c = CATEGORY_COLORS_EXP.get(cat,'#64748b')
        fig5.add_trace(go.Scatter(
            x=pivoted.index, y=pivoted[cat]/1e3,
            name=cat.replace(' GROUP','').title(), mode='lines', stackgroup='one',
            line=dict(width=0, color=c), fillcolor=hex_to_rgba(c),
            hovertemplate=f'<b>{cat}</b>: $%{{y:.0f}}M<extra></extra>'
        ))
    fig5.update_layout(**pl(300,
        xaxis=dict(tickformat='%b %Y', dtick='M6', tickangle=-30),
        yaxis=dict(title='USD Millions'),
        legend=dict(orientation='h',y=-0.3,bgcolor='rgba(0,0,0,0)',font=dict(color='#64748b',size=10))))
    st.plotly_chart(fig5, use_container_width=True, config={'displayModeBar':False})
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Category share + Scatter ────────────────────────────────────────────
    col1, col2 = st.columns([1,2])
    with col1:
        st.markdown(f'<div class="chart-card"><div class="chart-title">🌐 Category Share — {year_sel}</div>', unsafe_allow_html=True)
        ec_y = exp[exp['Year']==year_sel].groupby('CATEGORY')['DOLLARS'].sum().reset_index()
        ec_y = ec_y[ec_y['DOLLARS']>0]
        fig6 = go.Figure(go.Pie(
            labels=[c.replace(' GROUP','') for c in ec_y['CATEGORY']],
            values=ec_y['DOLLARS']/1e6, hole=0.5,
            marker=dict(colors=[CATEGORY_COLORS_EXP.get(c,'#64748b') for c in ec_y['CATEGORY']],
                        line=dict(color='#0a0e1a',width=2)),
            textinfo='percent+label', textfont=dict(size=10,color='#e2e8f0'),
            hovertemplate='<b>%{label}</b>: $%{value:.1f}B · %{percent}<extra></extra>'
        ))
        fig6.update_layout(**pl(300, margin=dict(l=0,r=0,t=10,b=0), showlegend=False))
        st.plotly_chart(fig6, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div class="chart-card"><div class="chart-title">⚡ Export Quantity vs Value — {year_sel} (Top Products)</div>', unsafe_allow_html=True)
        sc = exp[(exp['Year']==year_sel) & exp['QUANTITY'].notna() & (exp['QUANTITY']>0) & (exp['DOLLARS']>10000)].copy()
        sc = sc.groupby(['PRODUCT','CATEGORY']).agg({'QUANTITY':'sum','DOLLARS':'sum'}).reset_index().nlargest(40,'DOLLARS')
        fig7 = px.scatter(sc, x='QUANTITY', y=sc['DOLLARS']/1e3, size=sc['DOLLARS']/1e3,
            color='CATEGORY', hover_name='PRODUCT',
            color_discrete_map=CATEGORY_COLORS_EXP, size_max=60,
            labels={'y':'Value (USD Millions)','QUANTITY':'Quantity (MT)'})
        fig7.update_traces(marker=dict(opacity=0.8, line=dict(width=1,color='rgba(255,255,255,0.15)')))
        fig7.update_layout(**pl(300,
            xaxis=dict(title='Quantity (MT / Units)'),
            yaxis=dict(title='USD Millions'),
            legend=dict(orientation='h',y=-0.25,bgcolor='rgba(0,0,0,0)',font=dict(color='#64748b',size=10))))
        st.plotly_chart(fig7, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)
