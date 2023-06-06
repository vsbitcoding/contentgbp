import requests
from .models import *
from celery import shared_task
from concurrent.futures import ThreadPoolExecutor

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


@shared_task
def call_chatgpt_api_for_gmb():
    try:
        with ThreadPoolExecutor() as executor:
            executor.map(process_object_for_gmb_descriptions, GMBDescription.objects.filter(flag=True))
        return True
    except Exception as e:
        print(f"An error occurred during API call: {str(e)}")
        return False


def process_object_for_gmb_descriptions(obj):
    prompt = (
    "User"
    f"Hey, please write me an SEO optimized GMB description for a {obj.category} in {obj.location}.\n"
    f"\n{obj.keyword} in {obj.location}.\n"
    f"\nThe company name is {obj.brand_name}.\n"
    "\nGive me the SEO keywords you use, please."
)
    payload = create_payload(prompt)
    headers = get_api_headers()
    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        if 'seo' in content.lower():
            result = {'seo': {'before': content.split('seo', 1)[0].strip(), 'after': content.split('seo', 1)[1].strip()} for _ in [0]}
            obj.description = result['seo']['before']
            obj.seo_description = result['seo']['after']
        else:
            obj.description = content
            obj.seo_description = ''
        obj.flag = False
        obj.save()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during API request: {str(e)}")
    except KeyError as e:
        print(f"Error in processing API response: {str(e)}")