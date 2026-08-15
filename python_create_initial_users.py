"""
One-off script to create initial login users. Run once:
    python create_initial_users.py
Edit the usernames/passwords below before running.
"""
from chat_storage import init_user_table, create_user

init_user_table()

users_to_create = [
    ("staff1", "ChangeMe123", "staff"),
    ("super1", "ChangeMe123", "supervisor"),
    ("manager1", "ChangeMe123", "manager"),
]

for username, password, role in users_to_create:
    ok = create_user(username, password, role)
    print(f"{username} ({role}): {'created' if ok else 'FAILED (maybe already exists)'}")