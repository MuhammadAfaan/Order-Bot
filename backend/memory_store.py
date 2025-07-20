from collections import defaultdict

user_orders = defaultdict(lambda: {
    "items": [],
    "confirmed": False,
    "address": None,
    "phone": None
})

def get_user_state(user_id):
    return user_orders[user_id]
