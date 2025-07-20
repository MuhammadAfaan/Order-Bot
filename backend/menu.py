# backend/menu.py

menu = {
    "Burgers": {
        "zinger burger": 450,
        "beef burger": 400,
        "double cheese burger": 550
    },
    "Fries & Sides": {
        "fries": 200,
        "cheese fries": 300
    },
    "Drinks": {
        "coke": 100,
        "sprite": 100,
        "water": 50
    }
}

flat_menu_items = [item.lower() for cat in menu.values() for item in cat]

def get_menu_string():
    output = []
    for category, items in menu.items():
        output.append(f"\n🍽️ {category}:\n")
        for name, price in items.items():
            output.append(f"{name.title()} — Rs. {price}")
    return "\n".join(output)


def calculate_total(order_items):
    total = 0
    for item in order_items:
        for category_items in menu.values():
            if item in category_items:
                total += category_items[item]
    return total