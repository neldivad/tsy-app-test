import numpy as np
import pandas as pd
import streamlit as st

from google.oauth2 import service_account
import pygsheets

import plotly.express as px
import plotly.graph_objects as go

################################
# Dataframe uploads and downloads
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
        layer= "below"
      )]
    return fig


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
