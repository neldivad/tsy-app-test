import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf

import plotly.express as px
import math

def correlation_analysis():
  st.header('Correlation Analysis')
  st.session_state.datatable = pd.read_csv('assets/init_tickers.csv')
  with st.form(key= 'asset_correlation'):
    st.session_state.tickers_sel = st.multiselect('Assets to analyze:',st.session_state.datatable['Ticker'])
    if st.form_submit_button(label='Analyze correlation'): 
      if len(st.session_state.tickers_sel) == 0:
        st.error('At least 1 asset is required to be selected.')

  if len(st.session_state.tickers_sel) != 0:
    calculate_correlation()

def fix_col_names(df): # Function to remove the .SA or correct the symbols (??)
  return ['IBOV' if col =='^BVSP' else col.rstrip('.SA') for col in df.columns]

def calculate_correlation():
  with st.expander("Correlation between assets and indices", expanded=True):
    if st.checkbox('Correlation', help='Calculate correlation between asset and indices', value=True):
      tickers = [item + '.SA' for item in st.session_state.tickers_sel] # Add .SA suffix to tickers
      tickers += ['^BVSP','^GSPC', 'USDBRL=X']

      col1, col2 = st.columns(2)
      with col1:
        time_period = st.selectbox('Select period:',['1 year', '6 months', '3 mmonths'])
        if time_period == '1 year': time_period='1y'
        if time_period == '6 months': time_period = '6mo'
        if time_period == '3 months': time_period = '3mo'
      ticker_returns = yf.download(tickers, period=time_period, progress=False)["Adj Close"].pct_change()
      ticker_returns = ticker_returns.rename(columns={'^BVSP': 'IBOV','^GSPC': 'SP500', 'USDBRL=X': 'Dollar'})
      ticker_returns = ticker_returns.fillna(method='bfill')
      
      from copy import deepcopy #
      check_df = deepcopy( ticker_returns )
      
      ticker_returns = ticker_returns[1:] # Remove header
      ticker_returns.columns = fix_col_names(ticker_returns) 
      
      corr_full = ticker_returns.corr() # Correlation object
      corr_table = corr_full.drop('IBOV',1) # Create table removing the Indexes (Separate two comparisons)
      corr_table = corr_table.drop('IBOV',0)
      corr_table = corr_table.drop('Dollar',1)
      corr_table = corr_table.drop('Dollar',0)
      corr_table = corr_table.drop('SP500',1)
      corr_table = corr_table.drop('SP500',0)

      if len(st.session_state.tickers_sel)== 1: # If you have only 1 asset, show only the correlation between it and the Indices
        st.write('**Correlation of assets with IBOV, SP500 and Dollar**')
        corr_table_indices = pd.DataFrame(corr_full['IBOV'])
        corr_table_indices['SP500'] = corr_full['SP500']
        corr_table_indices['Dollar'] = corr_full['Dollar']
        corr_table_indices = corr_table_indices.drop('IBOV',0)
        corr_table_indices = corr_table_indices.drop('SP500', 0)
        corr_table_indices = corr_table_indices.drop('Dollar',0)
        corr_table_indices = corr_table_indices.style.background_gradient(cmap="Oranges").format({"IBOV": "{:.0%}","SP500": "{:.0%}", "Dollar": "{:.0%}"})
        
        st.table(corr_table_indices)
        st.dataframe(corr_table_indices, width=800, height=400)
        
        st.write(tickers) #
        st.write(check_df) #
        st.write(ticker_returns) #
        st.write(ticker_returns) #
        st.write(corr_full) #
        st.write(corr_table) #


      else: # If you have more than 1 asset, show the correlation between them and between the indices
        col1, col2, col3 = st.columns([1, 0.1 ,1])

        with col1:
          st.write('**Correlation between Assets**')
          
          corr_table['Asset 1'] = corr_table.index
          corr_table = corr_table.melt(id_vars='Asset 1', var_name="Asset 2", value_name='Correlation').reset_index(drop=True)
          corr_table = corr_table[ corr_table['Asset 1'] < corr_table['Asset 2'] ].dropna()
          
          highest_corr = corr_table.sort_values("Correlation", ascending=False)
          highest_corr.reset_index(drop=True, inplace=True)
          highest_corr.index += 1  # Start index at 1 instead of 0 (why?)

          def _color_red_or_green(val):  # Function for table colormap
            color = 'red' if val < 0 else 'green'
            # return 'color: %s' % color
            return 'background-color: %s' % color

          # highest_corr = highest_corr.style.applymap(_color_red_or_green, subset=['Correlação']).format({"Correlação": "{:.0%}"}) # Aplicar Cores
          highest_corr = highest_corr.style.background_gradient(cmap="Oranges").format({"Correlation": "{:.0%}"})

          st.table(highest_corr)
          st.dataframe(highest_corr, height=600)
          st.write(corr_table)#

        with col3:
          st.write('**Correlation of Assets with IBOV, SP500 and Dollar**')
          corr_table_indices = pd.DataFrame(corr_full['IBOV'])
          corr_table_indices['SP500'] = corr_full['SP500']
          corr_table_indices['Dollar'] = corr_full['Dollar']
          
          corr_table_indices = corr_table_indices.drop('IBOV',0)
          corr_table_indices = corr_table_indices.drop('SP500', 0)
          corr_table_indices = corr_table_indices.drop('Dollar',0)

          order = st.selectbox('Sort by', ['IBOV','SP500', 'Dollar'])
          if order == 'IBOV':
            corr_table_indices = corr_table_indices.sort_values("IBOV",ascending = False)
            corr_table_indices = corr_table_indices.style.background_gradient(cmap="Oranges").format({"IBOV": "{:.0%}","SP500": "{:.0%}", "Dollar": "{:.0%}"})
            st.table(corr_table_indices)
            
          if order == 'SP500':
            corr_table_indices = corr_table_indices.sort_values("SP500",ascending = False)
            corr_table_indices = corr_table_indices.style.background_gradient(cmap="Oranges").format({"IBOV": "{:.0%}","SP500": "{:.0%}", "Dollar": "{:.0%}"})
            st.table(corr_table_indices)

          if order == 'Dollar':
            corr_table_indices = corr_table_indices.sort_values("Dollar",ascending = False)
            corr_table_indices = corr_table_indices.style.background_gradient(cmap="Oranges").format({"IBOV": "{:.0%}","SP500": "{:.0%}", "Dollar": "{:.0%}"})
            st.table(corr_table_indices)

  with st.expander("Time Series Correlation Chart", expanded=True):
    if st.checkbox('Correlation over time', help='Show the correlation in time in relation to the Indices'):
      ticker_returns = yf.download(tickers, period='10y', progress=False)["Adj Close"].pct_change()
      ticker_returns = ticker_returns.rename(columns={'^BVSP': 'IBOV','^GSPC': 'SP500', 'USDBRL=X': 'Dollar'}) 
      ticker_returns = ticker_returns.fillna(method='bfill')
      
      ticker_returns.columns = fix_col_names(ticker_returns) 
      
      indice = st.radio('Indices:',['IBOV', 'SP500', 'Dollar'])
      
      corr_temp = pd.DataFrame(ticker_returns.rolling(252).corr(ticker_returns[indice]) * 100)
      corr_temp.dropna(inplace=True)
      corr_temp.drop(columns=['IBOV','SP500','Dollar'], inplace=True)
      
      st.write(corr_temp)

      wide_df = corr_temp
      fig = px.line(wide_df, x= wide_df.index, y= wide_df.columns)
    
      st.write(fig)

def app():
  st.write('Hey hey heeeeeeeeeeeeeeeeeeeeey')

  correlation_analysis()
  st.write( st.session_state )
