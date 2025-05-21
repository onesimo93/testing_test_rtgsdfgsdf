
import time
import json
import requests
from datetime import datetime, timedelta
from flask import Flask
from threading import Thread

BOT_TOKEN = "7974439707:AAED3mhse6kTlEi_PhqV8-akTXWQUdEizog"
CHAT_ID = "7040364059"
MEMORY_FILE = "memory.json"
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)
@app.route('/')
def home():
    return "I'm alive"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

def load_memory():
    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "name": "Ivan",
            "preferences": {"tone": "motivational"},
            "reminders": {},
            "notes": [],
            "meal_plan": {},
            "exercise_plan": {},
            "overtime_check": {},
            "custom_reminders": []
        }

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f)

memory = load_memory()
if "calendar" not in memory:
    memory["calendar"] = []

def send_message(text):
    url = f"{API_URL}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    requests.post(url, data=payload)

def process_command(message):
    text = message.strip()
    if text.startswith("/note"):
        note = text[6:]
        memory["notes"].append(note)
        save_memory(memory)
        return f"📝 Note saved: {note}"
    elif text.startswith("/reminder"):
        parts = text.split(" ")
        if len(parts) >= 3:
            task = parts[1]
            time_val = parts[2]
            memory["custom_reminders"].append({"task": task, "time": time_val})
            save_memory(memory)
            return f"⏰ Custom reminder set: {task} at {time_val}"
    elif text.startswith("/tone"):
        tone = text[6:]
        memory["preferences"]["tone"] = tone
        save_memory(memory)
        return f"🎭 Tone preference updated to: {tone}"


    elif text.startswith("/remove"):
        task_to_remove = text[8:].strip()
        initial_len = len(memory["custom_reminders"])
        memory["custom_reminders"] = [r for r in memory["custom_reminders"] if r["task"] != task_to_remove]
        save_memory(memory)
        if len(memory["custom_reminders"]) < initial_len:
            return f"✅ Removed custom reminder: {task_to_remove}"
        else:
            return f"⚠️ No custom reminder found for: {task_to_remove}"

    elif text.startswith("/event"):
        parts = text.split(" ", 3)
        if len(parts) < 4:
            return "⚠️ Usage: /event YYYY-MM-DD HH:MM Your reminder text"
        date_str, time_str, task = parts[1], parts[2], parts[3]
        memory["calendar"].append({"date": date_str, "time": time_str, "event": task})
        save_memory(memory)
        return f"📅 Event scheduled: {task} on {date_str} at {time_str}"
    elif text.startswith("/meal"):
        from datetime import datetime
        import random
        day = datetime.utcnow() + timedelta(hours=9)
        weekday = day.strftime("%A").lower()
        meals = memory.get("meal_plan", {}).get("weekday", {}).get(weekday, {})
        if not meals:
            return "🍽️ No meal plan found for today."
        breakfast = ", ".join(meals.get("breakfast", []))
        lunch = ", ".join(meals.get("lunch", []))
        quote = random.choice(memory.get("motivational_quotes", []))
        return f"🍱 Today’s Meal Plan ({weekday.title()})\n🥣 Breakfast: {breakfast}\n🍛 Lunch: {lunch}\n💬 {quote}"
    elif text.startswith("/status"):
        reminders = "\n".join([f"{k}: {v}" for k, v in memory["reminders"].items()])
        custom = "\n".join([f"{r['task']} at {r['time']}" for r in memory["custom_reminders"]])
        notes = "\n".join(memory["notes"])
        return f"👤 Name: {memory['name']}\n🎭 Tone: {memory['preferences']['tone']}\n⏰ Reminders:\n{reminders}\n🔔 Custom Reminders:\n{custom}\n📝 Notes:\n{notes}"
    return "❓ Command not recognized."

sent_today = set()
last_update_id = None

def check_reminders():
    now = (datetime.utcnow() + timedelta(hours=9)).strftime("%H:%M")
    (datetime.utcnow() + timedelta(hours=9)).strftime("%H:%M")
    for task, time_val in memory["reminders"].items():
        if time_val == now and f"{task}_{time_val}" not in sent_today:
            send_message(f"🔔 Reminder: It's time to {task}!")
            sent_today.add(f"{task}_{time_val}")
    for item in memory.get("custom_reminders", []):
        task = item["task"]
        time_val = item["time"]
        if time_val == now and f"{task}_{time_val}" not in sent_today:
            send_message(f"🔔 Custom Reminder: {task}")
            sent_today.add(f"{task}_{time_val}")
    if now == "00:00":
        sent_today.clear()

def poll_telegram():
    global last_update_id
    while True:
        try:
            url = f"{API_URL}/getUpdates"
            if last_update_id:
                url += f"?offset={last_update_id + 1}"
            res = requests.get(url)
            data = res.json()
            for update in data.get("result", []):
                last_update_id = update["update_id"]
                message = update.get("message", {})
                text = message.get("text", "")
                if text and message["chat"]["id"] == int(CHAT_ID):
                    reply = process_command(text)
                    send_message(reply)
        except Exception as e:
            print(f"Polling error: {e}")
        time.sleep(2)

# Start everything
keep_alive()
send_message("🤖 Kamano Assistant is now online.")
Thread(target=poll_telegram).start()

while True:
    check_reminders()
    time.sleep(60)

