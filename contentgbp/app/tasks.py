import json
import requests
from .models import *
from celery import shared_task
from concurrent import futures


@shared_task
def call_chatgpt_api():
    try:
        with futures.ThreadPoolExecutor() as executor:
            executor.map(process_object, Content.objects.filter(flag=True))
        return True
    except Exception as e:
        print(f"An error occurred during API call: {str(e)}")
        return False


def process_object(obj):
    url = "https://api.openai.com/v1/chat/completions"
    payload = json.dumps(
        {
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
            ],
        }
    )

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer  {(ChatGptKey.objects.all().first()).secret_key}",
    }

    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()

    obj.content = response.json()["choices"][0]["message"]["content"]
    obj.flag = False
    obj.save()



@shared_task
def call_chatgpt_api_for_gmb():
    try:
        with futures.ThreadPoolExecutor() as executor:
            executor.map(process_object_for_gmb_descriptions, GMBDescription.objects.filter(flag=True))
        return True
    except Exception as e:
        print(f"An error occurred during API call: {str(e)}")
        return False


def process_object_for_gmb_descriptions(obj):
    url = "https://api.openai.com/v1/chat/completions"
    payload = json.dumps(
        {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "user",
                    "content": f"please write me seo optimize GMB description for a {obj.category} in {obj.location} \n"
                    f"{obj.keyword} in {obj.location}\n"
                    f"the company name is twin city {obj.brand_name}\n"               
                }
            ],
        }
    )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {(ChatGptKey.objects.all().first()).secret_key}",
    }
    response = requests.post(url, headers=headers, data=payload)
    response.raise_for_status()
    obj.description = response.json()["choices"][0]["message"]["content"]
    obj.flag = False
    obj.save()