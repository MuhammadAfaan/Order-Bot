MENU_DATA = {
    "mains": {
        "biryani": {"name": "Chicken Biryani", "price": 12.99},
        "pizza": {"name": "Margherita Pizza", "price": 14.99},
        "burger": {"name": "Beef Burger", "price": 9.99},
        "pasta": {"name": "Chicken Alfredo Pasta", "price": 11.99},
        "sandwich": {"name": "Club Sandwich", "price": 8.99},
    },
    "sides": {
        "fries": {"name": "French Fries", "price": 4.99},
        "salad": {"name": "Caesar Salad", "price": 6.99},
        "wings": {"name": "Buffalo Wings", "price": 7.99},
        "bread": {"name": "Garlic Bread", "price": 3.99},
    },
    "drinks": {
        "coke": {"name": "Coca Cola", "price": 2.99},
        "pepsi": {"name": "Pepsi", "price": 2.99},
        "water": {"name": "Bottled Water", "price": 1.99},
        "juice": {"name": "Orange Juice", "price": 3.49},
        "coffee": {"name": "Coffee", "price": 2.49},
    },
    "desserts": {
        "cake": {"name": "Chocolate Cake", "price": 5.99},
        "icecream": {"name": "Vanilla Ice Cream", "price": 4.99},
        "cookie": {"name": "Chocolate Chip Cookie", "price": 2.99},
    }
}

def get_full_menu():
    """Get formatted menu string"""
    menu_str = "🍽️ **RESTAURANT MENU** 🍽️\n\n"
    
    for category, items in MENU_DATA.items():
        menu_str += f"**{category.upper()}:**\n"
        for key, item in items.items():
            menu_str += f"  • {item['name']} - ${item['price']:.2f}\n"
        menu_str += "\n"
    
    return menu_str

def find_menu_item(item_name):
    """Find menu item by name (case-insensitive, flexible matching)"""
    item_name = item_name.lower().strip()
    
    # Direct key matching first
    for category, items in MENU_DATA.items():
        if item_name in items:
            return items[item_name], category
    
    # Fuzzy matching by item name
    for category, items in MENU_DATA.items():
        for key, item in items.items():
            if item_name in item['name'].lower() or item_name in key:
                return item, category
    
    return None, None

def get_item_price(item_name):
    """Get price of menu item"""
    item, _ = find_menu_item(item_name)
    return item['price'] if item else 0.0