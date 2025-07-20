from langchain.tools import Tool
from langchain.pydantic_v1 import BaseModel, Field
from typing import Dict, Any, List
import json
from .menu import get_full_menu, find_menu_item, get_item_price
from .memory_store import memory_store
from .order_logger import order_logger

class OrderInput(BaseModel):
    user_id: str = Field(description="User identifier")
    items: Dict[str, int] = Field(description="Items to add/modify with quantities")
    action: str = Field(description="Action: 'add', 'remove', 'modify', or 'clear'")

class CustomerInfoInput(BaseModel):
    user_id: str = Field(description="User identifier")
    name: str = Field(description="Customer name", default="")
    phone: str = Field(description="Customer phone", default="")
    address: str = Field(description="Customer address", default="")

def show_menu_tool(input_str: str) -> str:
    """Show the restaurant menu"""
    return get_full_menu()

def manage_order_tool(input_str: str) -> str:
    """Add, modify, or remove items from order"""
    try:
        # Parse input - expect JSON string
        data = json.loads(input_str) if isinstance(input_str, str) else input_str
        user_id = data.get('user_id')
        items = data.get('items', {})
        action = data.get('action', 'add').lower()
        
        state = memory_store.get_user_state(user_id)
        current_order = state['current_order'].copy()
        
        result_messages = []
        
        for item_name, quantity in items.items():
            menu_item, category = find_menu_item(item_name)
            
            if not menu_item:
                result_messages.append(f"❌ '{item_name}' not found in menu.")
                continue
            
            item_key = item_name.lower()
            
            if action == 'add':
                current_order[item_key] = current_order.get(item_key, 0) + quantity
                result_messages.append(f"✅ Added {quantity}x {menu_item['name']}")
            
            elif action == 'modify':
                if item_key in current_order:
                    current_order[item_key] = quantity
                    result_messages.append(f"✅ Modified {menu_item['name']} quantity to {quantity}")
                else:
                    result_messages.append(f"❌ {menu_item['name']} not in current order")
            
            elif action == 'remove':
                if item_key in current_order:
                    if current_order[item_key] <= quantity:
                        del current_order[item_key]
                        result_messages.append(f"✅ Removed {menu_item['name']} from order")
                    else:
                        current_order[item_key] -= quantity
                        result_messages.append(f"✅ Removed {quantity}x {menu_item['name']}")
                else:
                    result_messages.append(f"❌ {menu_item['name']} not in current order")
        
        if action == 'clear':
            current_order = {}
            result_messages.append("🗑️ Cleared entire order")
        
        # Calculate new total
        total = 0.0
        for item_name, qty in current_order.items():
            price = get_item_price(item_name)
            total += price * qty
        
        # Update state
        memory_store.update_user_state(user_id, {
            'current_order': current_order,
            'order_total': total
        })
        
        # Format current order
        order_summary = "\n**CURRENT ORDER:**\n"
        if current_order:
            for item_name, qty in current_order.items():
                menu_item, _ = find_menu_item(item_name)
                if menu_item:
                    order_summary += f"• {qty}x {menu_item['name']} - ${menu_item['price']:.2f} each\n"
            order_summary += f"\n**TOTAL: ${total:.2f}**"
        else:
            order_summary += "Empty"
        
        return "\n".join(result_messages) + "\n" + order_summary
        
    except Exception as e:
        return f"Error managing order: {str(e)}"

def collect_customer_info_tool(input_str: str) -> str:
    """Collect customer information"""
    try:
        data = json.loads(input_str) if isinstance(input_str, str) else input_str
        user_id = data.get('user_id')
        name = data.get('name', '')
        phone = data.get('phone', '')
        address = data.get('address', '')
        
        customer_info = {}
        if name:
            customer_info['name'] = name
        if phone:
            customer_info['phone'] = phone
        if address:
            customer_info['address'] = address
        
        memory_store.update_user_state(user_id, {
            'customer_info': customer_info,
            'context': 'confirming'
        })
        
        return f"✅ Customer information collected: {customer_info}"
        
    except Exception as e:
        return f"Error collecting customer info: {str(e)}"

def confirm_order_tool(input_str: str) -> str:
    """Confirm and log the order"""
    try:
        data = json.loads(input_str) if isinstance(input_str, str) else input_str
        user_id = data.get('user_id')
        
        state = memory_store.get_user_state(user_id)
        
        if not state['current_order']:
            return "❌ Cannot confirm empty order"
        
        # Log the order
        order_id = order_logger.log_order(user_id, state)
        
        if order_id:
            # Update state
            memory_store.update_user_state(user_id, {
                'order_confirmed': True,
                'context': 'completed'
            })
            
            return f"🎉 ORDER CONFIRMED!\nOrder ID: {order_id}\nTotal: ${state['order_total']:.2f}\nEstimated delivery: 25-35 minutes"
        else:
            return "❌ Error confirming order. Please try again."
            
    except Exception as e:
        return f"Error confirming order: {str(e)}"

def get_order_status_tool(input_str: str) -> str:
    """Get current order status and summary"""
    try:
        data = json.loads(input_str) if isinstance(input_str, str) else input_str
        user_id = data.get('user_id')
        
        state = memory_store.get_user_state(user_id)
        
        if state['order_confirmed']:
            return f"✅ Your order is confirmed! Total: ${state['order_total']:.2f}"
        elif state['current_order']:
            order_summary = "📋 **CURRENT ORDER STATUS:**\n"
            for item_name, qty in state['current_order'].items():
                menu_item, _ = find_menu_item(item_name)
                if menu_item:
                    order_summary += f"• {qty}x {menu_item['name']} - ${menu_item['price']:.2f}\n"
            order_summary += f"\n**TOTAL: ${state['order_total']:.2f}**\n"
            order_summary += "Status: Pending confirmation"
            return order_summary
        else:
            return "📋 No current order. Would you like to see our menu?"
    
    except Exception as e:
        return f"Error getting order status: {str(e)}"

# Define tools
tools = [
    Tool(
        name="show_menu",
        description="Show the restaurant menu to the customer",
        func=show_menu_tool
    ),
    Tool(
        name="manage_order",
        description="Add, modify, remove items from order. Input should be JSON with 'user_id', 'items' dict, and 'action' ('add'/'modify'/'remove'/'clear')",
        func=manage_order_tool
    ),
    Tool(
        name="collect_customer_info",
        description="Collect customer information (name, phone, address). Input should be JSON with 'user_id' and info fields",
        func=collect_customer_info_tool
    ),
    Tool(
        name="confirm_order",
        description="Confirm and log the final order. Input should be JSON with 'user_id'",
        func=confirm_order_tool
    ),
    Tool(
        name="get_order_status",
        description="Get current order status and summary. Input should be JSON with 'user_id'",
        func=get_order_status_tool
    )
]