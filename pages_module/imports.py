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
        <div class="section-badge">Import Analysis</div>
        <div class="page-title">🛒 Pakistan Imports Deep Dive</div>
        <div class="page-subtitle">Commodity-level import intelligence · {data_period}</div>
    </div></div>""", unsafe_allow_html=True)

    _, imp = load_data()
    ann    = get_annual_totals()
    monthly= get_monthly_totals()
    years  = sorted(ann['YEAR'].unique(), reverse=True)

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        year_sel = st.selectbox("Focus Year", years, key='imp_year')
    with col_f2:
        compare_year = st.selectbox("Compare Against", [y for y in years if y!=year_sel], key='imp_compare')

    imp_y  = imp[imp['YEAR']==year_sel]
    imp_py = imp[imp['YEAR']==compare_year]
    tot_y  = imp_y['DOLLARS'].sum()
    tot_py = imp_py['DOLLARS'].sum()
    yoy    = (tot_y-tot_py)/tot_py*100 if tot_py>0 else 0
    petrol = imp_y[imp_y['CATEGORY']=='PETROLEUM GROUP']['DOLLARS'].sum()/tot_y*100 if tot_y>0 else 0
    mach   = imp_y[imp_y['CATEGORY']=='MACHINERY GROUP']['DOLLARS'].sum()/tot_y*100  if tot_y>0 else 0

    vc = {'green':'#10d9a0','red':'#f43f5e','gold':'#f59e0b','blue':'#60a5fa','purple':'#a78bfa'}
    def kpi(col,lbl,val,sub,delta=None,color='red'):
        dhtml=""
        if delta is not None:
            cls="delta-pos" if delta>=0 else "delta-neg"
            dhtml=f'<div class="metric-delta {cls}">{"▲" if delta>=0 else "▼"} {abs(delta):.1f}%</div>'
        col.markdown(f"""<div class="metric-card {color}">
        <div class="metric-label">{lbl}</div>
        <div class="metric-value" style="color:{vc.get(color,'#e2e8f0')};">{val}</div>
        <div class="metric-sub">{sub}</div>{dhtml}</div>""", unsafe_allow_html=True)

    c1,c2,c3,c4,c5 = st.columns(5)
    kpi(c1,"Import Value",fmt_usd(tot_y),f"vs {fmt_usd(tot_py)} in {compare_year}",yoy,'red')
    kpi(c2,"YoY Change",f"{yoy:+.1f}%",f"{year_sel} vs {compare_year}",None,'red' if yoy>=0 else 'green')
    kpi(c3,"Energy Share",f"{petrol:.1f}%","Petroleum group",None,'gold')
    kpi(c4,"Machinery Share",f"{mach:.1f}%","Machinery group",None,'blue')
    top_imp = imp_y.groupby('PRODUCT')['DOLLARS'].sum().idxmax() if len(imp_y)>0 else 'N/A'
    kpi(c5,"Top Import",str(top_imp)[:18]+("…" if len(str(top_imp))>18 else ""),"By USD value",None,'purple')
    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    imp_cat = get_category_annual('import')
    col1, col2 = st.columns([3,2])

    with col1:
        st.markdown('<div class="chart-card"><div class="chart-title">📊 Import Category Trends (Annual, USD Billions)</div>', unsafe_allow_html=True)
        ic = imp_cat.groupby(['YEAR','CATEGORY'])['DOLLARS'].sum().reset_index()
        fig = go.Figure()
        for cat in sorted(ic['CATEGORY'].unique()):
            d = ic[ic['CATEGORY']==cat].sort_values('YEAR')
            c = CATEGORY_COLORS_IMP.get(cat,'#64748b')
            lbl = cat.replace(' GROUP','').replace('AGRICULTURAL AND OTHER CHEMICALS','Agri Chem').title()
            fig.add_trace(go.Scatter(x=d['YEAR'], y=d['DOLLARS']/1e6,
                name=lbl, mode='lines+markers',
                line=dict(color=c,width=2.5), marker=dict(size=8,color=c),
                hovertemplate=f'<b>{cat}</b> %{{x}}: $%{{y:.2f}}B<extra></extra>'))
        fig.update_layout(**pl(300, yaxis=dict(title='USD Billions'),
            legend=dict(orientation='h',y=-0.35,bgcolor='rgba(0,0,0,0)',font=dict(color='#64748b',size=9))))
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div class="chart-card"><div class="chart-title">📅 Monthly Imports — {year_sel} vs {compare_year}</div>', unsafe_allow_html=True)
        mon_y  = imp[imp['YEAR']==year_sel].groupby('MONTH')['DOLLARS'].sum().reset_index()
        mon_py = imp[imp['YEAR']==compare_year].groupby('MONTH')['DOLLARS'].sum().reset_index()
        for df in [mon_y,mon_py]:
            df['MC'] = pd.Categorical(df['MONTH'],categories=MONTH_ORDER,ordered=True)
            df.sort_values('MC',inplace=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=mon_py['MONTH'].str[:3], y=mon_py['DOLLARS']/1e3,
            name=str(compare_year), marker_color='rgba(255,255,255,0.1)',
            hovertemplate=f'<b>%{{x}} {compare_year}</b>: $%{{y:.0f}}M<extra></extra>'))
        fig2.add_trace(go.Bar(x=mon_y['MONTH'].str[:3], y=mon_y['DOLLARS']/1e3,
            name=str(year_sel), marker_color='#f43f5e',
            hovertemplate=f'<b>%{{x}} {year_sel}</b>: $%{{y:.0f}}M<extra></extra>'))
        fig2.update_layout(**pl(300, yaxis=dict(title='USD Millions'), barmode='group',
            legend=dict(orientation='h',y=1.05,bgcolor='rgba(0,0,0,0)',font=dict(color='#64748b'))))
        st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="chart-card"><div class="chart-title">🏆 Top 15 Import Products — {year_sel}</div>', unsafe_allow_html=True)
        tp = imp[imp['YEAR']==year_sel].groupby('PRODUCT')['DOLLARS'].sum().reset_index()
        tp = tp[tp['PRODUCT'].notna() & (tp['PRODUCT']!='')].nlargest(15,'DOLLARS').sort_values('DOLLARS')
        fig3 = go.Figure(go.Bar(
            x=tp['DOLLARS']/1e3, y=tp['PRODUCT'], orientation='h',
            marker=dict(color=tp['DOLLARS'], colorscale=[[0,'#3d0016'],[0.5,'#cc1147'],[1,'#f43f5e']], showscale=False),
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
        st.markdown(f'<div class="chart-card"><div class="chart-title">📈 Import YoY Change — {year_sel} vs {compare_year}</div>', unsafe_allow_html=True)
        p_y   = imp[imp['YEAR']==year_sel].groupby('PRODUCT')['DOLLARS'].sum()
        p_py  = imp[imp['YEAR']==compare_year].groupby('PRODUCT')['DOLLARS'].sum()
        gdf   = pd.DataFrame({'cur':p_y,'prev':p_py}).dropna()
        gdf   = gdf[(gdf['prev']>0) & (gdf['cur']>50000)]
        gdf['growth'] = (gdf['cur']-gdf['prev'])/gdf['prev']*100
        gdf   = pd.concat([gdf.nsmallest(10,'growth'), gdf.nlargest(10,'growth')]).drop_duplicates()
        fig4  = go.Figure(go.Bar(
            x=gdf['growth'], y=gdf.index, orientation='h',
            marker_color=['#f43f5e' if x>=0 else '#10d9a0' for x in gdf['growth']],
            text=[f"{v:+.1f}%" for v in gdf['growth']], textposition='outside',
            textfont=dict(color='#64748b',size=10),
            hovertemplate='<b>%{y}</b>: %{x:+.1f}%<extra></extra>'
        ))
        fig4.add_vline(x=0, line=dict(color='rgba(255,255,255,0.15)',width=1))
        fig4.update_layout(**pl(420,
            xaxis=dict(title='YoY Change (%)'),
            yaxis=dict(tickfont=dict(size=10)),
            margin=dict(l=5,r=70,t=20,b=10), showlegend=False))
        st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Energy focus ───────────────────────────────────────────────────────
    st.markdown('<div class="section-header">⛽ Energy Imports Focus</div>', unsafe_allow_html=True)
    col1, col2 = st.columns([2,1])
    energy = imp[imp['CATEGORY']=='PETROLEUM GROUP'].groupby(['YEAR','PRODUCT'])['DOLLARS'].sum().reset_index()
    top_e  = energy.groupby('PRODUCT')['DOLLARS'].sum().nlargest(5).index

    with col1:
        st.markdown('<div class="chart-card"><div class="chart-title">⛽ Energy Import by Product (Annual, USD Millions)</div>', unsafe_allow_html=True)
        e_df = energy[energy['PRODUCT'].isin(top_e)]
        fig5 = go.Figure()
        ec = ['#f43f5e','#fb923c','#f59e0b','#f472b6','#a78bfa']
        for i,prod in enumerate(top_e):
            d = e_df[e_df['PRODUCT']==prod].sort_values('YEAR')
            fig5.add_trace(go.Bar(x=d['YEAR'], y=d['DOLLARS']/1e3, name=prod.strip(),
                marker_color=ec[i%len(ec)],
                hovertemplate=f'<b>{prod.strip()}</b> %{{x}}: $%{{y:.0f}}M<extra></extra>'))
        fig5.update_layout(**pl(300, yaxis=dict(title='USD Millions'), barmode='stack',
            legend=dict(orientation='h',y=-0.3,bgcolor='rgba(0,0,0,0)',font=dict(color='#64748b',size=9))))
        st.plotly_chart(fig5, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card"><div class="chart-title">⛽ Energy % of Total Imports</div>', unsafe_allow_html=True)
        e_share = imp.groupby('YEAR').apply(
            lambda x: x[x['CATEGORY']=='PETROLEUM GROUP']['DOLLARS'].sum() / x['DOLLARS'].sum() * 100
            if x['DOLLARS'].sum()>0 else 0
        ).reset_index(name='share')
        fig6 = go.Figure(go.Bar(
            x=e_share['YEAR'], y=e_share['share'],
            marker=dict(color=e_share['share'], colorscale=[[0,'#3d0016'],[1,'#f43f5e']], showscale=False),
            text=[f"{v:.1f}%" for v in e_share['share']], textposition='outside',
            textfont=dict(color='#64748b',size=11),
            hovertemplate='<b>%{x}</b>: %{y:.1f}%<extra></extra>'
        ))
        fig6.update_layout(**pl(300, yaxis=dict(title='% of Total'), showlegend=False))
        st.plotly_chart(fig6, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Monthly heatmap ────────────────────────────────────────────────────
    st.markdown('<div class="chart-card"><div class="chart-title">🌡️ Monthly Import Heatmap by Year (USD Millions)</div>', unsafe_allow_html=True)
    mon_heat = imp.groupby(['YEAR','MONTH','Month_Num'])['DOLLARS'].sum().reset_index()
    mon_heat['MC'] = pd.Categorical(mon_heat['MONTH'],categories=MONTH_ORDER,ordered=True)
    pvt = mon_heat.pivot_table(index='YEAR', columns='MC', values='DOLLARS').fillna(0)/1e3
    pvt.columns = [str(c)[:3] for c in pvt.columns]
    fig7 = go.Figure(go.Heatmap(
        z=pvt.values, x=list(pvt.columns), y=[str(y) for y in pvt.index],
        colorscale=[[0,'#0d1526'],[0.5,'#7d1a2d'],[1,'#f43f5e']],
        text=[[f"${v:.0f}M" for v in row] for row in pvt.values],
        texttemplate='%{text}', textfont=dict(size=10,color='#e2e8f0'),
        hovertemplate='<b>%{y} %{x}</b>: $%{z:.0f}M<extra></extra>',
        colorbar=dict(tickfont=dict(color='#64748b'),outlinecolor='rgba(0,0,0,0)')
    ))
    fig7.update_layout(**pl(max(200,len(pvt)*38), yaxis=dict(autorange='reversed')))
    st.plotly_chart(fig7, use_container_width=True, config={'displayModeBar':False})
    st.markdown('</div>', unsafe_allow_html=True)
