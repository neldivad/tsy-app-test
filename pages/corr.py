import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf

import plotly.express as px
import math

def correlacao():
  st.header('Correlation Analysis')
  st.session_state.datatable = pd.read_csv('assets/init_tickers.csv')
  with st.form(key= 'asset_correlation'):
    st.session_state.tickers_sel = st.multiselect('Assets to analyze:',st.session_state.datatable['Ticker'])
    if st.form_submit_button(label='Analyze correlation'): 
      if len(st.session_state.tickers_sel) == 0:
        st.error('At least 1 asset is required to be selected.')

  if len(st.session_state.tickers_sel) != 0:
    calcular_correlacoes()

def fix_col_names(df): # Function to remove the .SA or correct the symbols (??)
  return ['IBOV' if col =='^BVSP' else col.rstrip('.SA') for col in df.columns]

def calcular_correlacoes():
  with st.expander("Correlation between assets and indices", expanded=True):
    if st.checkbox('Correlation', help='Calculate correlation between asset and indices', value=True):
      tickers = [item + '.SA' for item in st.session_state.tickers_sel] # Add .SA suffix to tickers
      tickers += ['^BVSP','^GSPC', 'USDBRL=X']
      #st.session_state.tickers_corr = st.session_state.tickers_sel + ['^BVSP', 'USDBRL=X'] # Adiciona os Indices para comparação

      col1, col2 = st.columns(2)
      with col1:
        periodo = st.selectbox('Select period:',['1 year', '6 months', '3 mmonths'])
        if periodo == '1 year': periodo='1y'
        if periodo == '6 months': periodo = '6mo'
        if periodo == '3 months': periodo = '3mo'
      retornos = yf.download(tickers, period=periodo, progress=False)["Adj Close"].pct_change()
      retornos = retornos.rename(columns={'^BVSP': 'IBOV','^GSPC': 'SP500', 'USDBRL=X': 'Dollar'}) # Renomeia as Colunas
      retornos = retornos.fillna(method='bfill')
      retornos = retornos[1:] # Remove header
      retornos.columns = fix_col_names(retornos) 
      
      correlacao_full = retornos.corr() # Correlation object
      correlacao = correlacao_full.drop('IBOV',1) # Create table removing the Indexes (Separate two comparisons)
      correlacao = correlacao.drop('IBOV',0)
      correlacao = correlacao.drop('Dollar',1)
      correlacao = correlacao.drop('Dollar',0)
      correlacao = correlacao.drop('SP500',1)
      correlacao = correlacao.drop('SP500',0)

      if len(st.session_state.tickers_sel)== 1: # If you have only 1 asset, show only the correlation between it and the Indices
        st.write('**Correlation of assets with IBOV, SP500 and Dollar**')
        corr_table_indices = pd.DataFrame(correlacao_full['IBOV'])
        corr_table_indices['SP500'] = correlacao_full['SP500']
        corr_table_indices['Dollar'] = correlacao_full['Dollar']
        corr_table_indices = corr_table_indices.drop('IBOV',0)
        corr_table_indices = corr_table_indices.drop('SP500', 0)
        corr_table_indices = corr_table_indices.drop('Dollar',0)
        corr_table_indices = corr_table_indices.style.background_gradient(cmap="Oranges").format({"IBOV": "{:.0%}","SP500": "{:.0%}", "Dollar": "{:.0%}"})
        
        st.table(corr_table_indices)
        st.dataframe(corr_table_indices, width=800, height=400)
        st.write(retornos) #
        st.write(correlacao_full)#
        st.write(correlacao)#


      else: # If you have more than 1 asset, show the correlation between them and between the indices
        col1, col2, col3 = st.columns([1, 0.1 ,1])

        with col1:
          st.write('**Correlation between Assets**')
          
          correlacao['Asset 1'] = correlacao.index
          correlacao = correlacao.melt(id_vars='Asset 1', var_name="Asset 2", value_name='Correlation').reset_index(drop=True)
          correlacao = correlacao[ correlacao['Asset 1'] < correlacao['Asset 2'] ].dropna()
          
          highest_corr = correlacao.sort_values("Correlation", ascending=False)
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
          st.write(correlacao)#

        with col3:
          st.write('**Correlation of Assets with IBOV, SP500 and Dollar**')
          corr_table_indices = pd.DataFrame(correlacao_full['IBOV'])
          corr_table_indices['SP500'] = correlacao_full['SP500']
          corr_table_indices['Dollar'] = correlacao_full['Dollar']
          
          corr_table_indices = corr_table_indices.drop('IBOV',0)
          corr_table_indices = corr_table_indices.drop('SP500', 0)
          corr_table_indices = corr_table_indices.drop('Dollar',0)

          ordenar = st.selectbox('Sort by', ['IBOV','SP500', 'Dollar'])
          if ordenar == 'IBOV':
            corr_table_indices = corr_table_indices.sort_values("IBOV",ascending = False)
            corr_table_indices = corr_table_indices.style.background_gradient(cmap="Oranges").format({"IBOV": "{:.0%}","SP500": "{:.0%}", "Dollar": "{:.0%}"})
            st.table(corr_table_indices)
            #st.dataframe(corr_table_indices,width=800,height=400)
          if ordenar == 'SP500':
            corr_table_indices = corr_table_indices.sort_values("SP500",ascending = False)
            corr_table_indices = corr_table_indices.style.background_gradient(cmap="Oranges").format({"IBOV": "{:.0%}","SP500": "{:.0%}", "Dollar": "{:.0%}"})
            st.table(corr_table_indices)
            #st.dataframe(corr_table_indices, height=400)
          if ordenar == 'Dollar':
            corr_table_indices = corr_table_indices.sort_values("Dollar",ascending = False)
            corr_table_indices = corr_table_indices.style.background_gradient(cmap="Oranges").format({"IBOV": "{:.0%}","SP500": "{:.0%}", "Dollar": "{:.0%}"})
            st.table(corr_table_indices)
            #st.dataframe(corr_table_indices, height=400)

  with st.expander("Time Series Correlation Chart", expanded=True):
    if st.checkbox('Correlation over time', help='Show the correlation in time in relation to the Indices'):
      retornos = yf.download(tickers, period='10y', progress=False)["Adj Close"].pct_change()
      retornos = retornos.rename(columns={'^BVSP': 'IBOV','^GSPC': 'SP500', 'USDBRL=X': 'Dollar'}) 
      retornos = retornos.fillna(method='bfill')
      #retornos = retornos[1:] # Apagar primeira linha
      retornos.columns = fix_col_names(retornos) # Corrigir as colunas
      
      indice = st.radio('Indices:',['IBOV', 'SP500', 'Dollar'])
      
      correlacao_tempo = pd.DataFrame(retornos.rolling(252).corr(retornos[indice]) * 100)
      correlacao_tempo.dropna(inplace=True)
      correlacao_tempo.drop(columns=['IBOV','SP500','Dollar'], inplace=True)
      
      st.write(correlacao_tempo)

      wide_df = correlacao_tempo
      fig = px.line(wide_df, x= wide_df.index, y= wide_df.columns)
    
      st.write(fig)

def app():
  st.write('Hey hey heeeeeeeeeeeeeeeeeeeeey')

  correlacao()
  st.write( st.session_state )
