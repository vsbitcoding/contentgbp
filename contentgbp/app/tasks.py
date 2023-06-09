import json
import requests
from .models import *
from celery import shared_task
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import io 
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

def get_api_headers():
    chat_gpt_key = ChatGptKey.objects.first()
    if chat_gpt_key:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {chat_gpt_key.secret_key}",
        }
    else:
        raise ValueError("ChatGptKey not found in the database.")

def create_payload(prompt):
    return {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
    }

@shared_task
def call_chatgpt_api():
    try:
        with ThreadPoolExecutor() as executor:
            executor.map(process_object, Content.objects.filter(flag=True))
        return True
    except Exception as e:
        print(f"An error occurred during API call: {str(e)}")
        return False

def process_object(obj):
    prompt = (
        f"Please write me a review for {obj.company_name} company\n"
        f"Character Long: {obj.character_long}\n"
        f"Category: {obj.category}\n"
        f"Keywords: {obj.keywords}\n"
        f"City: {obj.city}\n"
        f"Tech Name: {obj.tech_name}\n"
        f"Stars: {obj.stars}\n"
        f"Review Writing Style: {obj.review_writing_style}"
    )
    payload = create_payload(prompt)
    headers = get_api_headers()
    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        obj.content = response.json()["choices"][0]["message"]["content"]
        obj.flag = False
        obj.save()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during API request: {str(e)}")


import json
import httpx
import asyncio
from concurrent.futures import ThreadPoolExecutor
from asgiref.sync import sync_to_async
from celery import shared_task
from asgiref.sync import sync_to_async

async def get_api_headers1():
    chat_gpt_key = await sync_to_async(ChatGptKey.objects.first)()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {chat_gpt_key.secret_key}'
    }
    return headers

@shared_task
def process_gmb_tasks(json_data):
    data = json.loads(json_data)

    objects_to_create = [
        GMBDescription(
            category=row['Category'],
            location=row['Location'],
            keyword=row['Keyword'],
            brand_name=row['Brand Name'],
            flag=True
        )
        for row in data
    ]

    GMBDescription.objects.bulk_create(objects_to_create)

    while GMBDescription.objects.filter(flag=True).exists():
        # Get the next object with flag=True
        obj = GMBDescription.objects.filter(flag=True).first()
        if obj:
            process_object(obj)

def process_object(obj):
    prompt = f"User\nHey, please write me an SEO optimized GMB description for a {obj.category} in {obj.location}.\n\n{obj.keyword} in {obj.location}.\n\nThe company name is {obj.brand_name}.\n\nGive me the SEO keywords you use, please."
    payload = create_payload(prompt)

    async def process_description():
        headers = await get_api_headers1()

        async with httpx.AsyncClient() as client:
            response = await client.post(OPENAI_API_URL, headers=headers, json=payload, timeout=30.0)

            response_data = response.json()
            description = response_data["choices"][0]["message"]["content"]
            obj.description = description
            obj.flag = False
            await sync_to_async(obj.save)()

    asyncio.run(process_description())

# Example usage to regenerate description for a specific object ID
def regenerate_description(obj_id):
    obj = GMBDescription.objects.get(id=obj_id)
    process_object(obj)






  








