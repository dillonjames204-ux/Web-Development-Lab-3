import os

import streamlit as st
from pydantic_ai import Agent

# Give Pydantic AI your Gemini key from secrets.toml (or the app's Secrets settings when deployed)
os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

# The Gemini model this app uses
MODEL = "google:gemini-2.5-flash-lite"

st.title("Georgia Tech Football Chatbot")

# The agent: its instructions control how it behaves
agent = Agent(
    MODEL,
    instructions=(
        "You are a friendly Georgia Tech football fan chatting with another fan. "
        "Rules: "
        "1. Keep every answer to 1 to 3 short sentences. "
        "2. You have no access to live data, stats, scores, rosters, or records. "
        "If asked for any exact number (yards, scores, records, win totals, dates), "
        "say plainly that you can't look that up, then point the user to the Season "
        "Explorer page for real numbers. Do not guess. "
        "3. Never invent facts, numbers, or claims about how a player or the team "
        "is performing this season. "
        "4. You can talk about football in general: how positions work, how analytics "
        "like win probability work, and Georgia Tech traditions you are confident about. "
        "5. Stay on football and sports analytics. If a question is off topic, "
        "steer the conversation back politely. "
        "6. Sound like a real fan: casual and upbeat, not a list of buzzwords."
    ),
)

# Remember the conversation between reruns
if "messages" not in st.session_state:
    st.session_state.messages = []  # what we show on screen
    st.session_state.history = []  # what the agent remembers

# Show past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Message box at the bottom
prompt = st.chat_input("Ask me about Georgia Tech football...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        try:
            result = agent.run_sync(prompt, message_history=st.session_state.history)
            reply = result.output
            st.session_state.history = result.all_messages()
        except Exception as error:
            print("Chatbot error:", error)  # shows in the terminal / Manage app logs
            reply = f"Sorry, something went wrong: {error}"
        st.write(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})