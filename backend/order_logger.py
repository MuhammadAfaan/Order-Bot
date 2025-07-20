import csv

def log_order(user_id, order_state):
    with open("orders.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            user_id,
            ", ".join(order_state["items"]),
            order_state.get("address"),
            order_state.get("phone"),
            "confirmed" if order_state["confirmed"] else "not confirmed"
        ])
