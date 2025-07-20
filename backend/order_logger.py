import pandas as pd
import os
from datetime import datetime
from typing import Dict, Any

class OrderLogger:
    def __init__(self, csv_path: str = "data/orders.csv"):
        self.csv_path = csv_path
        self.ensure_data_dir()
        self.ensure_csv_exists()
    
    def ensure_data_dir(self):
        """Create data directory if it doesn't exist"""
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
    
    def ensure_csv_exists(self):
        """Create CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.csv_path):
            df = pd.DataFrame(columns=[
                'order_id', 'timestamp', 'user_id', 'items', 
                'total', 'customer_info', 'status'
            ])
            df.to_csv(self.csv_path, index=False)
    
    def log_order(self, user_id: str, order_data: Dict[str, Any]) -> str:
        """Log confirmed order to CSV"""
        order_id = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
        
        new_row = {
            'order_id': order_id,
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'items': str(order_data.get('current_order', {})),
            'total': order_data.get('order_total', 0.0),
            'customer_info': str(order_data.get('customer_info', {})),
            'status': 'confirmed'
        }
        
        try:
            df = pd.read_csv(self.csv_path)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_csv(self.csv_path, index=False)
            return order_id
        except Exception as e:
            print(f"Error logging order: {e}")
            return None
    
    def get_order_history(self, user_id: str = None) -> pd.DataFrame:
        """Get order history, optionally filtered by user"""
        try:
            df = pd.read_csv(self.csv_path)
            if user_id:
                df = df[df['user_id'] == user_id]
            return df
        except Exception:
            return pd.DataFrame()

# Global logger instance
order_logger = OrderLogger()