import streamlit as st
import streamlit.components.v1 as components

from PIL import Image

def app():
    #-------------------------
    # About
    #------------------------
    expander_bar= st.expander('About this app')
    expander_bar.markdown(f"""
    * **Current time:** 28 Feb 2022 
    * **Python libraries:** base64, pandas, streamlit, numpy, matplotlib, seaborn, BeautifulSoup, requests, json, time
    * **Data source:** [CoinMarketCap](http://coinmarketcap.com).
    * **Credit:** Web scraper adapted from the Medium article *[Web Scraping Crypto Prices With Python](https://towardsdatascience.com/web-scraping-crypto-prices-with-python-41072ea5b5bf)* written by [Bryan Feng](https://medium.com/@bryanf).
    """)
    col1 = st.sidebar
    
    #--------------------
    # Markdown
    #-------------------
    st.markdown("""
    ## Cathie Wood's Portfolio
    Historic holdings for every Cathie's funds.
    """)
    df = app_functions.make_df(spreadsheet_id, 'Daily ARK data').astype(str)
    st.write(df)
    
    from app_functions2 import convert_df
    st.download_button(
      label='Click to download CSV file', 
      data= convert_df(df), 
      file_name= f'data.csv',
      mime='text/csv')
    
    
