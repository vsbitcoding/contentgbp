import json
import requests
from .models import ChatGptKey


def checkChatGPTKey():
    url = "https://api.openai.com/v1/chat/completions"
    payload = json.dumps(
        {
            "model": "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": "You are the assistant."},
                {"role": "user", "content": "Hi!"},
            ],
        }
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer  {(ChatGptKey.objects.all().first()).secret_key}",
    }

    response = requests.request("POST", url, headers=headers, data=payload).json()
    print("::", response)
    if response.get("error") and response.get("error")["type"] == "insufficient_quota":
        return True
    return False
