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
        <div class="section-badge">Product Intelligence</div>
        <div class="page-title">🔬 Commodity Deep Dive</div>
        <div class="page-subtitle">Product-level analytics · Price discovery · Market share evolution · {data_period}</div>
    </div></div>""", unsafe_allow_html=True)

    exp, imp = load_data()
    ann = get_annual_totals()
    years = sorted(ann['YEAR'].unique(), reverse=True)

    tab1, tab2, tab3 = st.tabs(["📤 Export Products", "📥 Import Products", "🔄 Trade Composition"])

    # ══════════════════════════════════════════════
    with tab1:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            yr = st.selectbox("Year", years, key='prod_exp_yr')
        with col_f2:
            cat_list = ['All'] + sorted(exp['CATEGORY'].dropna().unique().tolist())
            cat = st.selectbox("Category", cat_list, key='prod_exp_cat')

        df = exp[exp['YEAR']==yr].copy()
        if cat != 'All':
            df = df[df['CATEGORY']==cat]
        dp = df.groupby(['CATEGORY','PRODUCT'])['DOLLARS'].sum().reset_index()
        dp = dp[dp['PRODUCT'].notna() & (dp['DOLLARS']>0)]

        st.markdown('<div class="chart-card"><div class="chart-title">🗺️ Export Treemap (Size = USD Value)</div>', unsafe_allow_html=True)
        fig = px.treemap(dp, path=[px.Constant('Pakistan Exports'),'CATEGORY','PRODUCT'],
            values='DOLLARS', color='DOLLARS',
            color_continuous_scale=[[0,'#003d2d'],[0.4,'#006b4f'],[0.7,'#00a870'],[1,'#10d9a0']])
        fig.update_traces(textfont=dict(color='#e2e8f0',family='Plus Jakarta Sans',size=12),
            hovertemplate='<b>%{label}</b><br>$%{value:,.0f}K<extra></extra>')
        fig.update_layout(**pl(420, margin=dict(l=5,r=5,t=30,b=5)))
        fig.update_coloraxes(showscale=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="chart-card"><div class="chart-title">📈 Top Export Products — {data_period} Total</div>', unsafe_allow_html=True)
            top15 = exp.groupby('PRODUCT')['DOLLARS'].sum().nlargest(15).reset_index().sort_values('DOLLARS')
            fig2 = go.Figure(go.Bar(
                x=top15['DOLLARS']/1e6, y=top15['PRODUCT'], orientation='h',
                marker=dict(color=top15['DOLLARS'], colorscale='Greens', showscale=False),
                text=[fmt_usd(v) for v in top15['DOLLARS']], textposition='outside',
                textfont=dict(color='#64748b',size=10),
                hovertemplate='<b>%{y}</b>: $%{x:.0f}M<extra></extra>'))
            fig2.update_layout(**pl(380, xaxis=dict(title=f'USD Millions ({min_yr}–{max_yr} Total)'),
                margin=dict(l=5,r=80,t=10,b=10), showlegend=False))
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar':False})
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="chart-card"><div class="chart-title">📊 Top Product Share Evolution (% of total exports)</div>', unsafe_allow_html=True)
            top6 = exp.groupby('PRODUCT')['DOLLARS'].sum().nlargest(6).index
            df6  = exp[exp['PRODUCT'].isin(top6)].groupby(['YEAR','PRODUCT'])['DOLLARS'].sum().reset_index()
            tot  = exp.groupby('YEAR')['DOLLARS'].sum().reset_index().rename(columns={'DOLLARS':'total'})
            df6  = df6.merge(tot, on='YEAR')
            df6['share'] = df6['DOLLARS']/df6['total']*100
            pal  = ['#10d9a0','#60a5fa','#f59e0b','#a78bfa','#fb923c','#f472b6']
            fig3 = go.Figure()
            for i,prod in enumerate(top6):
                d = df6[df6['PRODUCT']==prod].sort_values('YEAR')
                fig3.add_trace(go.Scatter(x=d['YEAR'], y=d['share'], mode='lines+markers+text',
                    name=prod[:20], line=dict(color=pal[i],width=2), marker=dict(size=7),
                    text=[f"{v:.1f}%" for v in d['share']], textposition='top center',
                    textfont=dict(size=9),
                    hovertemplate=f'<b>{prod[:20]}</b> %{{x}}: %{{y:.1f}}%<extra></extra>'))
            fig3.update_layout(**pl(380, yaxis=dict(title='% Share'),
                legend=dict(orientation='h',y=-0.28,bgcolor='rgba(0,0,0,0)',font=dict(color='#64748b',size=9))))
            st.plotly_chart(fig3, use_container_width=True, config={'displayModeBar':False})
            st.markdown('</div>', unsafe_allow_html=True)

        # Unit value analysis
        st.markdown('<div class="chart-card"><div class="chart-title">💰 Unit Value Trend — Price per MT (Top Products with Quantity Data)</div>', unsafe_allow_html=True)
        uv = exp[(exp['QUANTITY'].notna()) & (exp['QUANTITY']>0)].groupby(['YEAR','PRODUCT']).agg(
            dollars=('DOLLARS','sum'), qty=('QUANTITY','sum')).reset_index()
        uv['unit_val'] = uv['dollars']/uv['qty']
        top_uv = uv.groupby('PRODUCT')['dollars'].sum().nlargest(8).index
        fig4 = go.Figure()
        pal2 = ['#10d9a0','#60a5fa','#f59e0b','#a78bfa','#fb923c','#f472b6','#2dd4bf','#e879f9']
        for i,prod in enumerate(top_uv):
            d = uv[uv['PRODUCT']==prod].sort_values('YEAR')
            fig4.add_trace(go.Scatter(x=d['YEAR'], y=d['unit_val']*1000,
                mode='lines+markers', name=prod[:20], line=dict(color=pal2[i],width=2), marker=dict(size=8),
                hovertemplate=f'<b>{prod[:20]}</b> %{{x}}: $%{{y:,.0f}}/MT<extra></extra>'))
        fig4.update_layout(**pl(300, yaxis=dict(title='USD per Metric Ton'),
            legend=dict(orientation='h',y=-0.3,bgcolor='rgba(0,0,0,0)',font=dict(color='#64748b',size=9))))
        st.plotly_chart(fig4, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════
    with tab2:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            yr2 = st.selectbox("Year", years, key='prod_imp_yr')
        with col_f2:
            cat_list2 = ['All'] + sorted(imp['CATEGORY'].dropna().unique().tolist())
            cat2 = st.selectbox("Category", cat_list2, key='prod_imp_cat')

        df2 = imp[imp['YEAR']==yr2].copy()
        if cat2 != 'All':
            df2 = df2[df2['CATEGORY']==cat2]
        dp2 = df2.groupby(['CATEGORY','PRODUCT'])['DOLLARS'].sum().reset_index()
        dp2 = dp2[dp2['PRODUCT'].notna() & (dp2['DOLLARS']>0)]

        st.markdown('<div class="chart-card"><div class="chart-title">🗺️ Import Treemap (Size = USD Value)</div>', unsafe_allow_html=True)
        fig5 = px.treemap(dp2, path=[px.Constant('Pakistan Imports'),'CATEGORY','PRODUCT'],
            values='DOLLARS', color='DOLLARS',
            color_continuous_scale=[[0,'#3d0016'],[0.4,'#7d1a2d'],[0.7,'#cc3352'],[1,'#f43f5e']])
        fig5.update_traces(textfont=dict(color='#e2e8f0',family='Plus Jakarta Sans',size=12),
            hovertemplate='<b>%{label}</b><br>$%{value:,.0f}K<extra></extra>')
        fig5.update_layout(**pl(400, margin=dict(l=5,r=5,t=30,b=5)))
        fig5.update_coloraxes(showscale=False)
        st.plotly_chart(fig5, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f'<div class="chart-card"><div class="chart-title">📈 Top Import Products — {data_period} Total</div>', unsafe_allow_html=True)
            top15i = imp.groupby('PRODUCT')['DOLLARS'].sum().nlargest(15).reset_index().sort_values('DOLLARS')
            fig6 = go.Figure(go.Bar(
                x=top15i['DOLLARS']/1e6, y=top15i['PRODUCT'], orientation='h',
                marker=dict(color=top15i['DOLLARS'], colorscale=[[0,'#3d0016'],[1,'#f43f5e']], showscale=False),
                text=[fmt_usd(v) for v in top15i['DOLLARS']], textposition='outside',
                textfont=dict(color='#64748b',size=10),
                hovertemplate='<b>%{y}</b>: $%{x:.0f}M<extra></extra>'))
            fig6.update_layout(**pl(380, xaxis=dict(title='USD Millions (Total)'),
                margin=dict(l=5,r=80,t=10,b=10), showlegend=False))
            st.plotly_chart(fig6, use_container_width=True, config={'displayModeBar':False})
            st.markdown('</div>', unsafe_allow_html=True)

        with col2:
            st.markdown('<div class="chart-card"><div class="chart-title">📊 Top Import Share Evolution</div>', unsafe_allow_html=True)
            top6i = imp.groupby('PRODUCT')['DOLLARS'].sum().nlargest(6).index
            df6i  = imp[imp['PRODUCT'].isin(top6i)].groupby(['YEAR','PRODUCT'])['DOLLARS'].sum().reset_index()
            toti  = imp.groupby('YEAR')['DOLLARS'].sum().reset_index().rename(columns={'DOLLARS':'total'})
            df6i  = df6i.merge(toti, on='YEAR')
            df6i['share'] = df6i['DOLLARS']/df6i['total']*100
            pal3 = ['#f43f5e','#fb923c','#f59e0b','#60a5fa','#a78bfa','#2dd4bf']
            fig7 = go.Figure()
            for i,prod in enumerate(top6i):
                d = df6i[df6i['PRODUCT']==prod].sort_values('YEAR')
                fig7.add_trace(go.Scatter(x=d['YEAR'], y=d['share'], mode='lines+markers+text',
                    name=prod.strip()[:20], line=dict(color=pal3[i],width=2), marker=dict(size=7),
                    text=[f"{v:.1f}%" for v in d['share']], textposition='top center',
                    textfont=dict(size=9),
                    hovertemplate=f'<b>{prod.strip()[:20]}</b> %{{x}}: %{{y:.1f}}%<extra></extra>'))
            fig7.update_layout(**pl(380, yaxis=dict(title='% Share'),
                legend=dict(orientation='h',y=-0.28,bgcolor='rgba(0,0,0,0)',font=dict(color='#64748b',size=9))))
            st.plotly_chart(fig7, use_container_width=True, config={'displayModeBar':False})
            st.markdown('</div>', unsafe_allow_html=True)

    # ══════════════════════════════════════════════
    with tab3:
        latest_yr = ann['YEAR'].max()
        st.markdown(f'<div class="chart-card"><div class="chart-title">📊 Export vs Import Category Comparison — {latest_yr}</div>', unsafe_allow_html=True)
        e_c = exp[exp['YEAR']==latest_yr].groupby('CATEGORY')['DOLLARS'].sum().reset_index()
        i_c = imp[imp['YEAR']==latest_yr].groupby('CATEGORY')['DOLLARS'].sum().reset_index()
        fig8 = go.Figure()
        fig8.add_trace(go.Bar(name='Exports', x=e_c['CATEGORY'], y=e_c['DOLLARS']/1e3,
            marker_color='#10d9a0', hovertemplate='<b>%{x}</b> Exports: $%{y:.0f}M<extra></extra>'))
        fig8.add_trace(go.Bar(name='Imports', x=i_c['CATEGORY'], y=i_c['DOLLARS']/1e3,
            marker_color='#f43f5e', hovertemplate='<b>%{x}</b> Imports: $%{y:.0f}M<extra></extra>'))
        fig8.update_layout(**pl(380, yaxis=dict(title='USD Millions'), barmode='group',
            xaxis=dict(tickangle=-25, tickfont=dict(size=9)),
            legend=dict(orientation='h',y=1.05,bgcolor='rgba(0,0,0,0)',font=dict(color='#64748b'))))
        st.plotly_chart(fig8, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)

        # Quantity trend
        st.markdown('<div class="chart-card"><div class="chart-title">📦 Quantity Trend — Top Export Products (Million MT)</div>', unsafe_allow_html=True)
        top_qty = exp[(exp['QUANTITY'].notna()) & (exp['QUANTITY']>0)].groupby('PRODUCT')['QUANTITY'].sum().nlargest(10).index
        qty_df  = exp[exp['PRODUCT'].isin(top_qty)].groupby(['YEAR','PRODUCT'])['QUANTITY'].sum().reset_index()
        pal4 = ['#10d9a0','#60a5fa','#f59e0b','#a78bfa','#fb923c','#f472b6','#2dd4bf','#e879f9','#84cc16','#f59e0b']
        fig9 = go.Figure()
        for i,prod in enumerate(top_qty):
            d = qty_df[qty_df['PRODUCT']==prod].sort_values('YEAR')
            fig9.add_trace(go.Bar(x=d['YEAR'], y=d['QUANTITY']/1e6, name=prod[:20],
                marker_color=pal4[i%len(pal4)],
                hovertemplate=f'<b>{prod[:20]}</b> %{{x}}: %{{y:.2f}}M MT<extra></extra>'))
        fig9.update_layout(**pl(320, yaxis=dict(title='Million MT'), barmode='group',
            legend=dict(orientation='h',y=-0.3,bgcolor='rgba(0,0,0,0)',font=dict(color='#64748b',size=9))))
        st.plotly_chart(fig9, use_container_width=True, config={'displayModeBar':False})
        st.markdown('</div>', unsafe_allow_html=True)
