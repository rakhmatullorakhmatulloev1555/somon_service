from datetime import datetime, timedelta

def check_overdue(ticket):

    created = datetime.fromisoformat(ticket["created_at"])

    if datetime.now() - created > timedelta(hours=4):
        ticket["sla"] = "OVERDUE"
