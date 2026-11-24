import streamlit as st

# Title of App
st.title("Georgia Tech Football Analytics")

# Assignment Data
st.header("CS 1301")
st.subheader("Team XX, Web Development - Section X")  # TODO: your team number and section
st.subheader("Your Name, Partner Name")  # TODO: both names

# Introduction
st.write("""
Welcome to our Georgia Tech football analytics app! We built it to explore how data
can tell the story of the Yellow Jackets' seasons. Use the sidebar on the left to
navigate between the pages:

1. **Season Explorer**: Explore Georgia Tech's results by season, look up player stats,
   see all-time records against opponents, and compare pregame win probabilities to
   what actually happened.
2. **Football Chatbot**: Chat with an AI Yellow Jackets fan about Georgia Tech
   football and sports analytics.
""")

st.caption("Data from the College Football Data API (CFBD).")
