import os
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage
from .tools import tools
from .memory_store import memory_store

class RestaurantAgent:
    def __init__(self, groq_api_key: str):
        # Initialize LLM
        self.llm = ChatGroq(
            groq_api_key=groq_api_key,
            model_name="llama3-70b-8192",  # or "llama3-8b-8192" for faster responses
            temperature=0.1
        )
        
        # Create prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}\n\nUser State:\n{user_state}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create agent
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=tools,
            prompt=self.prompt
        )
        
        # Create executor
        self.executor = AgentExecutor(
            agent=self.agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )
        
        # Chat histories for each user
        self.chat_histories = {}
    
    def _get_system_prompt(self) -> str:
        return """You are a friendly and efficient restaurant order-taking assistant. Your job is to help customers place orders.

IMPORTANT RULES:
1. **Only use tools when necessary** - Don't call tools for simple greetings or questions
2. **Call tools ONCE per user message** when needed, passing ALL relevant data at once
3. **Natural conversation** - Be conversational and helpful, not robotic
4. **Order management** - Help with adding, modifying, removing items
5. **Process flow**: Menu → Order → Customer Info → Confirmation

KEY BEHAVIORS:
- Greet customers warmly and offer to show the menu
- Parse natural language like "2 biryani and 3 cokes" into structured data
- Handle modifications: "change fries to 2", "remove 1 coke"
- Ask for customer info (name, phone, address) before confirming
- Always show order summary after changes
- Be proactive in guiding the customer through the process

TOOL USAGE:
- Use "show_menu" when customer wants to see menu
- Use "manage_order" for adding/modifying/removing items (pass JSON: {"user_id": "...", "items": {"item_name": quantity}, "action": "add/modify/remove"})
- Use "collect_customer_info" when collecting customer details
- Use "confirm_order" to finalize the order
- Use "get_order_status" to check current order

Remember: Be helpful, natural, and efficient. Guide customers smoothly from browsing to ordering to confirmation."""

    def get_chat_history(self, user_id: str) -> list:
        """Get chat history for user"""
        if user_id not in self.chat_histories:
            self.chat_histories[user_id] = []
        return self.chat_histories[user_id]
    
    def add_to_chat_history(self, user_id: str, message, response):
        """Add message exchange to chat history"""
        history = self.get_chat_history(user_id)
        history.append(HumanMessage(content=message))
        history.append(AIMessage(content=response))
        
        # Keep last 20 messages to avoid context overflow
        if len(history) > 20:
            self.chat_histories[user_id] = history[-20:]
    
    def process_message(self, user_id: str, message: str) -> str:
        """Process user message and return response"""
        try:
            # Get user state and chat history
            user_state = memory_store.get_state_summary(user_id)
            chat_history = self.get_chat_history(user_id)
            
            # Execute agent
            result = self.executor.invoke({
                "input": message,
                "user_state": user_state,
                "chat_history": chat_history
            })
            
            response = result.get("output", "I apologize, but I couldn't process your request. Please try again.")
            
            # Add to chat history
            self.add_to_chat_history(user_id, message, response)
            
            return response
            
        except Exception as e:
            error_msg = f"I apologize for the technical difficulty. Please try rephrasing your request."
            print(f"Agent error: {e}")
            return error_msg

def create_agent(groq_api_key: str) -> RestaurantAgent:
    """Factory function to create agent"""
    return RestaurantAgent(groq_api_key)