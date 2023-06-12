import json
import httpx
import asyncio
import requests
from .models import *
from celery import shared_task
from asgiref.sync import sync_to_async
from concurrent.futures import ThreadPoolExecutor

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

def create_payload(prompt):
    return {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
    }

async def get_api_headers():
    chat_gpt_key = await sync_to_async(ChatGptKey.objects.first)()
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {chat_gpt_key.secret_key}'
    }
    return headers

@shared_task
def process_object_content():
    while Content.objects.filter(flag=True).exists():
        updated_objects = Content.objects.filter(flag=True)
        try:
            async def process_object(obj):
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
                headers = await get_api_headers()
                async with httpx.AsyncClient() as client:
                    response = await client.post(OPENAI_API_URL, headers=headers, json=payload, timeout=30.0)

                    response_data = response.json()
                    obj.content = response_data["choices"][0]["message"]["content"]
                    obj.flag = False
                    await sync_to_async(obj.save)()
        except:pass
        try:
            with ThreadPoolExecutor(max_workers=50) as executor:
                loop = asyncio.get_event_loop()
                tasks = [process_object(obj) for obj in updated_objects]
                loop.run_until_complete(asyncio.gather(*tasks))
        except:pass

@shared_task
def process_gmb_tasks():

    while GMBDescription.objects.filter(flag=True).exists():
        updated_objects = GMBDescription.objects.filter(flag=True)
        try:
            async def process_object(obj):
                prompt = f"User\nHey, please write me an SEO optimized GMB description for a {obj.category} in {obj.location}.\n\n{obj.keyword} in {obj.location}.\n\nThe company name is {obj.brand_name}.\n\nGive me the SEO keywords you use, please."
                payload = create_payload(prompt)
                headers = await get_api_headers()
                async with httpx.AsyncClient() as client:
                    response = await client.post(OPENAI_API_URL, headers=headers, json=payload, timeout=30.0)

                    response_data = response.json()
                    description = response_data["choices"][0]["message"]["content"]
                    obj.description = description
                    obj.flag = False
                    await sync_to_async(obj.save)()
        except:pass
        try:
            with ThreadPoolExecutor(max_workers=50) as executor:
                loop = asyncio.get_event_loop()
                tasks = [process_object(obj) for obj in updated_objects]
                loop.run_until_complete(asyncio.gather(*tasks))
        except:pass



  








