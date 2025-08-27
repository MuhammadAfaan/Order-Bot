import streamlit as st
import pandas as pd
import os
from app import build_graph, create_initial_state  # your LangGraph code

ORDERS_FILE = "orders.csv"

# ---- Streamlit Setup ----
st.set_page_config(page_title="🍽 Restaurant Chatbot", layout="wide")
st.markdown("<h1 style='text-align:center; color:#d35400;'>🍽 Restaurant Ordering Assistant</h1>", unsafe_allow_html=True)
st.markdown("---")

# ---- User Login ----
if "user_id" not in st.session_state:
    st.session_state.user_id = None

if not st.session_state.user_id:
    st.markdown("### 🔑 Login to start your order")
    user_id = st.text_input("Enter your User ID:", key="login_input")
    if st.button("🚀 Start Chat", key="login_btn") and user_id.strip():
        st.session_state.user_id = user_id.strip()
        st.session_state.graph = build_graph()
        st.session_state.state = create_initial_state(st.session_state.user_id)
        st.session_state.messages = []
        st.rerun()
    st.stop()  # Prevent rest of app until login

# ---- Navigation ----
page = st.sidebar.radio("📍 Navigate", ["💬 Chat", "📜 Orders"])

# ---- Chat Page ----
if page == "💬 Chat":
    st.markdown("### 💬 Chat with Assistant")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Type your message..."):
        st.session_state.state["messages"].append({"role": "user", "content": user_input})
        st.session_state.messages.append({"role": "user", "content": user_input})

        st.session_state.state = st.session_state.graph.invoke(st.session_state.state)

        if st.session_state.state["messages"]:
            last_bot_message = st.session_state.state["messages"][-1]
            if last_bot_message["role"] == "assistant":
                st.session_state.messages.append(last_bot_message)

        st.rerun()

# ---- Orders Page ----
elif page == "📜 Orders":
    st.markdown("### 📜 Orders Dashboard")
    tabs = st.tabs(["👤 My Orders", "🌍 All Orders"])

    with tabs[0]:
        if os.path.exists(ORDERS_FILE):
            df = pd.read_csv(ORDERS_FILE).sort_values(by="timestamp", ascending=False)
            user_orders = df[df["user_id"].astype(str) == str(st.session_state.user_id)]
            if not user_orders.empty:
                st.dataframe(user_orders, use_container_width=True, hide_index=True)
            else:
                st.info("You have no orders yet.")
        else:
            st.info("No orders found yet.")

    with tabs[1]:
        if os.path.exists(ORDERS_FILE):
            df = pd.read_csv(ORDERS_FILE).sort_values(by="timestamp", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.download_button(
                label="📥 Download All Orders (CSV)",
                data=df.to_csv(index=False),
                file_name="all_orders.csv",
                mime="text/csv",
            )
        else:
            st.info("No orders found yet.")
