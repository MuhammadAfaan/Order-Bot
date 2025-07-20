# backend/langchain_agent.py

from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain.agents import Tool, initialize_agent
from langchain.agents.agent_types import AgentType
from langchain.memory import ConversationBufferMemory
import os

from backend.menu import flat_menu_items, get_menu_string, calculate_total
from backend.order_logger import log_order

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model_name="llama3-8b-8192"
)

system_prompt = """You are a helpful and polite AI assistant that works at a restaurant.
Your job is to:
- Show the menu when asked
- Take orders only from the items in the menu
- Confirm orders
- Be short, clear, and friendly in responses
Avoid discussing anything that is not related to the restaurant or food ordering."""

memory = ConversationBufferMemory(return_messages=True)

user_orders = {}

# Tool: Show menu
def show_menu(_):
    return "Here’s our menu:\n" + get_menu_string()

# Tool: Add items to order
def add_to_order(user_id_and_message):
    user_id, message = user_id_and_message.split("|", 1)
    items = [item for item in flat_menu_items if item in message.lower()]
    if not items:
        return "I couldn't find any menu items in your message."
    user_orders.setdefault(user_id, []).extend(items)
    return f"📝 Added to your order: {', '.join(items)}.\nReply 'confirm' to place the order or add more."

# Tool: Remove items from order
def remove_from_order(user_id_and_message):
    user_id, message = user_id_and_message.split("|", 1)
    current = user_orders.get(user_id, [])
    to_remove = [item for item in current if item in message.lower()]
    if not to_remove:
        return "No matching items found in your current order to remove."
    user_orders[user_id] = [i for i in current if i not in to_remove]
    return f"❌ Removed: {', '.join(to_remove)}.\nYour current order: {', '.join(user_orders[user_id]) or 'Empty'}"

# Tool: Confirm order
def confirm_order(user_id):
    items = user_orders.get(user_id, [])
    if not items:
        return "🚫 You haven't ordered anything yet."
    total = calculate_total(items)
    delivery_fee = 100
    grand_total = total + delivery_fee
    log_order(user_id, ", ".join(items))
    user_orders[user_id] = []
    return f"✅ Your order for: {', '.join(items)} has been placed!\nSubtotal: Rs. {total}\nDelivery: Rs. {delivery_fee}\nTotal: Rs. {grand_total}"

# Tools
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationChain

def get_chain():
    prompt = PromptTemplate(
        input_variables=["input", "history"],
        template="{system_prompt}\n\nConversation history:\n{history}\nUser: {input}\nAI:"
    ).partial(system_prompt=system_prompt)

    return ConversationChain(
        llm=llm,
        memory=memory,
        prompt=prompt
    )

tools = [
    Tool(
        name="ShowMenu",
        func=show_menu,
        description=(
            "Use this tool when user asks for menu, food list, options, items, prices, or says things like 'menu', "
            "'show menu', 'see items', 'what can I order', etc."
        )
    ),
    Tool(
        name="AddToOrder",
        func=add_to_order,
        description="Use when user wants to order or add food items like burger, fries, coke, etc."
    ),
    Tool(
        name="RemoveFromOrder",
        func=remove_from_order,
        description="Use when user wants to remove or cancel specific items from their order."
    ),
    Tool(
        name="ConfirmOrder",
        func=confirm_order,
        description="Use when user wants to confirm, finalize, or place the order."
    ),
]


agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    memory=memory,
    verbose=False
)

def handle_user_message(user_id, message):
    try:
        return agent.run(f"{user_id}|{message}")
    except Exception as e:
        return f"⚠️ Error: {str(e)}"