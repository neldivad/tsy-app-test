import streamlit as st
import streamlit.components.v1 as components
from streamlit_player import st_player
from streamlit_option_menu import option_menu

import pandas as pd

# Custom imports 
from pages import home, fundamentals, ark_portfolio #, pr, , test, corr

st.set_page_config(
     page_title="Ticker Symbol YOU | Channel that invests in you",
     page_icon="https://www.qed-insights.com/content/images/2021/04/qed-mark-black---600.png",
     layout="wide",
     initial_sidebar_state="expanded",
 )

def main():
    # Removing and add pages
    pages = {
        "Home": homepage,
        'Fundamentals': fundamental_page,
        'Cathie\'s Portfolio': cathie_portfolio,
    }

    st.sidebar.write(' ')
    with st.sidebar:
        st.title('App Navigation')
        page = option_menu("", tuple(pages.keys()), 
            menu_icon="list", default_index=0)

    pages[page]()

    with st.sidebar.expander('Version'):
        st.write('Streamlit:', st.__version__)
        st.write('Pandas:', pd.__version__)

    with st.sidebar:
        st.markdown('''<small>QED Insights</small>''', unsafe_allow_html=True)
        st.markdown('''<small>dl.eeee.nv@gmail.com</small>''', unsafe_allow_html=True)
    
def homepage():
    home.home()

def fundamental_page():
    fundamentals.fundamentals()

def cathie_portfolio():
    ark_portfolio.app()

if __name__ == "__main__":
    main()
