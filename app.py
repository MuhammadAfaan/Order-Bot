# app.py

import streamlit as st
from backend.langchain_agent import handle_user_message
import streamlit as st
from backend.langchain_agent import handle_user_message
import traceback


st.set_page_config(page_title="🍟 Restaurant Order Bot", layout="centered")

st.title("🍟 Restaurant Order Bot")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_id" not in st.session_state:
    st.session_state.user_id = "guest"  # You can set unique IDs if needed

# Chat input
user_input = st.chat_input("Say something...")

# Initial welcome message
if len(st.session_state.chat_history) == 0:
    st.session_state.chat_history.append(("bot", "Hello! What would you like to order? Type 'menu' to see available items."))

# Show chat history
for role, message in st.session_state.chat_history:
    with st.chat_message(role):
        st.markdown(message)

# Process user message
if user_input:
    st.session_state.chat_history.append(("user", user_input))
    with st.chat_message("user"):
        st.markdown(user_input)

    response = handle_user_message(st.session_state.user_id, user_input)

    st.session_state.chat_history.append(("bot", response))
    with st.chat_message("bot"):
        st.markdown(response)
