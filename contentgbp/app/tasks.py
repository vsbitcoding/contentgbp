from celery import shared_task
import requests
import json
from .models import YourModel

@shared_task
def call_chatgpt_api():
    obj = YourModel.objects.all()
    for i in obj:
        url = "https://api.openai.com/v1/chat/completions"

        payload = json.dumps({
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": f"please write me a review for {i.company_name} company\n"
                            f"Character Long: {i.character_long}\n"
                            f"Category: {i.category}\n"
                            f"Keywords: {i.keywords}\n"
                            f"City: {i.city}\n"
                            f"Tech Name: {i.tech_name}\n"
                            f"Stars: {i.stars}\n"
                            f"Review Writing Style: {i.review_writing_style}",
                }
            ]
        })

        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer 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'
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        print(response, "::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")
        # Find the YourModel object using the provided obj_id
        i.content = response.json()["choices"][0]["message"]["content"]
        i.save()

    return True
