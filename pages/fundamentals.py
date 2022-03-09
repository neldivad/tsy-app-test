import streamlit as st
import streamlit.components.v1 as components
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode

import pandas as pd 
import numpy as np

import investpy as inv
from yahoo_fin.stock_info import get_income_statement, get_balance_sheet, get_cash_flow

import plotly.express as px
import plotly.graph_objects as go

#-------------------------
# Body
#--------------------------
def fundamentals():
    st.header('Fundamentals')
    with st.sidebar:
        st.write('---')
        st.title('Resources')
        st.markdown('#### Find me on Twitter')
        components.html("""
        <a href="https://twitter.com/just_neldivad" class="twitter-follow-button" data-show-screen-name="true" data-show-count="true">Follow @just_neldivad</a>
        <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
        """, height=30,)
        st.markdown('#### Or join my discord community.')
        components.html("""
        <iframe src="https://discord.com/widget?id=749377367482433677&theme=dark" width="280" height="380" allowtransparency="true" frameborder="0" sandbox="allow-popups allow-popups-to-escape-sandbox allow-same-origin allow-scripts"></iframe>
        """, height=400)

    def get_inc_statement(ticker, yearly= False):
        df = pd.DataFrame( get_income_statement(ticker.upper(), yearly=yearly) ).T
        df = df.rename_axis('date').reset_index()
        df.insert(0,'ticker', ticker.upper())
        return df

    def get_bs(ticker, yearly= False):
        df = pd.DataFrame( get_balance_sheet(ticker.upper(), yearly=yearly) ).T
        df = df.rename_axis('date').reset_index()
        df.insert(0,'ticker', ticker.upper())
        return df

    def get_cf(ticker, yearly= False):
        df = pd.DataFrame( get_cash_flow(ticker.upper(), yearly=yearly) ).T
        df = df.rename_axis('date').reset_index()
        df.insert(0,'ticker', ticker.upper())
        return df

    def fundamental_sheet(tickers, yearly= False):
        inc_statement =[]
        bs = []
        cf = []

        for ticker in tickers:
            inc_statement.append( get_inc_statement(ticker, yearly) )
            bs.append( get_bs(ticker, yearly) )
            cf.append( get_cf(ticker, yearly) )
            
        df = pd.concat(inc_statement, axis=0)
        df2= pd.concat(bs, axis=0)
        df3= pd.concat(cf, axis=0)

        fs = pd.merge(df, df2, on=['ticker', 'date'], how = "right")
        fs2 = pd.merge(fs, df3, on=['ticker', 'date'], how = "right")
        return fs2

    tickers = inv.get_stocks_list(country='united states')

    df = ''
    recession = [
        ["2020-02-01", "2020-04-15"],
        ["2021-11-01", "2022-1-15"],
    ]
    with st.form(key='Select ticker'):
        ticker = st.multiselect('Select stock', tickers, tickers[:3])
        st.markdown('''<small>Recommended number of tickers should not be more than 5</small>''', unsafe_allow_html=True)
        period = st.selectbox('Time period', ['Quarterly', 'Yearly'])
        if st.form_submit_button(label='Return Fundamentals'):
            if period == 'Quarterly':
                try:
                    df= fundamental_sheet(ticker, yearly=False)
                    recession = [["2021-11-01", "2022-1-15"]]
                except:
                    st.error('There is an issue with the selected tickers.')
            if period == 'Yearly':
                try:
                    df= fundamental_sheet(ticker, yearly=True)
                except:
                    st.error('There is an issue with the selected tickers.')
    
    if len(df) != 0:
        df.replace(0, np.nan, inplace=True)
        df['roe'] = round( (df['netIncome_y'] / df['totalStockholderEquity']*100).apply(pd.to_numeric), 2)
        df['netMargin'] = round( (df['netIncome_y'] / df['totalRevenue']*100).apply(pd.to_numeric), 2) 
        df['operatingMargin'] = round( (df['operatingIncome'] / df['totalRevenue']*100).apply(pd.to_numeric), 2) 
        df['revGrowth'] = round( (df['totalRevenue'] / df.groupby('ticker')['totalRevenue'].shift(periods= -1) *100 -100).apply(pd.to_numeric), 2)
        df['rndGrowth'] = round( (df['researchDevelopment'] / df.groupby('ticker')['researchDevelopment'].shift(periods= -1) *100 -100).apply(pd.to_numeric), 2)
        df['revCostGrowth'] = round( (df['costOfRevenue'] / df.groupby('ticker')['costOfRevenue'].shift(periods= -1) *100 -100).apply(pd.to_numeric), 2)
        df['opexGrowth'] = round( (df['totalOperatingExpenses'] / df.groupby('ticker')['totalOperatingExpenses'].shift(periods= -1) *100 -100).apply(pd.to_numeric), 2)

        AgGrid(df)
        make_kpi_chart(df, recession)
        make_line_chart(df, 'revGrowth', recession)
        make_line_chart(df, 'opexGrowth', recession)

#-----------------------------
# Helper functions
#-----------------------------
def make_kpi_chart(df, recession):
    costs = ['rndGrowth', 'revCostGrowth', 'opexGrowth']
    ticks = df['ticker'].unique()
    temp = df[costs]

    colors = px.colors.qualitative.Plotly

    with st.expander(f"Revenue growth against operating expense growth", expanded=True):
        fig = px.line(
            df,
            x= df['date'],
            y= temp.columns.values,
            color= df['ticker'],
            markers= True,
        )

        for (color, tick) in zip(colors, ticks):
            fig.add_trace(go.Bar(
                x= df[ df['ticker']== tick]['date'],
                y= df[ df['ticker']== tick]['revGrowth'],
                opacity=0.3,
                name= tick,
                hovertext= f'Revenue Growth for {tick}',
                marker_color= color,
                visible='legendonly',
            ))

        for date in recession:
            fig.add_vrect(
                x0= date[0], 
                x1= date[1], 
                line_width=0, 
                fillcolor="green", 
                opacity=0.1
            )
        fig.add_hline(
            y= 0,
            line_dash= 'dot',
            )

        fig.update_yaxes(title_text=f'<b>Growth rate (%)<b>')
        fig.update_xaxes(title_text='')

        st.plotly_chart(fig)
        st.markdown('> *Shaded region = recession*')


def make_line_chart(df, ydata, recession):
    with st.expander(f"Line Chart for {ydata}", expanded=False):
        fig = px.line(
            df,
            x= 'date',
            y= ydata,
            color= 'ticker',
            markers= True,
        )

        for date in recession:
            fig.add_vrect(
                x0= date[0], 
                x1= date[1], 
                line_width=0, 
                fillcolor="green", 
                opacity=0.1
            )
        fig.add_hline(
            y= 0,
            line_dash= 'dot',
            )

        fig.update_yaxes(title_text=f'{ydata}')
        fig.update_xaxes(title_text='')
        st.plotly_chart(fig)    
        st.markdown('> *Shaded region = recession*')
