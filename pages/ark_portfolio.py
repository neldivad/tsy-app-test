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

from app_functions import derive_columns, derive_etf_columns

def app():
    #-----------------------------
    # Internal functions
    #----------------------------
    @st.cache
    def make_df_i(spreadsheet_id, sheetname):
        gc = pygsheets.authorize(service_account_file= 'pages/gsheet-key.json')
        sh = gc.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(property= 'title', value= sheetname)
        df = worksheet.get_as_df()
        return df
    
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

    @st.cache
    def convert_df(df):
         # IMPORTANT: Cache the conversion to prevent computation on every rerun
         return df.to_csv().encode('utf-8')
    #--------------------------------------
    # Date object
    #---------------------------------------
    current_time= datetime.datetime.now(pytz.timezone('US/Eastern'))
    date_string= current_time.strftime('%Y%m%d')

    spreadsheet_id = st.secrets['gsheet_id']
        # dnd
    st.write(spreadsheet_id)
    st.write(st.secrets["gcp_service_account"])
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
    test_df = pd.read_csv("https://docs.google.com/spreadsheets/d/e/2PACX-1vSJ5B9E5p6MbKot2HBwAwkGGr_YxVJWgUdTgUVvamEtI6Vo2IdsqcjUq-MCdVoJD7dYpawtaHxgfSNO/pub?output=csv") 
    st.dataframe(test_df)
    
#     df = make_df(spreadsheet_id, 'Daily ARK data').astype(str)
#     st.write(df)

    
    df = make_df(spreadsheet_id, 'Daily ARK data').astype(str)
    st.dataframe(df)
    
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
        data = make_df_i(spreadsheet_id, f'Daily {df} data').astype(str)
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
    from app_functions import create_ark_conviction_df, create_ark_etf_conviction_df

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
    from app_functions import make_line_chart
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
