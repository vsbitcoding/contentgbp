from celery import shared_task
import requests
import json
from .models import YourModel

@shared_task
def call_chatgpt_api(obj):
    url = "https://api.openai.com/v1/chat/completions"

    payload = json.dumps({
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": f"please write me a review for {obj.company_name} company\n"
                           f"Character Long: {obj.character_long}\n"
                           f"Category: {obj.category}\n"
                           f"Keywords: {obj.keywords}\n"
                           f"City: {obj.city}\n"
                           f"Tech Name: {obj.tech_name}\n"
                           f"Stars: {obj.stars}\n"
                           f"Review Writing Style: {obj.review_writing_style}",
            }
        ]
    })

    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer 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'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    obj.content = response.json()["choices"][0]["message"]["content"]
    obj.save()

    return response.json()
