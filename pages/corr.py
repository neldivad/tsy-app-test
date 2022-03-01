import streamlit as st
import numpy as np
import pandas as pd
import yfinance as yf

import plotly.express as px
import math

def correlacao():
  st.header('Análise de Correlação')
  st.session_state.tabela_papeis = pd.read_csv('assets/init_tickers.csv')
  with st.form(key='Correlacao_Inserir_Ativos'):
    st.session_state.tickers_sel = st.multiselect('Insira os Ativos para analisar as correlações',st.session_state.tabela_papeis['Ticker'])
    if st.form_submit_button(label='Analisar Correlações'): 
      if len(st.session_state.tickers_sel) == 0:
        st.error('Lista Vazia. Insira ao menos 1 ativo!')

  if len(st.session_state.tickers_sel) != 0: # Se a lista estiver vazia, não mostra nada
    calcular_correlacoes()

def fix_col_names(df): # Função para tirar os .SA ou corrigir os simbolos
  return ['IBOV' if col =='^BVSP' else col.rstrip('.SA') for col in df.columns]

def calcular_correlacoes():
  with st.expander("Correlação entre Ativos e Indices", expanded=True):
    if st.checkbox('Correlação', help='Calcular a correlação entre os Ativos e os Indices do Mercado', value=True):
      tickers = [item + '.SA' for item in st.session_state.tickers_sel] # Adicionar o '.SA' nos tickers
      tickers += ['^BVSP','^GSPC', 'USDBRL=X']
      #st.session_state.tickers_corr = st.session_state.tickers_sel + ['^BVSP', 'USDBRL=X'] # Adiciona os Indices para comparação

      col1, col2 = st.columns(2)
      with col1:
        periodo = st.selectbox('Período:',['1 ano', '6 meses', '3 meses'])
        if periodo == '1 ano': periodo='1y'
        if periodo == '6 meses': periodo = '6mo'
        if periodo == '3 meses': periodo = '3mo'
      retornos = yf.download(tickers, period=periodo, progress=False)["Adj Close"].pct_change()
      retornos = retornos.rename(columns={'^BVSP': 'IBOV','^GSPC': 'SP500', 'USDBRL=X': 'Dolar'}) # Renomeia as Colunas
      retornos = retornos.fillna(method='bfill')
      retornos = retornos[1:] # Apagar primeira linha
      retornos.columns = fix_col_names(retornos) # Corrigir as colunas
      correlacao_full = retornos.corr() # Calcula a correlação entre todo mundo com indices
      correlacao = correlacao_full.drop('IBOV',1) # Cria tabela retirando os Indices (Separar duas comparacoes)
      correlacao = correlacao.drop('IBOV',0)
      correlacao = correlacao.drop('Dolar',1)
      correlacao = correlacao.drop('Dolar',0)
      correlacao = correlacao.drop('SP500',1)
      correlacao = correlacao.drop('SP500',0)

      if len(st.session_state.tickers_sel)== 1: # Se tiver apenas 1 Ativo, mostrar apenas a correlação entre ele e os Indices
        st.write('**Correlação dos Ativos com IBOV, SP500 e Dolar**')
        corr_table_indices = pd.DataFrame(correlacao_full['IBOV'])
        corr_table_indices['SP500'] = correlacao_full['SP500']
        corr_table_indices['Dolar'] = correlacao_full['Dolar']
        corr_table_indices = corr_table_indices.drop('IBOV',0)
        corr_table_indices = corr_table_indices.drop('SP500', 0)
        corr_table_indices = corr_table_indices.drop('Dolar',0)
        corr_table_indices = corr_table_indices.style.background_gradient(cmap="Oranges").format({"IBOV": "{:.0%}","SP500": "{:.0%}", "Dolar": "{:.0%}"})
        st.table(corr_table_indices)
        #st.dataframe(corr_table_indices,width=800,height=400)


      else: #Se tiver mais de 1 ativo, mostrar a correlação entre eles e entre os indices
        col1, col2, col3 = st.columns([1,0.1,1])

        with col1:
          st.write('**Correlação entre os Ativos**')
          correlacao['Ação 1'] = correlacao.index
          correlacao = correlacao.melt(id_vars='Ação 1', var_name="Ação 2", value_name='Correlação').reset_index(drop=True)
          correlacao = correlacao[correlacao['Ação 1'] < correlacao['Ação 2']].dropna()
          highest_corr = correlacao.sort_values("Correlação", ascending=False)
          highest_corr.reset_index(drop=True, inplace=True)  # Reseta o indice
          highest_corr.index += 1  # Iniciar o index em 1 ao invés de 0

          def _color_red_or_green(val):  # Função para o mapa de cores da tabela
            color = 'red' if val < 0 else 'green'
            # return 'color: %s' % color
            return 'background-color: %s' % color

          # highest_corr = highest_corr.style.applymap(_color_red_or_green, subset=['Correlação']).format({"Correlação": "{:.0%}"}) # Aplicar Cores
          highest_corr = highest_corr.style.background_gradient(cmap="Oranges").format({"Correlação": "{:.0%}"})

          st.table(highest_corr)
          # st.dataframe(highest_corr, height=600)

        with col3:
          st.write('**Correlação dos Ativos com IBOV, SP500 e Dolar**')
          corr_table_indices = pd.DataFrame(correlacao_full['IBOV'])
          corr_table_indices['SP500'] = correlacao_full['SP500']
          corr_table_indices['Dolar'] = correlacao_full['Dolar']
          corr_table_indices = corr_table_indices.drop('IBOV',0)
          corr_table_indices = corr_table_indices.drop('SP500', 0)
          corr_table_indices = corr_table_indices.drop('Dolar',0)

          ordenar = st.selectbox('Ordenar por', ['IBOV','SP500', 'Dolar'])
          if ordenar == 'IBOV':
            corr_table_indices = corr_table_indices.sort_values("IBOV",ascending = False)
            corr_table_indices = corr_table_indices.style.background_gradient(cmap="Oranges").format({"IBOV": "{:.0%}","SP500": "{:.0%}", "Dolar": "{:.0%}"})
            st.table(corr_table_indices)
            #st.dataframe(corr_table_indices,width=800,height=400)
          if ordenar == 'SP500':
            corr_table_indices = corr_table_indices.sort_values("SP500",ascending = False)
            corr_table_indices = corr_table_indices.style.background_gradient(cmap="Oranges").format({"IBOV": "{:.0%}","SP500": "{:.0%}", "Dolar": "{:.0%}"})
            st.table(corr_table_indices)
            #st.dataframe(corr_table_indices, height=400)
          if ordenar == 'Dolar':
            corr_table_indices = corr_table_indices.sort_values("Dolar",ascending = False)
            corr_table_indices = corr_table_indices.style.background_gradient(cmap="Oranges").format({"IBOV": "{:.0%}","SP500": "{:.0%}", "Dolar": "{:.0%}"})
            st.table(corr_table_indices)
            #st.dataframe(corr_table_indices, height=400)

  with st.expander("Gráfico de Correlação no Tempo", expanded=True):
    if st.checkbox('Correlação no Tempo', help='Mostrar a correlação no tempo em relação aos Indices'):
      retornos = yf.download(tickers, period='10y', progress=False)["Adj Close"].pct_change()
      retornos = retornos.rename(columns={'^BVSP': 'IBOV','^GSPC': 'SP500', 'USDBRL=X': 'Dolar'}) # Renomeia as Colunas
      retornos = retornos.fillna(method='bfill')
      #retornos = retornos[1:] # Apagar primeira linha
      retornos.columns = fix_col_names(retornos) # Corrigir as colunas
      indice = st.radio('Indices:',['IBOV', 'SP500', 'Dolar'])
      correlacao_tempo = pd.DataFrame(retornos.rolling(252).corr(retornos[indice]) * 100)
      correlacao_tempo.dropna(inplace=True)
      correlacao_tempo.drop(columns=['IBOV','SP500','Dolar'], inplace=True)
      st.write(correlacao_tempo)
      fig = correlacao_tempo.plot(
        #asFigure=True, 
                                  xTitle='Data', yTitle='Correlação %',
                                   title='Correlação no Tempo entre os Ativos e ' + indice)
      # fig = px.line(correlacao_tempo, x= 'Data', y= 'Correlação %')
    
      st.write(fig)

def app():
  st.write('Hey hey heeeeeeeeeeeeeeeeeeeeey')
  correlacao()
