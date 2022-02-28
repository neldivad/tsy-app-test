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

from bs4 import BeautifulSoup
import requests
from google.oauth2 import service_account
import pygsheets

################################
# Helper functions unable to import from different file
################################
# @st.cache # cache seems to break the code
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

###########################
# Dataframe manipulation
#############################

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
@st.cache
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
        source="https://raw.githubusercontent.com/neldivad/tsy-app-test/main/assets/tickersymbolyou-transparent.png",
        xref="paper", yref="paper",
        x=0.9, y=0.15,
        sizex=0.4, sizey=0.4,
        xanchor="center", yanchor="bottom",
        layer= "below",
      )]
    return fig

@st.cache
def make_corr_map(data, title, zmin=-1, zmax=1, height=600, width= 800):
    """
    data: Your dataframe.
    title: Title for the correlation matrix.
    zmin: Minimum number for color scale. (-1 to 1). Default = -1.
    zmax: Maximum number for color scale. (-1 to 1). Default = 1.
    height: Default = 600
    width: Default = 800
    """
    
    data = data.corr()
    mask = np.triu(np.ones_like(data, dtype=bool))
    rLT = data.mask(mask)

    heat = go.Heatmap(
        z = rLT,
        x = rLT.columns.values,
        y = rLT.columns.values,
        zmin = zmin, 
            # Sets the lower bound of the color domain
        zmax = zmax,
            # Sets the upper bound of color domain
        xgap = 1, # Sets the horizontal gap (in pixels) between bricks
        ygap = 1,
        colorscale = 'RdBu'
    )

    title = title

    layout = go.Layout(
        title_text=title, 
        title_x=0.5, 
        width= width, 
        height= height,
        xaxis_showgrid=False,
        yaxis_showgrid=False,
        yaxis_autorange='reversed'
    )

    fig=go.Figure(data=[heat], layout=layout)
    return fig 

######################################
# Finaly, app building time
######################################
def app():
    #----------------------------------
    # Helper function (can't seem to import properly)
    #---------------------------------
    #from app_functions import derive_columns, derive_etf_columns 
    # @st.cache # cache seems to break the code
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
    
    #--------------------------------------
    # Date object
    #---------------------------------------
    current_time= datetime.datetime.now(pytz.timezone('US/Eastern'))
    date_string= current_time.strftime('%Y%m%d')

    spreadsheet_id = st.secrets['gsheet_id']
    #----------------
    # Title
    #---------------
    image = Image.open('assets/tickersymbolyou-transparent.png')
    col1, col2, col3 = st.columns([2, 3, 2])
    col2.image(image, use_column_width=True)

    st.subheader('Test Youtube Embed')
    st.video("https://youtu.be/U3aXWizDbQ4")
    
    st.subheader('Test Soundcloud Embed')
    components.html("""
    <iframe width="100%" height="300" scrolling="no" frameborder="no" allow="autoplay" src="https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/884456854&color=%23ff5500&auto_play=false&hide_related=false&show_comments=true&show_user=true&show_reposts=false&show_teaser=true&visual=true"></iframe><div style="font-size: 10px; color: #cccccc;line-break: anywhere;word-break: normal;overflow: hidden;white-space: nowrap;text-overflow: ellipsis; font-family: Interstate,Lucida Grande,Lucida Sans Unicode,Lucida Sans,Garuda,Verdana,Tahoma,sans-serif;font-weight: 100;"><a href="https://soundcloud.com/divadlen" title="Nel D." target="_blank" style="color: #cccccc; text-decoration: none;">Nel D.</a> · <a href="https://soundcloud.com/divadlen/othello-piano" title="Othello (piano)" target="_blank" style="color: #cccccc; text-decoration: none;">Othello (piano)</a></div>
    """, height=300)
    
    st.subheader('Test Spotify Embed')
    st.markdown('> My spotify')
    components.html("""
    <iframe style="border-radius:12px" src="https://open.spotify.com/embed/artist/7LhsgxH9e9ZvF9yxyEz0wR?utm_source=generator" width="100%" height="280" frameBorder="0" allowfullscreen="" allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"></iframe>
    """, height=300)

    #-------------------------
    # About
    #------------------------
    expander_bar= st.expander('About this app')
    expander_bar.markdown(f"""
    * **Current time:** {current_time} 
    * **Python libraries:** base64, pandas, streamlit, numpy, matplotlib, seaborn, BeautifulSoup, requests, json, time
    * **Data source:** [CoinMarketCap](http://coinmarketcap.com).
    * **Credit:** Web scraper adapted from the Medium article *[Web Scraping Crypto Prices With Python](https://towardsdatascience.com/web-scraping-crypto-prices-with-python-41072ea5b5bf)* written by [Bryan Feng](https://medium.com/@bryanf).
    """)

    #---------------------------------------
    # Page layout
    #---------------------------------
    col1 = st.sidebar



    #--------------------
    # Markdown
    #-------------------
    st.markdown("""
    ## Cathie Wood's Portfolio
    Historic holdings for every Cathie's funds.
    """)
    df = make_df(spreadsheet_id, 'Daily ARK data').astype(str)
    st.write(df)
    
    st.download_button(
        label='Click to download CSV file', 
        data= convert_df(df), 
        file_name= f'data-for-ARK-Invest-{date_string}.csv',
        mime='text/csv')

    etfs = ['ARKK', 'ARKG',
            'ARKF', 'ARKQ', 'ARKW', 
            'ARKX', 'CTRU', 'PRNT',
            'IZRL']

    st.header('Select ETF')
    expander_etf= st.expander('Select ETF')
    ms_etfs = expander_etf.multiselect('', etfs, etfs[:3] )
    for df in ms_etfs:
        data = make_df(spreadsheet_id, f'Daily {df} data').astype(str)
        expander_etf.subheader(f'Data for {df}')
        expander_etf.write(data)
        expander_etf.download_button(
            label='Click to download CSV file', 
            data= convert_df(data), 
            file_name= f'data-for-{df}-{date_string}.csv',
            mime='text/csv')
    st.write('---')

    #---------------------------
    #
    #---------------------------
    #from app_functions import create_ark_conviction_df, create_ark_etf_conviction_df

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
    col1.markdown("""
    --------------
    # Input features penguin
    Example csv input
    """)
    ms_ticker = col1.multiselect(
        'Select ticker',
        convict['ticker'].unique(), 
        convict['ticker'].unique()[:10],
    ) 
    selected_ticker = convict[ convict['ticker'].isin(ms_ticker) ]

    col2, col3 = st.columns( (3, 2) )
    # Make share and market rank plot
    #from app_functions import make_line_chart
    
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
    col2.plotly_chart(mv_rank_fig)
    col2.plotly_chart(sh_rank_fig) 
