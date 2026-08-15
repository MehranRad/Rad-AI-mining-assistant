from chat_storage import list_sessions, load_messages
for s in list_sessions(limit=5):
    print(s)
    for m in load_messages(s["session_id"]):
        print("   ", m["role"], "-", m["content"][:80])