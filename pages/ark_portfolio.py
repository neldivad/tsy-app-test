import streamlit as st
import streamlit.components.v1 as components

import pandas as pd
import numpy as np
from PIL import Image
from io import BytesIO
import base64
import json

import pytz
import datetime
import time

import plotly.graph_objs as go
import plotly.express as px

from google.oauth2 import service_account
import pygsheets

def app():
    #--------------------------------------
    # Date object
    #---------------------------------------
    current_time= datetime.datetime.now(pytz.timezone('US/Eastern'))
    date_string= current_time.strftime('%Y%m%d')

    spreadsheet_id = st.secrets['gsheet_id']
    #----------------
    # Title
    #---------------
    st.title('Cathie\'s Portfolio')
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

    #-------------------------
    # About
    #------------------------
    with st.expander('About this app', expanded=False):
        st.markdown(f"""
    * **Current time:** {current_time} 
    * *More updates to come*
    """)

    #--------------------
    # Markdown
    #-------------------
    st.markdown("""
    ## Cathie Wood's Portfolio
    Historic holdings for every Cathie's funds.
    """)

    etfs = ['ARKK', 'ARKG',
            'ARKF', 'ARKQ', 'ARKW', 
            'ARKX', 'CTRU', 'PRNT',
            'IZRL']

    with st.expander('Select ETF', expanded=True):
        ms_etfs = st.multiselect('', etfs, etfs[:1] )

        for df in ms_etfs:
            data = make_df(spreadsheet_id, f'Daily {df} data').astype(str)
            st.subheader(f'Data for {df}')
            st.write(data)
            st.download_button(
                label='Click to download CSV file', 
                data= convert_df(data), 
                file_name= f'data-for-{df}-{date_string}.csv',
                mime='text/csv')

    st.write('---')

    #---------------------------
    #
    #---------------------------

    st.subheader(f'ARK Invest Total Holdings for {current_time.strftime("%d-%m-%Y")}')
    ark_daily = make_df(spreadsheet_id, 'Daily ARK data')
    convict = create_ark_conviction_df(ark_daily).reset_index()
    convict = derive_columns(convict)

    st.write(convict.astype(str))
    st.download_button(
        label='Click to download CSV file', 
        data= convert_df(convict), 
        file_name= f'arkinvest-total-holdings-{date_string}.csv',
        mime='text/csv')

    # Multiselect box for weighing
    col2, col3 = st.columns( (3, 2) )
    with col2:
        ms_ticker = st.multiselect(
            'Select ticker',
            convict['ticker'].unique(), 
            convict['ticker'].unique()[:10],
        ) 
        selected_ticker = convict[ convict['ticker'].isin(ms_ticker) ]

    #--------------------------------------
    # Make share and market rank plot
    #-----------------------------------------
    with col2:
        mv_rank_fig = make_line_chart(
            selected_ticker, 
            'date', 'mv rank', 'ticker', 
            'ARK Invest Portfolio Weighing Rank (market value)',
            xtitle= 'Date',
            ytitle= 'Portfolio Weigh Rank (market value)',
            ctitle= 'Ticker',
            yreverse= True,
            )
        sh_rank_fig = make_line_chart(
            selected_ticker, 
            'date', 'share rank', 'ticker', 
            'ARK Invest Portfolio Weighing Rank (No. shares)',
            xtitle= 'Date',
            ytitle= 'Portfolio Weigh Rank (share count)',
            ctitle= 'Ticker',
            yreverse= True,
            )
        st.plotly_chart(mv_rank_fig)
        st.plotly_chart(sh_rank_fig)


#------------------------
# Helper functions
#--------------------------
def make_df(spreadsheet_id, sheetname):
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            ],
    )
    gc = pygsheets.authorize(custom_credentials= credentials)
    sh = gc.open_by_key(spreadsheet_id)
    worksheet = sh.worksheet(property= 'title', value= sheetname)
    df = worksheet.get_as_df()
    return df

# @st.cache
def convert_df(df):
     # IMPORTANT: Cache the conversion to prevent computation on every rerun
     return df.to_csv().encode('utf-8')


def create_ark_conviction_df(df):
    convict = pd.DataFrame(df.groupby(['date', 'ticker', 'cusip'])[['shares', 'market value ($)']].sum() )
    convict['weight (%)'] = convict['market value ($)'] / convict.groupby(['date'])['market value ($)'].sum()  * 100
    
    convict = convict.groupby(level=[0], group_keys=False) \
              .apply(lambda x: x.sort_values('weight (%)', ascending=False))
    
    return convict.round(2)

def create_ark_etf_conviction_df(df):
    convict = pd.DataFrame(df.groupby(['date', 'fund', 'cusip', 'ticker'])[['shares', 'market value ($)', 'weight (%)']].sum() )
    
    convict = convict.groupby(level=[0, 1], group_keys=False) \
              .apply(lambda x: x.sort_values('weight (%)', ascending=False))
    
    return convict.round(2)

def derive_columns(df):
    """
    Dataframe passed should be dataframe returned through create_ark_conviction() function.
    Columns must not be renamed. 
    """
    df['price'] = df['market value ($)'] / df['shares']
    
    # Get change for the day
    df['d_shares']     = df.groupby(['ticker'])['shares'].diff()
    df['d_mv']         = df.groupby(['ticker'])['market value ($)'].diff()
    df['d_shares (%)'] = df['d_shares'] *100 / df.groupby(['ticker'])['shares'].shift(1) 
    df['d_mv (%)']     = df['d_mv'] *100 / df.groupby(['ticker'])['market value ($)'].shift(1) 
    df['d_weight (%)'] = df.groupby(['ticker'])['weight (%)'].diff()
    
    
    # Get rank for the day
    df = df.fillna(0)
    df['weight rank']  = df.groupby(['date'])['weight (%)'].rank('dense', ascending=False)
    df['mv rank']      = df.groupby(['date'])['market value ($)'].rank('dense', ascending=False)
    df['share rank']   = df.groupby(['date'])['shares'].rank('dense', ascending=False)
    df['d_mv rank']    = df.groupby(['date'])['d_mv'].rank('dense', ascending=False)
    df['d_shares rank']= df.groupby(['date'])['d_shares'].rank('dense', ascending=False)
    
    df = df.sort_values(by= ['date', 'weight (%)'], ascending=[True, False])
    
    return df

def derive_etf_columns(df):
    """
    Dataframe passed should be dataframe returned through create_ark_etf_conviction() function.
    Columns must not be renamed. 
    """
    df['price'] = df['market value ($)'] / df['shares']
    
    # Get change for the day
    df['d_shares']     = df.groupby(['fund', 'ticker'])['shares'].diff()
    df['d_mv']         = df.groupby(['fund', 'ticker'])['market value ($)'].diff()
    df['d_shares (%)'] = df['d_shares'] *100 / df.groupby(['fund', 'ticker'])['shares'].shift(1) 
    df['d_mv (%)']     = df['d_mv'] *100 / df.groupby(['fund', 'ticker'])['market value ($)'].shift(1) 
    df['d_weight (%)'] = df.groupby(['fund', 'ticker'])['weight (%)'].diff() 
    
    
    # Get rank for the day
    df = df.fillna(0)
    df['weight rank']  = df.groupby(['fund', 'date'])['weight (%)'].rank('dense', ascending=False)
    df['mv rank']      = df.groupby(['fund', 'date'])['market value ($)'].rank('dense', ascending=False)
    df['share rank']   = df.groupby(['fund', 'date'])['shares'].rank('dense', ascending=False)
    df['d_mv rank']    = df.groupby(['fund', 'date'])['d_mv'].rank('dense', ascending=False)
    df['d_shares rank']= df.groupby(['fund', 'date'])['d_shares'].rank('dense', ascending=False)
    
    df = df.sort_values(by= ['date', 'fund', 'weight (%)'], ascending=[True, True, False])
    
    return df


########################
#
#######################
def make_line_chart(
    df, xdata, ydata, cdata, 
    title, height=600, width=800, 
    xtitle=None, ytitle=None, ctitle=None,
    yreverse=False, legend=True
    ):
    if xtitle == None:
        xtitle = xdata
    if ytitle == None:
        ytitle = ydata
    if ctitle == None:
        ctitle = cdata
    
    fig = px.line(
        df, 
        x= xdata,
        y= ydata,
        color= cdata,
        labels={
            f"{xdata}": xtitle,
            f"{ydata}": ytitle,
            f"{cdata}": ctitle,
        },
    )

    yauto = True
    if yreverse == True:
        yauto = 'reversed'

    fig.update_layout(
        title={
            'text': title,
            'y':1,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20)
            },
        height = height,
        width = width,
        xaxis=dict(
            showline=True,
            linecolor='rgb(204, 204, 204)',
            linewidth=2,
            ticks='outside',
            tickfont=dict(
                family='Arial',
                size=12,
                color='rgb(82, 82, 82)',
            ),
        ),
        yaxis=dict(
            autorange= yauto
        ),
        showlegend= legend,
        plot_bgcolor='#F1F8F6',
    )
    fig.update_xaxes(showline=True, linewidth=2, linecolor='#658e9c', gridcolor='#A2D3C2')
    fig.update_yaxes(showline=True, linewidth=2, linecolor='#658e9c', gridcolor='#A2D3C2', zeroline= False,)

    fig.layout.images = [dict(
        source="https://www.qed-insights.com/content/images/2021/04/qed-horizontal-black---transp-8.png",
        xref="paper", yref="paper",
        x=0.92, y=0.03,
        sizex=0.2, sizey=0.2,
        xanchor="center", yanchor="bottom",
        layer= "below",
      )]
    return fig
