import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_utils import *

def simple_forecast(series, n_ahead=12):
    x = np.arange(len(series))
    y = series.values
    valid = ~np.isnan(y)
    if valid.sum() < 4:
        return np.full(n_ahead, np.nanmean(y))
    coeffs = np.polyfit(x[valid], y[valid], 1)
    trend  = np.polyval(coeffs, np.arange(len(series), len(series)+n_ahead))
    if len(series) >= 12:
        seasonal = []
        for i in range(n_ahead):
            midx = (len(series)+i) % 12
            past = [y[j] for j in range(midx, len(series), 12) if not np.isnan(y[j])]
            seasonal.append(np.mean(past) - np.nanmean(y) if past else 0)
        return np.maximum(trend + np.array(seasonal), 0)
    return np.maximum(trend, 0)

def render():
    min_yr, max_yr, latest_m = get_date_range()
    data_period = f"{min_yr} – {latest_m} {max_yr}"

    st.markdown(f"""
    <div class="page-header"><div>
        <div class="section-badge">Scenario Forecaster</div>
        <div class="page-title">🔮 Trade Scenario Forecaster</div>
        <div class="page-subtitle">Statistical projections based on {data_period} historical patterns</div>
    </div></div>""", unsafe_allow_html=True)

    ann     = get_annual_totals()
    monthly = get_monthly_totals()

    if 'date' not in monthly.columns:
        monthly = monthly.sort_values(['YEAR','Month_Num']).reset_index(drop=True)
        monthly['date'] = pd.to_datetime(
            monthly['YEAR'].astype(str)+'-'+monthly['Month_Num'].astype(str).str.zfill(2)+'-01')

    ms = monthly.sort_values('date').reset_index(drop=True)

    st.markdown(f"""<div class="insight-box">
    <strong style="color:#10d9a0;">ℹ️ Methodology Note</strong><br>
    Forecasts use linear trend decomposition with seasonal adjustment based on historical monthly patterns from {data_period}.
    Projections are statistical only — actual outcomes depend on global commodity prices, PKR exchange rate,
    policy changes, and geopolitical factors not captured in historical data.
    </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # Scenario controls
    st.markdown('<div class="section-header">🎛️ Scenario Parameters</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        exp_shock = st.slider("Export Growth Adjustment (%)", -30, 50, 0, step=5)
    with col2:
        imp_shock = st.slider("Import Growth Adjustment (%)", -30, 50, 0, step=5)
    with col3:
        scenario = st.selectbox("Preset Scenario", [
            "Baseline","Optimistic Export Growth","Import Compression",
            "Energy Price Spike","Export + Import Growth","Austerity"])

    presets = {
        "Baseline": (0,0), "Optimistic Export Growth": (20,5),
        "Import Compression": (5,-15), "Energy Price Spike": (-5,25),
        "Export + Import Growth": (15,15), "Austerity": (-10,-20),
    }
    pe, pi = presets[scenario]
    exp_fc_base = simple_forecast(ms['DOLLARS_exp'])
    imp_fc_base = simple_forecast(ms['DOLLARS_imp'])
    exp_fc = exp_fc_base * (1 + (exp_shock+pe)/100)
    imp_fc = imp_fc_base * (1 + (imp_shock+pi)/100)
    bal_fc = exp_fc - imp_fc

    # Generate future date labels starting from last month+1
    last_date = ms['date'].max()
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=12, freq='MS')
    future_labels = [d.strftime('%b %Y') for d in future_dates]
    hist_x  = list(range(len(ms)))
    future_x = list(range(len(ms), len(ms)+12))

    # KPIs
    c1,c2,c3,c4 = st.columns(4)
    fc_cov = exp_fc.sum()/imp_fc.sum()*100 if imp_fc.sum()>0 else 0
    for col,lbl,val,sub,color in [
        (c1,"12M Fcst Exports",fmt_usd(exp_fc.sum()),f"Under '{scenario}'",'green'),
        (c2,"12M Fcst Imports",fmt_usd(imp_fc.sum()),f"Under '{scenario}'",'red'),
        (c3,"12M Fcst Balance",fmt_usd(bal_fc.sum()),'Surplus' if bal_fc.sum()>0 else 'Deficit','gold'),
        (c4,"Fcst Coverage",f"{fc_cov:.1f}%","Exports÷Imports",'blue'),
    ]:
        vc = {'green':'#10d9a0','red':'#f43f5e','gold':'#f59e0b','blue':'#60a5fa'}
        col.markdown(f"""<div class="metric-card {color}">
        <div class="metric-label">{lbl}</div>
        <div class="metric-value" style="color:{vc[color]};">{val}</div>
        <div class="metric-sub">{sub}</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # Main forecast chart
    st.markdown('<div class="chart-card"><div class="chart-title">📈 Trade Forecast — Historical + 12-Month Projection</div>', unsafe_allow_html=True)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=hist_x, y=ms['DOLLARS_imp']/1e3, mode='lines',
        name='Historical Imports', line=dict(color='#f43f5e',width=2),
        customdata=ms['date'].dt.strftime('%b %Y'),
        hovertemplate='<b>%{customdata}</b> Imports: $%{y:.0f}M<extra></extra>'))
    fig.add_trace(go.Scatter(x=hist_x, y=ms['DOLLARS_exp']/1e3, mode='lines',
        name='Historical Exports', line=dict(color='#10d9a0',width=2),
        customdata=ms['date'].dt.strftime('%b %Y'),
        hovertemplate='<b>%{customdata}</b> Exports: $%{y:.0f}M<extra></extra>'))
    fig.add_trace(go.Scatter(x=future_x, y=imp_fc/1e3, mode='lines+markers',
        name='Forecast Imports', line=dict(color='#f43f5e',width=2.5,dash='dot'),
        marker=dict(size=7,symbol='diamond'), customdata=future_labels,
        hovertemplate='<b>%{customdata}</b> Fcst Imp: $%{y:.0f}M<extra></extra>'))
    fig.add_trace(go.Scatter(x=future_x, y=exp_fc/1e3, mode='lines+markers',
        name='Forecast Exports', line=dict(color='#10d9a0',width=2.5,dash='dot'),
        marker=dict(size=7,symbol='diamond'), customdata=future_labels,
        hovertemplate='<b>%{customdata}</b> Fcst Exp: $%{y:.0f}M<extra></extra>'))
    divx = len(ms) - 0.5
    fig.add_vline(x=divx, line=dict(color='rgba(255,255,255,0.25)',dash='dash',width=1.5),
        annotation_text='← History | Forecast →', annotation_font=dict(color='#64748b',size=10))
    fig.add_vrect(x0=divx, x1=len(ms)+12, fillcolor='rgba(255,255,255,0.01)', line_width=0)

    step = max(1, len(ms)//14)
    tv = list(range(0,len(ms)+12,step))
    all_labels = [ms.iloc[i]['date'].strftime('%b %Y') if i < len(ms) else future_labels[i-len(ms)] for i in tv if i<len(ms)+12]
    tv = tv[:len(all_labels)]
    fig.update_layout(**pl(380,
        xaxis=dict(tickvals=tv, ticktext=all_labels, tickangle=-30, tickfont=dict(size=10)),
        yaxis=dict(title='USD Millions'),
        legend=dict(orientation='h',y=1.05,bgcolor='rgba(0,0,0,0)',font=dict(color='#64748b'))))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="chart-card"><div class="chart-title">⚖️ Forecasted Monthly Balance</div>', unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_hline(y=0, line=dict(color='rgba(255,255,255,0.15)',width=1))
        fig2.add_trace(go.Bar(x=future_labels, y=bal_fc/1e3,
            marker_color=['#10d9a0' if x>=0 else '#f43f5e' for x in bal_fc],
            text=[f"${v:.0f}M" for v in bal_fc/1e3], textposition='outside',
            textfont=dict(color='#64748b',size=10),
            hovertemplate='<b>%{x}</b>: $%{y:.0f}M<extra></extra>'))
        fig2.update_layout(**pl(300, xaxis=dict(tickangle=-30), yaxis=dict(title='USD Millions'), showlegend=False))
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card"><div class="chart-title">🎯 All Scenarios — 12M Comparison</div>', unsafe_allow_html=True)
        sc_rows = {}
        for sc_name, (spe,spi) in presets.items():
            e = exp_fc_base*(1+spe/100); i = imp_fc_base*(1+spi/100)
            sc_rows[sc_name] = {'exp':e.sum(),'imp':i.sum(),'bal':(e-i).sum()}
        sc_df = pd.DataFrame(sc_rows).T
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name='Exports', x=sc_df.index, y=sc_df['exp']/1e6,
            marker_color='#10d9a0', hovertemplate='<b>%{x}</b> Exports: $%{y:.1f}B<extra></extra>'))
        fig3.add_trace(go.Bar(name='Imports', x=sc_df.index, y=sc_df['imp']/1e6,
            marker_color='#f43f5e', hovertemplate='<b>%{x}</b> Imports: $%{y:.1f}B<extra></extra>'))
        fig3.update_layout(**pl(300, yaxis=dict(title='USD Billions'), barmode='group',
            xaxis=dict(tickangle=-20, tickfont=dict(size=9)),
            legend=dict(orientation='h',y=1.05,bgcolor='rgba(0,0,0,0)',font=dict(color='#64748b'))))
        st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    # Export target tool
    st.markdown('<div class="section-header">🎯 Export Target Analysis</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([1,2])
    with col1:
        best_ann_exp = ann['exports'].max()
        default_target = round(best_ann_exp/1e6*1.15, 0)  # 15% above best year
        target = st.number_input("Annual Export Target (USD Billions)", min_value=5.0, max_value=300.0,
            value=float(default_target), step=1.0)
        target_th = target*1e6
        gap = target_th - best_ann_exp
        st.markdown(f"""<div class="insight-box">
        <strong style="color:#10d9a0;">📊 Target Gap</strong><br>
        Target: <strong>{fmt_usd(target_th)}/year</strong><br>
        Best historical: <strong>{fmt_usd(best_ann_exp)}</strong><br>
        Gap: <strong>{fmt_usd(abs(gap))}</strong> {'above best ✅' if gap<0 else 'still needed'}<br>
        Monthly needed: <strong>{fmt_usd(abs(gap)/12)}</strong>/month
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card"><div class="chart-title">🎯 Historical Annual Exports vs Target</div>', unsafe_allow_html=True)
        fig4 = go.Figure()
        fig4.add_hline(y=target, line=dict(color='#f59e0b',dash='dash',width=2),
            annotation_text=f'Target: ${target}B', annotation_font=dict(color='#f59e0b',size=11))
        fig4.add_trace(go.Bar(x=ann['YEAR'], y=ann['exports']/1e6,
            marker_color=['#10d9a0' if v/1e6>=target else '#f43f5e' for v in ann['exports']],
            text=[fmt_usd(v) for v in ann['exports']], textposition='outside',
            textfont=dict(color='#64748b',size=11),
            hovertemplate='<b>%{x}</b>: $%{y:.2f}B<extra></extra>'))
        fig4.update_layout(**pl(280, yaxis=dict(title='USD Billions'), showlegend=False))
        st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    # Forecast table
    st.markdown('<div class="chart-card"><div class="chart-title">📋 12-Month Forecast Data Table</div>', unsafe_allow_html=True)
    fc_table = pd.DataFrame({
        'Period':           future_labels,
        'Fcst Exports (M)': (exp_fc/1e3).round(1),
        'Fcst Imports (M)': (imp_fc/1e3).round(1),
        'Fcst Balance (M)': (bal_fc/1e3).round(1),
        'Coverage (%)':     (exp_fc/np.maximum(imp_fc,1)*100).round(1)
    })
    st.dataframe(fc_table.set_index('Period'), use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
