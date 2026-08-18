"""Real-AI behavior test harness: runs the 7 evaluation questions (plus the
follow-up) against the LIVE FastAPI server via the SSE streaming endpoint.

Usage: venv\\Scripts\\python.exe tools\\real_ai_test.py [--role staff|supervisor|manager] [--username X]
Default role: manager (avoids RBAC refusals muddying the evaluation).
"""
import argparse
import json
import sys
import urllib.request

API = "http://localhost:8000"
PASSWORD = "ChangeMe123"

QUESTIONS = [
    "کدام معدن نسبت به تعداد تجهیزات فعالش، بیشترین حجم سنگ استخراج‌شده را دارد؟",
    "آیا معدنی که بیشترین مصرف انرژی را دارد، همان معدنی است که بیشترین تعداد تجهیزات در حال کار را هم دارد؟",
    "رابطه بین سن کارکنان و نرخ بازیابی هر معدن چیست؟",
    "مجموع کل ساعات توقف تجهیزات در تمام معادن چقدر است؟",
    "کدام تولیدکننده (Manufacturer) گران‌ترین تجهیزات را دارد؟",
    "میانگین عمر مفید تجهیزات در حال کار در معدن سونگون چند سال است؟",
    "وضعیت تجهیزات معدن میدوک را بگو",
]

FOLLOW_UP = "مقایسه‌اش کن با اون یکی که بیشترین تجهیز خراب را داره"


def post_json(path, body, token=None, timeout=180):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API + path, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def stream_ask(question, history, token, timeout=300):
    """Returns (answer, steps, is_confidential) from the SSE stream."""
    body = json.dumps({"question": question, "history": history}).encode("utf-8")
    req = urllib.request.Request(API + "/api/ask/stream", data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {token}"}, method="POST")
    answer = ""
    steps = []
    is_confidential = False
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        for raw in resp:
            line = raw.decode("utf-8").strip()
            if not line.startswith("data:"):
                continue
            event = json.loads(line[5:].strip())
            if event["type"] == "meta":
                steps = event.get("steps", [])
                is_confidential = event.get("is_confidential", False)
            elif event["type"] == "token":
                answer += event.get("content", "")
            elif event["type"] == "done":
                break
    return answer, steps, is_confidential


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", default="manager")
    ap.add_argument("--username", default="manager1")
    args = ap.parse_args()

    login = post_json("/api/login", {"username": args.username, "password": PASSWORD}, timeout=30)
    token = login["token"]
    print(f"== Logged in as {args.username} ({args.role}) ==\n", flush=True)

    results = []
    for i, q in enumerate(QUESTIONS, 1):
        print(f"===== QUESTION {i} =====", flush=True)
        print(f"Q: {q}", flush=True)
        answer, steps, is_conf = stream_ask(q, [], token)
        print(f"IS_CONFIDENTIAL: {is_conf}", flush=True)
        print(f"STEPS ({len(steps)}): " + " | ".join(s.get("label", "") for s in steps), flush=True)
        print(f"A:\n{answer}\n", flush=True)
        results.append({"q": q, "a": answer, "steps": steps, "conf": is_conf})

    # Follow-up context test — replay Q7 then ask the follow-up with history.
    print("===== FOLLOW-UP CONTEXT TEST =====", flush=True)
    q7 = results[-1]
    history = [{"role": "user", "content": q7["q"]}, {"role": "assistant", "content": q7["a"]}]
    print(f"Q7 (previous): {q7['q']}", flush=True)
    print(f"FOLLOW-UP: {FOLLOW_UP}", flush=True)
    answer, steps, is_conf = stream_ask(FOLLOW_UP, history, token)
    print(f"STEPS: " + " | ".join(s.get("label", "") for s in steps), flush=True)
    print(f"A:\n{answer}\n", flush=True)
    results.append({"q": FOLLOW_UP, "a": answer, "steps": steps, "conf": is_conf, "follow_up": True})

    with open(r"C:\Users\Mehran\AppData\Local\Temp\opencode\real_ai_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Saved results to real_ai_results.json", flush=True)


if __name__ == "__main__":
    main()
