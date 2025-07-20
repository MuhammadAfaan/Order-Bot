from langchain.tools import tool
from backend.menu import get_menu_string, flat_menu_items
from backend.memory_store import get_user_state

@tool
def show_menu_tool() -> str:
    """Show the restaurant menu."""
    return get_menu_string()

@tool
def add_to_order_tool(user_id: str, item: str) -> str:
    """Add an item to the user's order."""
    item = item.lower()
    if item not in flat_menu_items:
        return f"❌ Item '{item}' not on the menu."
    state = get_user_state(user_id)
    state["items"].append(item)
    state["confirmed"] = False
    return f"✅ Added '{item}' to your order."

@tool
def remove_from_order_tool(user_id: str, item: str) -> str:
    """Remove an item from the user's order."""
    state = get_user_state(user_id)
    try:
        state["items"].remove(item.lower())
        return f"🗑️ Removed '{item}' from your order."
    except ValueError:
        return f"⚠️ '{item}' not found in your current order."

@tool
def confirm_order_tool(user_id: str) -> str:
    """Confirm the user's current order."""
    state = get_user_state(user_id)
    if not state["items"]:
        return "Your order is empty."
    state["confirmed"] = True
    items = ", ".join(state["items"])
    return f"✅ Order confirmed for: {items}."

@tool
def collect_details_tool(user_id: str, address: str, phone: str) -> str:
    """Collect address and phone number from the user."""
    state = get_user_state(user_id)
    state["address"] = address
    state["phone"] = phone
    return f"📍 Address and 📞 phone saved."

@tool
def view_current_order_tool(user_id: str) -> str:
    """View current order for the user."""
    state = get_user_state(user_id)
    if not state["items"]:
        return "Your order is currently empty."
    return f"🧾 Your order: {', '.join(state['items'])}"
