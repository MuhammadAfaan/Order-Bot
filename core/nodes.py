# core/nodes.py
import json
from collections import defaultdict
from typing import TypedDict, List, Dict, Any, Literal
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import ChatPromptTemplate
from menu.menu_data import MENU
from core.state import ChatState, OrderItem, Message
from langchain_core.output_parsers import StrOutputParser
from datetime import datetime
import random
import csv
import os
from dotenv import load_dotenv

load_dotenv()


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=os.environ.get("GOOGLE_API_KEY")
)

ORDERS_FILE = "orders.csv"

def calculate_total(order_items: List[OrderItem]) -> float:
    """Calculates the total cost of the order based on the menu prices."""
    total = 0.0
    for item_data in order_items:
        price = MENU.get(item_data['item'], {}).get('price', 0)
        total += item_data['quantity'] * price
    return total

def save_order_to_csv(state: ChatState):
    """Save the confirmed order to CSV as a single row with all items grouped."""
    file_exists = os.path.isfile(ORDERS_FILE)

    with open(ORDERS_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Write header if file is new
        if not file_exists:
            writer.writerow([
                "order_number", "user_id", "timestamp", "items", "total_cost", 
                "delivery_address", "status"
            ])

        # Build items string
        items_str = []
        for item in state["order_items"]:
            customizations = f" ({', '.join(item['customizations'])})" if item.get("customizations") else ""
            items_str.append(f"{item['quantity']}x {item['item']}{customizations}")
            
        order_number = random.randint(1000, 9999)

        writer.writerow([
            order_number,
            state["user_id"],
            datetime.now().isoformat(timespec="seconds"),
            "; ".join(items_str),
            state["total_cost"],
            state["delivery_address"],
            state["status"]
        ])


def classify_intent(state: ChatState) -> ChatState:
    """Classifies the user's intent from the last 3 messages of the conversation."""

    if not state["messages"]:
        return state

    # Take last 3 messages (bot + user), join as context
    recent_messages = state["messages"][-6:]  # 3 user+bot exchanges = 6 msgs
    conversation_snippet = "\n".join(
        [f"{m['role']}: {m['content']}" for m in recent_messages]
    )

    status = state["status"].lower()
    menu_sent = "yes" if state.get("menu_sent") else "no"
    is_confirmed = "yes" if state.get("is_confirmed") else "no"
    has_address = "yes" if state.get("delivery_address") else "no"

    parser = JsonOutputParser(pydantic_object=None)
    format_instructions = parser.get_format_instructions()

    system_prompt = f"""
You are an intent classification assistant for a restaurant ordering chatbot.
Classify the conversation into exactly ONE of the following intents, providing a single lowercase string as the value for the 'intent' key:

- greetings
- send_menu
- handle_order
- take_address
- confirm_order
- place_order
- suggest_order
- track_order
- chit_chat
- display_orders

Conversation Flow:
greetings -> send_menu -> handle_order -> take_address -> confirm_order -> place_order -> track_order

Rules:
- If the user is making small talk, asking about the bot, or chatting casually, choose "chit_chat".
- If the user asks about their order status, use "track_order".
- If the user wants to see their current or past orders (e.g., "show me my order", "what did I order?"), choose "display_orders".
- If the user asks for the menu, or is trying to order but hasn't seen the menu yet, choose "send_menu".
- If the user is ordering or modifying food items, choose "handle_order".
- If the user wants recommendations, choose "suggest_order".
- If the user is finishing an order and Address Provided = "no", choose "take_address".
- If the user is finishing an order, Address Provided = "yes" and Is Confirmed = "no", choose "confirm_order".
- If the user is confirming (e.g., "yes", "confirm") AND Is Confirmed = "yes", choose "place_order".

{format_instructions}
"""

    prompt = PromptTemplate.from_template(system_prompt + """
Conversation (last 3 exchanges):
{conversation}

Current Status: {status}
Menu Sent?: {menu_sent}
Is Confirmed?: {is_confirmed}
Address Provided?: {has_address}
""")

    chain = prompt | llm | parser

    try:
        parsed_output = chain.invoke({
            "conversation": conversation_snippet,
            "status": status,
            "menu_sent": menu_sent,
            "is_confirmed": is_confirmed,
            "has_address": has_address
        })
        raw_intent = parsed_output.get("intent", "").lower()
    except Exception as e:
        print(f"[Warning] LLM failed to parse intent: {e}. Defaulting to 'handle_order'.")
        raw_intent = "handle_order"

    valid_intents = {
        "greetings", "send_menu", "handle_order",
        "take_address", "confirm_order", "place_order",
        "suggest_order", "track_order", "chit_chat", "display_orders"
    }

    intent = raw_intent if raw_intent in valid_intents else "handle_order"

    state["intent"] = intent
    print(f"[Debug] Classified Intent: {intent}")
    return state

def display_orders(state: ChatState) -> ChatState:
    """Node: Shows the current user order items."""
    if not state["order_items"]:
        reply = "You don’t have any items in your order yet."
    else:
        items_str = "\n".join([
            f"- {item['quantity']}x {item['item']} ({', '.join(item['customizations']) if item['customizations'] else 'no customizations'})"
            for item in state["order_items"]
        ])
        reply = f"Here’s your current order:\n{items_str}\n\nTotal: ${state['total_cost']:.2f}"

    state["messages"].append({
        "role": "assistant",
        "content": reply
    })
    return state


def suggest_order(state: ChatState) -> ChatState:
    """Node: Suggests items from the menu based on current order and user query."""
    
    order_items = "\n".join([
        f"- {item['quantity']}x {item['item']} ({', '.join(item['customizations']) if item['customizations'] else 'no customizations'})"
        for item in state["order_items"]
    ]) or "No items yet"

    # If you have your menu stored somewhere in state or DB
    menu = "\n".join(
        f"- {item}: ${data['price']:.2f} | {data.get('description', '')}"
        for item, data in MENU.items()
    )

    user_message = state["messages"][-1]["content"]

    prompt = PromptTemplate.from_template("""
You are a helpful restaurant assistant.
The customer has asked for suggestions.

Current Order:
{order_items}

Menu:
{menu}

User Query:
{user_message}

Suggest 2-3 items from the menu that complement their order or answer their request.
""")

    chain = prompt | llm | StrOutputParser()
    suggestion = chain.invoke({
        "order_items": order_items,
        "menu": menu,
        "user_message": user_message
    })

    state["messages"].append({
        "role": "assistant",
        "content": suggestion
    })
    return state


def chit_chat(state: ChatState) -> ChatState:
    """Node: Answers casual user questions about the restaurant."""
    user_message = state["messages"][-1]["content"]

    prompt = PromptTemplate.from_template("""
You are a friendly restaurant assistant.
Answer casual questions about the restaurant, staff, timings, and general chit-chat.

User: {user_message}
Assistant:
""")

    chain = prompt | llm | StrOutputParser()
    reply = chain.invoke({"user_message": user_message})

    state["messages"].append({
        "role": "assistant",
        "content": reply
    })
    return state


def track_order(state: ChatState) -> ChatState:
    """Node: Returns the current order status."""
    status = state.get("status", "not started")

    reply = f"Your order status is: **{status}**."
    state["messages"].append({
        "role": "assistant",
        "content": reply
    })
    return state

def send_menu(state: ChatState) -> ChatState:
    """Sends a formatted menu to the user."""
    categories = defaultdict(list)
    for item_name, item_data in MENU.items():
        category = item_data.get("category", "other").title()
        price = item_data["price"]
        customizations = item_data.get("customizations", [])
        if customizations:
            cust_str = ", ".join(customizations)
            cust_text = f" (Customizations: {cust_str})"
        else:
            cust_text = ""
        categories[category].append(f"- {item_name.replace('_', ' ').title()} — ${price:.2f}{cust_text}")

    menu_lines = ["Here’s our menu:\n"]
    for category in sorted(categories.keys()):
        menu_lines.append(f"🍽 **{category}**")
        menu_lines.extend(categories[category])
        menu_lines.append("")

    menu_text = "\n".join(menu_lines)
    state['messages'].append({"role": "assistant", "content": menu_text})
    state["menu_sent"] = True
    print("[Debug] Menu sent.")
    return state


def handle_order(state: ChatState) -> ChatState:
    """
    Uses the LLM to parse the user's message into structured order data.
    The LLM is given the *current* restaurant menu, the user's current order,
    and must output JSON with a list of items + a bot message.
    """
    if not state["messages"]:
        return state

    user_message = state["messages"][-1]
    state['is_confirmed'] = False  # Reset confirmation state for new order handling

    # Menu string for LLM
    menu_str = "\n".join(
        f"- {item}: ${data['price']:.2f} | {data.get('description', '')}"
        for item, data in MENU.items()
    )

    # Current order string for LLM
    current_order_str = "\n".join(
        f"- {o['item']} (x{o['quantity']})" for o in state["order_items"]
    ) if state["order_items"] else "None"

    # System prompt (all JSON braces escaped {{ }})
    system_prompt = f"""
You are an expert restaurant ordering assistant.

The current restaurant menu is:
{menu_str}

The customer's current order is:
{current_order_str}

Rules:
- Analyze the user's message carefully.
- Always output valid JSON with exactly two keys:
  {{
    "items": [
      {{
        "action": "add" | "remove" | "update",
        "item": "string",
        "quantity": int,
        "customizations": ["string", ...]
      }}
    ],
    "bot_message": "string"
  }}
- Only include items that exist in the menu.
- If a mentioned item is NOT in the menu, do NOT include it in "items", but mention it in "bot_message".
- For "remove" and "update", only include items that exist in the customer's current order.
  If not, just mention the issue in "bot_message".
- If quantity is not mentioned, default to 1.
- "bot_message" should summarize all valid actions and also mention invalid requests.
- Write the bot_message in the same language as the user (English, Roman Urdu, etc).
""".replace("{", "{{").replace("}", "}}")  # <-- escapes all braces

    # ChatPromptTemplate with escaped braces
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "User Message: {message}")
    ])

    chain = prompt | llm | (lambda x: x.content.strip())
    raw_response = chain.invoke({"message": user_message})

    print(f"[Debug] Raw LLM Order Parse: {raw_response}")

    clean_response = raw_response.strip()
    if clean_response.startswith("```"):
    # remove triple backticks and optional "json"
      clean_response = clean_response.strip("`").replace("json", "", 1).strip()

    try:
        parsed = json.loads(clean_response)
    except json.JSONDecodeError:
        state["messages"].append({
            "role": "assistant",
            "content": "Sorry, I couldn't understand your order. Could you please repeat it clearly?"
        })
        return state

    items = parsed.get("items", [])
    bot_message = parsed.get("bot_message", "Okay, got it!")

    # --- Apply changes only for valid items ---
    for change in items:
        action = change.get("action", "").lower()
        item = change.get("item", "").strip()
        quantity = change.get("quantity", 1)
        customizations = change.get("customizations", [])

        # Validate against menu
        if not item or item not in MENU:
            continue  # leave explanation to bot_message

        existing_item = next((o for o in state["order_items"] if o["item"].lower() == item.lower()), None)

        if action == "add":
            if existing_item:
                existing_item["quantity"] += quantity
                existing_item["customizations"].extend(customizations)
            else:
                state["order_items"].append({
                    "item": item,
                    "quantity": quantity,
                    "customizations": customizations
                })

        elif action == "update":
            if existing_item:
                existing_item["quantity"] = quantity
                existing_item["customizations"] = customizations
            # else ignore, bot_message should cover this

        elif action == "remove":
            if existing_item:
                existing_item["quantity"] -= quantity
                if existing_item["quantity"] <= 0:
                    state["order_items"].remove(existing_item)
            # else ignore, bot_message should cover this

    # --- Recalculate total ---
    state["total_cost"] = calculate_total(state["order_items"])

    # --- Add assistant reply ---
    state["messages"].append({
        "role": "assistant",
        "content": bot_message
    })

    return state


def take_address(state: ChatState) -> ChatState:
    """
    Uses the LLM to extract and validate the user's delivery address for a Pakistani context.
    The LLM now outputs a boolean for validation and the final address string.
    """
    if not state["messages"]:
        return state

    user_message = state["messages"][-1]["content"].strip()

    # The prompt is updated to be more flexible for Pakistani addresses
    # and to explicitly request a boolean `address_valid` in the output.
    system_prompt = f"""
You are a restaurant delivery assistant. Your task is to extract a complete delivery address from the user's message.
A complete Pakistani address might include a street name, house or apartment number, or a nearby landmark. You do not need to look for a state or city.

Rules:
- Always output *only* valid JSON with the keys `final_address` and `address_valid`.
- If a complete address is found, set `address_valid` to `true` and provide the address under `final_address`.
- If the address is vague or incomplete (e.g., "my home"), set `address_valid` to `false` and set `final_address` to an empty string.
"""
    # The prompt template is updated to use double braces for the JSON structure
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "User Message: {message}")
    ])
    
    chain = prompt | llm | (lambda x: x.content.strip())
    raw_response = chain.invoke({"message": user_message})
    print(f"[DEBUG] LLM Raw Response for Address: {raw_response}")

    try:
        # Clean and parse the JSON output from the LLM
        clean_response = raw_response.strip().strip("`").replace("json", "", 1).strip()
        parsed = json.loads(clean_response)

        # Extract the new `final_address` and `address_valid` fields
        final_address = parsed.get("final_address", "").strip()
        address_is_valid = parsed.get("address_valid", False)
        
        # Check the address_is_valid boolean to update the state
        if address_is_valid:
            state['delivery_address'] = final_address
            state['messages'].append({
                "role": "assistant",
                "content": (
                    f"Got it! Your address is recorded as: {final_address}. "
                    "Do you want to confirm the order or change anything else?"
                )
            })
            state['address_valid'] = True
            state['status'] = "awaiting_confirmation"
        else:
            state['messages'].append({
                "role": "assistant",
                "content": "I couldn't get a full address. Can you please provide your house number and street name?"
            })
            state['address_valid'] = False

    except json.JSONDecodeError:
        state['messages'].append({
            "role": "assistant",
            "content": "Sorry, I had trouble processing that. Can you please provide your address again?"
        })
        state['address_valid'] = False

    return state

def confirm_order(state: ChatState) -> ChatState:
    """Summarizes the order for confirmation."""
    order_summary = "\n".join([f"- {o['item']} (x{o['quantity']})" for o in state['order_items']])
    
    response_message = (
        f"Here is your final order:\n"
        f"Items:\n{order_summary}\n"
        f"Total: ${state['total_cost']:.2f}\n"
        f"Delivering to: {state['delivery_address']}\n"
        f"Please confirm to place your order."
    )

    state['messages'].append({"role": "assistant", "content": response_message})
    state['is_confirmed'] = True # Reset for user confirmation
    print("Processed Confirm Order.")
    return state

def place_order(state: ChatState) -> ChatState:
    """Simulates placing the order and provides confirmation."""
    response_message = "Thank you! Your order has been placed successfully."
    state['messages'].append({"role": "assistant", "content": response_message})
    state['status'] = "completed"
    save_order_to_csv(state)
    print("Processed Place Order.")
    return state

def greetings(state: ChatState) -> ChatState:
    """Greets the user and asks for their intent."""
    message = 'What would you like to do?\n1) Order\n2) Track'
    state['messages'].append({"role": "assistant", "content": message})
    state['status'] = 'greeted'
    return state

def router_func(state: ChatState) -> str:
    """A simple router that returns the last classified intent."""
    return state["intent"]