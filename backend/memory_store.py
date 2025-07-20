from typing import Dict, Any, List
import copy

class UserMemoryStore:
    def __init__(self):
        self.user_states: Dict[str, Dict[str, Any]] = {}
    
    def get_user_state(self, user_id: str) -> Dict[str, Any]:
        """Get user state, create if doesn't exist"""
        if user_id not in self.user_states:
            self.user_states[user_id] = {
                "current_order": {},  # {item_name: quantity}
                "order_confirmed": False,
                "customer_info": {},
                "order_total": 0.0,
                "order_history": [],
                "context": "ordering"  # ordering, confirming, completed
            }
        return self.user_states[user_id]
    
    def update_user_state(self, user_id: str, updates: Dict[str, Any]):
        """Update specific fields in user state"""
        state = self.get_user_state(user_id)
        state.update(updates)
    
    def clear_user_order(self, user_id: str):
        """Clear current order but keep user info"""
        state = self.get_user_state(user_id)
        state.update({
            "current_order": {},
            "order_confirmed": False,
            "order_total": 0.0,
            "context": "ordering"
        })
    
    def get_state_summary(self, user_id: str) -> str:
        """Get formatted state summary for LLM context"""
        state = self.get_user_state(user_id)
        
        summary = f"USER STATE:\n"
        summary += f"Context: {state['context']}\n"
        summary += f"Order Confirmed: {state['order_confirmed']}\n"
        summary += f"Current Order Total: ${state['order_total']:.2f}\n"
        
        if state['current_order']:
            summary += "Current Order Items:\n"
            for item, qty in state['current_order'].items():
                summary += f"  - {item}: {qty}\n"
        else:
            summary += "Current Order: Empty\n"
        
        if state['customer_info']:
            summary += f"Customer Info: {state['customer_info']}\n"
        
        return summary

# Global memory store instance
memory_store = UserMemoryStore()