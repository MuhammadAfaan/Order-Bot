import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_menu():
    """Test menu functionality"""
    print("=== TESTING MENU ===")
    from backend.menu import get_full_menu, find_menu_item
    
    print(get_full_menu())
    
    # Test item finding
    item, category = find_menu_item("biryani")
    print(f"Found: {item}, Category: {category}")
    

def test_tools():
    """Test tools functionality"""
    print("\n=== TESTING TOOLS ===")
    from backend.tools import show_menu_tool, manage_order_tool
    import json
    
    # Test menu tool
    print("Menu Tool:")
    print(show_menu_tool(""))
    
    # Test order tool
    print("\nOrder Tool:")
    order_input = {
        "user_id": "test_user",
        "items": {"biryani": 2, "coke": 3},
        "action": "add"
    }
    result = manage_order_tool(json.dumps(order_input))
    print(result)

def test_memory():
    """Test memory store"""
    print("\n=== TESTING MEMORY ===")
    from backend.memory_store import memory_store
    
    # Test user state
    state = memory_store.get_user_state("test_user")
    print(f"Initial state: {state}")
    
    # Update state
    memory_store.update_user_state("test_user", {"order_total": 25.99})
    updated_state = memory_store.get_user_state("test_user")
    print(f"Updated state: {updated_state}")

def test_simple_agent():
    """Test basic agent functionality"""
    print("\n=== TESTING SIMPLE RESPONSES ===")
    
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        print("❌ No GROQ_API_KEY found")
        return
    
    try:
        from backend.langchain_agent import create_agent
        agent = create_agent(groq_api_key)
        
        # Test simple greeting
        response = agent.process_message("test_user", "hi")
        print(f"Greeting response: {response}")
        
        # Test menu request
        response = agent.process_message("test_user", "show me the menu")
        print(f"Menu response: {response[:200]}...")
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_menu()
    test_tools()
    test_memory()
    test_simple_agent()