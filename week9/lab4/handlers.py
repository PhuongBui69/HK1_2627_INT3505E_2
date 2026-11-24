def v1_create_order(body):
    return {"account_id": body.get("account_id", ""), "status": "ok"}


def v2_create_order(body):
    return {"account_id": body.get("account_id", ""), "status": "created"}
