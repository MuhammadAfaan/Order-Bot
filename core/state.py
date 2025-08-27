# core/state.py
from typing import TypedDict, List, Literal

# Message Types
class Message(TypedDict):
    """
    Represents a single message in the conversation.
    """
    role: Literal["user", "assistant"]
    content: str

# Order Item Structure
class OrderItem(TypedDict):
    """
    Represents a single item in the user's order.
    """
    item: str
    quantity: int
    customizations: List[str]

# Conversation State
class ChatState(TypedDict):
    """
    The state object for the LangGraph chatbot.
    It holds all the necessary information to manage the conversation.
    """
    user_id: str
    messages: List[Message]
    order_items: List[OrderItem]
    total_cost: float
    delivery_address: str
    status: str
    intent: str
    menu_sent: bool
    address_valid: bool
    is_confirmed: bool
