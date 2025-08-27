# app.py
import os
import sys
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from core.state import ChatState
from core.nodes import (
    classify_intent,
    send_menu,
    handle_order,
    take_address,
    confirm_order,
    place_order,
    greetings,
    router_func,
    display_orders,
    suggest_order,
    chit_chat,
    track_order
)

# Function to create a new initial state for a user
def create_initial_state(user_id: str) -> ChatState:
    """Initializes the chatbot state for a new user session."""
    return {
        "user_id": user_id,
        "messages": [],
        "order_items": [],
        "total_cost": 0.0,
        "delivery_address": None,
        "status": "idle",
        "intent": "greetings",
        "menu_sent": False,
        "address_valid": False,
        "is_confirmed": False
    }

# Build the LangGraph
def build_graph(llm=None):
    """Builds and compiles the LangGraph for the chatbot."""
    builder = StateGraph(ChatState)

    # Core nodes
    builder.add_node("classify_intent", classify_intent)
    builder.add_node("greetings", greetings)
    builder.add_node("send_menu", send_menu)
    builder.add_node("handle_order", handle_order)
    builder.add_node("take_address", take_address)
    builder.add_node("confirm_order", confirm_order)
    builder.add_node("place_order", place_order)

    # New nodes
    builder.add_node("display_orders", display_orders)
    builder.add_node("suggest_order", suggest_order)
    builder.add_node("chit_chat", chit_chat)
    builder.add_node("track_order", track_order)

    # Entry point
    builder.set_entry_point("classify_intent")

    # Router decides where to go based on intent
    builder.add_conditional_edges(
        "classify_intent",
        router_func,
        {
            "greetings": "greetings",
            "send_menu": "send_menu",
            "handle_order": "handle_order",
            "take_address": "take_address",
            "confirm_order": "confirm_order",
            "place_order": "place_order",
            "display_orders": "display_orders",
            "suggest_order": "suggest_order",
            "chit_chat": "chit_chat",
            "track_order": "track_order"
        }
    )
    
    # Define edges between nodes (default: return to END after each response)
    builder.add_edge("greetings", END)
    builder.add_edge("send_menu", END)
    builder.add_edge("handle_order", END)
    builder.add_edge("take_address", END)
    builder.add_edge("confirm_order", END)
    builder.add_edge("place_order", END)
    builder.add_edge("display_orders", END)
    builder.add_edge("suggest_order", END)
    builder.add_edge("chit_chat", END)
    builder.add_edge("track_order", END)

    return builder.compile()