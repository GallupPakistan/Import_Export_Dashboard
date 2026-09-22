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
    <div class="page-header"><div>
        <div class="section-badge">Balance of Trade</div>
        <div class="page-title">⚖️ Trade Balance Intelligence</div>
        <div class="page-subtitle">Deficit analysis, structural gaps & direction of trade flows · {data_period}</div>
    </div></div>""", unsafe_allow_html=True)

    exp, imp = load_data()
    ann      = get_annual_totals()
    monthly  = get_monthly_totals()

    if 'date' not in monthly.columns:
        monthly = monthly.sort_values(['YEAR','Month_Num']).reset_index(drop=True)
        monthly['date'] = pd.to_datetime(
            monthly['YEAR'].astype(str)+'-'+monthly['Month_Num'].astype(str).str.zfill(2)+'-01')

    total_deficit = ann['balance'].sum()
    worst_yr  = ann.loc[ann['balance'].idxmin()]
    best_yr   = ann.loc[ann['coverage_ratio'].idxmax()]
    months_def= (monthly['balance']<0).sum()

    vc = {'green':'#10d9a0','red':'#f43f5e','gold':'#f59e0b','blue':'#60a5fa'}
    def kpi(col,lbl,val,sub,color='red'):
        col.markdown(f"""<div class="metric-card {color}">
        <div class="metric-label">{lbl}</div>
        <div class="metric-value" style="color:{vc.get(color,'#e2e8f0')};">{val}</div>
        <div class="metric-sub">{sub}</div></div>""", unsafe_allow_html=True)

    c1,c2,c3,c4 = st.columns(4)
    kpi(c1,"Cumulative Deficit",fmt_usd(abs(total_deficit)),f"{data_period} Total",'red')
    kpi(c2,"Worst Deficit Year",str(int(worst_yr['YEAR'])),fmt_usd(abs(worst_yr['balance']))+" deficit",'red')
    kpi(c3,"Best Coverage Year",str(int(best_yr['YEAR'])),f"{best_yr['coverage_ratio']}% export coverage",'green')
    kpi(c4,"Months in Deficit",f"{months_def}/{len(monthly)}","Out of all months",'gold')
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # ── Annual decomposition ────────────────────────────────────────────────
    col1, col2 = st.columns([2,1])
    with col1:
        st.markdown('<div class="chart-card"><div class="chart-title">📊 Annual Trade Balance Decomposition (USD Billions)</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=ann['YEAR'], y=ann['exports']/1e6, name='Exports', marker_color='#10d9a0', opacity=0.9,
            hovertemplate='<b>Exports %{x}</b>: $%{y:.2f}B<extra></extra>'))
        fig.add_trace(go.Bar(x=ann['YEAR'], y=-ann['imports']/1e6, name='Imports', marker_color='#f43f5e', opacity=0.9,
            hovertemplate='<b>Imports %{x}</b>: $%{y:.2f}B<extra></extra>'))
        fig.add_trace(go.Scatter(x=ann['YEAR'], y=ann['balance']/1e6,
            mode='lines+markers+text', name='Balance',
            line=dict(color='#f59e0b',width=2.5,dash='dot'), marker=dict(size=10,color='#f59e0b'),
            text=[fmt_usd(v) for v in ann['balance']],
            textposition='top center', textfont=dict(color='#f59e0b',size=10),
            hovertemplate='<b>Balance %{x}</b>: $%{y:.2f}B<extra></extra>'))
        fig.update_layout(**pl(340, yaxis=dict(title='USD Billions'), barmode='relative',
            legend=dict(orientation='h',y=1.05,bgcolor='rgba(0,0,0,0)',font=dict(color='#64748b'))))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card"><div class="chart-title">📐 Coverage Ratio Trend</div>', unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_hrect(y0=0, y1=50, fillcolor='rgba(244,63,94,0.04)', line_width=0)
        fig2.add_hrect(y0=50, y1=75, fillcolor='rgba(245,158,11,0.04)', line_width=0)
        fig2.add_hline(y=100, line=dict(color='rgba(16,217,160,0.3)',dash='dot',width=1.5),
            annotation_text='100% balanced', annotation_font=dict(color='#10d9a0',size=9))
        fig2.add_trace(go.Scatter(x=ann['YEAR'], y=ann['coverage_ratio'],
            mode='lines+markers+text', fill='tozeroy', fillcolor='rgba(96,165,250,0.07)',
            line=dict(color='#60a5fa',width=3), marker=dict(size=12,color='#60a5fa'),
            text=[f"{v}%" for v in ann['coverage_ratio']],
            textposition='top center', textfont=dict(color='#60a5fa',size=11),
            hovertemplate='<b>%{x}</b>: %{y}% coverage<extra></extra>'))
        ymax = max(ann['coverage_ratio'].max()+20, 110)
        fig2.update_layout(**pl(340, yaxis=dict(title='%',range=[0,ymax]), showlegend=False))
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Cumulative monthly balance ──────────────────────────────────────────
    st.markdown('<div class="chart-card"><div class="chart-title">📈 Monthly Trade Balance + Cumulative Track</div>', unsafe_allow_html=True)
    ms = monthly.sort_values('date').copy().reset_index(drop=True)
    ms['cumulative'] = ms['balance'].cumsum()
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=ms['date'], y=ms['balance']/1e3,
        marker_color=['#10d9a0' if x>=0 else '#f43f5e' for x in ms['balance']],
        name='Monthly Balance', opacity=0.8,
        hovertemplate='<b>%{x|%b %Y}</b>: $%{y:.0f}M<extra></extra>'))
    fig3.add_trace(go.Scatter(
        x=ms['date'], y=ms['cumulative']/1e3,
        mode='lines', name='Cumulative', line=dict(color='#f59e0b',width=2.5), yaxis='y2',
        hovertemplate='<b>Cumulative %{x|%b %Y}</b>: $%{y:.0f}M<extra></extra>'))
    fig3.update_layout(**pl(320,
        xaxis=dict(tickformat='%b %Y', dtick='M6', tickangle=-30),
        yaxis=dict(title='Monthly Balance (USD M)'),
        yaxis2=dict(title='Cumulative (USD M)', overlaying='y', side='right',
                   gridcolor='rgba(0,0,0,0)', tickfont=dict(color='#f59e0b')),
        legend=dict(orientation='h',y=1.05,bgcolor='rgba(0,0,0,0)',font=dict(color='#64748b'))))
    st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar':False})
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Sectoral + Full table ──────────────────────────────────────────────
    col1, col2 = st.columns([1,2])

    with col1:
        yr_sel = st.selectbox("Year for sector analysis:", sorted(ann['YEAR'].unique(),reverse=True), key='bal_yr')
        e_sec = exp[exp['YEAR']==yr_sel].groupby('CATEGORY')['DOLLARS'].sum()
        i_sec = imp[imp['YEAR']==yr_sel].groupby('CATEGORY')['DOLLARS'].sum()
        sec_df = pd.DataFrame({'exports':e_sec,'imports':i_sec}).fillna(0)
        sec_df['deficit'] = sec_df['exports'] - sec_df['imports']
        sec_df = sec_df.sort_values('deficit')

        st.markdown(f'<div class="chart-card"><div class="chart-title">⚖️ Sectoral Surplus/Deficit — {yr_sel}</div>', unsafe_allow_html=True)
        fig4 = go.Figure(go.Bar(
            x=sec_df['deficit']/1e3,
            y=[c.replace(' GROUP','').replace('AGRICULTURAL AND OTHER CHEMICALS','Agri Chem') for c in sec_df.index],
            orientation='h',
            marker_color=['#f43f5e' if v<0 else '#10d9a0' for v in sec_df['deficit']],
            text=[fmt_usd(v) for v in sec_df['deficit']],
            textposition='outside', textfont=dict(color='#64748b',size=9),
            hovertemplate='<b>%{y}</b>: $%{x:.0f}M<extra></extra>'
        ))
        fig4.add_vline(x=0, line=dict(color='rgba(255,255,255,0.15)',width=1))
        fig4.update_layout(**pl(370, xaxis=dict(title='USD Millions'), margin=dict(l=5,r=80,t=20,b=10), showlegend=False))
        st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card"><div class="chart-title">📋 Full Trade Balance Summary — All Years</div>', unsafe_allow_html=True)
        summary = ann.copy()
        summary['YEAR']     = summary['YEAR'].astype(int)
        summary['Exports']  = summary['exports'].apply(fmt_usd)
        summary['Imports']  = summary['imports'].apply(fmt_usd)
        summary['Balance']  = summary['balance'].apply(fmt_usd)
        summary['Coverage'] = summary['coverage_ratio'].apply(lambda x: f"{x}%")
        summary['Volume']   = summary['trade_volume'].apply(fmt_usd)
        st.dataframe(summary[['YEAR','Exports','Imports','Balance','Coverage','Volume']].set_index('YEAR'),
                    use_container_width=True)

        st.markdown('<div class="chart-title" style="margin-top:1rem;">📅 Monthly Balance Pivot (USD Millions)</div>', unsafe_allow_html=True)
        m_piv = monthly.copy()
        m_piv['bm'] = (m_piv['balance']/1e3).round(1)
        pt = m_piv.pivot_table(index='YEAR', columns='MONTH', values='bm')
        pt = pt.reindex(columns=[m for m in MONTH_ORDER if m in pt.columns])
        st.dataframe(pt.style.background_gradient(cmap='RdYlGn', axis=None), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
