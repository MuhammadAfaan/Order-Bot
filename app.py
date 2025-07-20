import streamlit as st
import os
from dotenv import load_dotenv
from backend.langchain_agent import create_agent
from backend.memory_store import memory_store
from backend.order_logger import order_logger

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="🍽️ Restaurant Order Bot",
    page_icon="🍽️",
    layout="centered"
)

# Initialize session state
if 'user_id' not in st.session_state:
    import time
    st.session_state.user_id = f"user_{int(time.time())}"

if 'messages' not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "🍽️ Welcome to our restaurant! I'm here to help you place your order. Would you like to see our menu?"}
    ]

if 'agent_error' not in st.session_state:
    st.session_state.agent_error = None

# Initialize agent with better error handling
if 'agent' not in st.session_state:
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        st.error("⚠️ GROQ_API_KEY not found in environment variables.")
        st.info("Please add your Groq API key to a .env file: `GROQ_API_KEY=your_key_here`")
        st.info("Get your API key from: https://console.groq.com/")
        st.stop()
    
    try:
        with st.spinner("Initializing restaurant assistant..."):
            st.session_state.agent = create_agent(groq_api_key)
            st.success("✅ Assistant ready!")
            st.session_state.agent_error = None
    except Exception as e:
        st.session_state.agent_error = str(e)
        st.error(f"❌ Failed to initialize assistant: {e}")
        st.info("Try refreshing the page or check your API key.")

# Show agent error if exists
if st.session_state.agent_error:
    st.error(f"Assistant Error: {st.session_state.agent_error}")
    if st.button("🔄 Retry Initialization"):
        st.session_state.agent_error = None
        if 'agent' in st.session_state:
            del st.session_state.agent
        st.rerun()

# Sidebar with user info and order status
with st.sidebar:
    st.header("🔧 Order Status")
    
    user_state = memory_store.get_user_state(st.session_state.user_id)
    
    st.write(f"**User ID:** {st.session_state.user_id}")
    st.write(f"**Context:** {user_state.get('context', 'ordering')}")
    st.write(f"**Order Total:** ${user_state.get('order_total', 0.0):.2f}")
    st.write(f"**Confirmed:** {'✅' if user_state.get('order_confirmed') else '❌'}")
    
    if user_state.get('current_order'):
        st.write("**Current Order:**")
        for item, qty in user_state['current_order'].items():
            st.write(f"• {qty}x {item}")
    
    # Clear order button
    if st.button("🗑️ Clear Order"):
        memory_store.clear_user_order(st.session_state.user_id)
        st.rerun()
    
    # Show order history
    st.header("📋 Order History")
    try:
        history_df = order_logger.get_order_history(st.session_state.user_id)
        if not history_df.empty:
            for _, order in history_df.iterrows():
                st.write(f"**{order['order_id']}**")
                st.write(f"Total: ${order['total']:.2f}")
                st.write(f"Status: {order['status']}")
                st.write("---")
        else:
            st.write("No order history")
    except Exception as e:
        st.write(f"Error loading history: {e}")

# Main chat interface
st.title("🍽️ Restaurant Order Bot")
st.caption("Natural language ordering powered by LangChain + LLaMA 3")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Chat input
if prompt := st.chat_input("Type your order or ask about the menu..."):
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
    
    # Get bot response
    with st.chat_message("assistant"):
        if st.session_state.agent_error:
            st.error("Assistant is not available. Please refresh the page.")
        else:
            with st.spinner("Processing your request..."):
                try:
                    response = st.session_state.agent.process_message(st.session_state.user_id, prompt)
                    st.write(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = "I'm experiencing technical difficulties. Let me try to help you directly!"
                    
                    # Provide fallback responses
                    prompt_lower = prompt.lower()
                    if any(word in prompt_lower for word in ['menu', 'food', 'what do you have']):
                        from backend.menu import get_full_menu
                        error_msg = get_full_menu()
                    elif 'hi' in prompt_lower or 'hello' in prompt_lower:
                        error_msg = "Hello! Welcome to our restaurant! 🍽️ Would you like to see our menu?"
                    
                    st.write(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    print(f"Error processing message: {e}")
    
    # Refresh sidebar
    st.rerun()

# Instructions
with st.expander("ℹ️ How to use"):
    st.markdown("""
    **Natural Language Examples:**
    - "Show me the menu"
    - "Add 2 biryani and 3 cokes to my order"
    - "Change the fries to 2 pieces"
    - "Remove 1 coke from my order"
    - "What's in my order?"
    - "I want to confirm my order"
    
    **Features:**
    - ✅ Natural language understanding
    - ✅ Order modifications
    - ✅ Customer info collection
    - ✅ Order confirmation & logging
    - ✅ Persistent user state
    """)

# Footer
st.markdown("---")
st.markdown("🤖 Powered by **LangChain** + **LLaMA 3** + **Groq API**")