import os

def load_whitelist():
    whitelist_env = os.getenv("EMAIL_WHITELIST")
    if whitelist_env:
        return set([email.strip().lower() for email in whitelist_env.split(",")])
    try:
        with open("allowed_senders.txt", "r") as f:
            return set(line.strip().lower() for line in f if line.strip())
    except FileNotFoundError:
        return set()

def is_allowed_sender(sender_email: str) -> bool:
    whitelist = load_whitelist()
    return sender_email.lower() in whitelist
