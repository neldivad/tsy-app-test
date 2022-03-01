import streamlit as st
import streamlit.components.v1 as components
from streamlit_player import st_player

# Custom imports 
from multipage import MultiPage
from pages import home, pr, ark_portfolio, test

st.set_page_config(
     page_title="Ticker Symbol YOU | Channel that invests in you",
     page_icon="https://cdn-icons-png.flaticon.com/512/2617/2617909.png",
     layout="wide",
     initial_sidebar_state="expanded",
 )

st.sidebar.text("> Pre-Alpha version 1.1.1")
with st.sidebar:
     components.html("""
     <a href="https://twitter.com/just_neldivad" class="twitter-follow-button" data-show-screen-name="true" data-show-count="true">Follow @just_neldivad</a>
     <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
     """, height=30,)
    
# Create an instance of the app 
app = MultiPage()

st.title("TSY")
st.subheader("Random text here so I know where I put it")
# Add all your application here
app.add_page("Wassup", home.app)
app.add_page("PR", pr.app)
app.add_page("ARK Invest Portfolio", ark_portfolio.app)

# app.add_page("DATA STRUCTURES", data_structures.app)
# app.add_page("PROBLEMS", problems.app)

# The main app
app.run() 
