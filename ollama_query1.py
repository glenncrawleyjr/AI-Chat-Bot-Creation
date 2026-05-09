import requests
from requests.exceptions import ConnectionError, Timeout
import json
import datetime
import os

def validate_temperature():
    while True:
        try:
            temp = float(input("Set AI temperature (0.0 to 1.0): "))
            if 0.0 <= temp <= 1.0:
                return temp
            print("! Please enter a number between 0.0 and 1.0.")
        except ValueError:
            print("! Invalid input. Enter a decimal number.")

def validate_server_ip():
    while True:
        ip = input("Enter Server IP: ")
        if ip:
            return ip
        print("! Server IP cannot be empty.")

def setup_logging():
    log_root = "logs"
    os.makedirs(log_root, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_path = os.path.join(log_root, f"session_{timestamp}")
    os.makedirs(session_path, exist_ok=True)
    return session_path

def save_chat(session_path, user_input, ai_reply):
    message_time = datetime.datetime.now().strftime("%H%M%S")
    filename = os.path.join(session_path, f"chat_{message_time}.txt")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"You: {user_input}\nAI: {ai_reply}\n")

if __name__ == "__main__":
    temperature = validate_temperature()
    server_ip = validate_server_ip()
    session_path = setup_logging()

    api_url = f"http://{server_ip}:11434/api/generate"
    headers = {"Content-Type": "application/json"}

    print("AI Assistant is ready. Type your question below.")
    print("Type 'exit' when finished or 'reset' to clear memory.\n")

    conversation_log = []

    while True:
        user_input = input("You: ")

        if user_input.strip().lower() == "exit":
            print("Goodbye!")
            break

        if user_input.strip().lower() == "reset":
            conversation_log.clear()
            print("Memory cleared.\n")
            continue

        conversation_log.append({
            "role": "user",
            "content": user_input
        })

        full_prompt = "".join(
            f"{entry['role'].capitalize()}: {entry['content']}\n"
            for entry in conversation_log
        )

        data = {
            "model": "llama3.2",
            "prompt": full_prompt,
            "temperature": temperature,
            "stream": False
        }

        try:
            response = requests.post(
                api_url,
                headers=headers,
                data=json.dumps(data),
                timeout=60
            )

            if response.status_code == 200:
                try:
                    result = response.json()
                    ai_reply = result.get("response", "[No response]").strip()

                    if not ai_reply:
                        print("AI returned no response. Check server or model name.")
                        continue

                    print(f"AI: {ai_reply}\n")

                    conversation_log.append({
                        "role": "assistant",
                        "content": ai_reply
                    })

                    save_chat(session_path, user_input, ai_reply)

                    with open("chat_log.txt", "a", encoding="utf-8") as log_file:
                        log_file.write(f"[{datetime.datetime.now().isoformat()}] User: {user_input}\n")
                        log_file.write(f"[{datetime.datetime.now().isoformat()}] AI: {ai_reply}\n\n")

                except json.JSONDecodeError:
                    print("Failed to parse response:", response.text)

            else:
                print(f"Error: {response.status_code} - {response.text}")

        except (ConnectionError, Timeout) as e:
            print(f"Connection error: {e}")

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
