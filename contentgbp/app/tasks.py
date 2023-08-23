import json
import httpx
import asyncio
import requests
from .models import *
from celery import shared_task
from asgiref.sync import sync_to_async
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup

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

@shared_task
def glossary_term():
    while GlossaryTerm.objects.filter(flag=True).exists():
        async def process_object(obj):
            try:
                prompt = (
                    f"Forget previous context. Write 10 H2 headings for an article about {obj.glossaryterm}. "
                    f"The article should focus on how {obj.glossaryterm} relates to {obj.main_topic}. "
                    "Create headings that define {obj.glossaryterm} in the context of {obj.main_topic} using a dictionary-style approach. "
                    "Each heading should build on the previous one. Use professional and neutral language. "
                    "Avoid quoting and numbering. Format lists with bold and appropriate H2 and H3 headings.\n\n"
                    "1. Clear and concise definition of the term.\n"
                    "2. 2 contexts and scopes where the term is used.\n"
                    "3. 2 synonyms and antonyms to understand its meanings.\n"
                    "4. 5 related concepts closely connected to the term.\n"
                    "5. 5 real-world examples and use cases.\n"
                    "6. 5 specific industries where the term is used.\n"
                    "7. 5 use cases the term is applied to.\n"
                    "8. 5 key attributes and characteristics of the term.\n"
                    "9. 3 classifications or categories the term belongs to.\n"
                    "10. Comparisons with 3 similar concepts, highlighting differences.\n\n"
                    "[BLACKLISTED WORDS]\n"
                    "The following words are blacklisted and cannot be used: "
                    "\"Additionally\", \"Moreover\", \"Ultimately\", \"Firstly\", \"Secondly\", "
                    "\"Thirdly\", \"Furthermore\", \"Subsequently\", \"For instance\".\n\n"
                    "Use Oxford Dictionary grammar rules. Maintain high burstiness and perplexity.\n"
                    "When done, ask: 'Would you like to do it again with a different term?' "
                    "If yes, paste the new glossary term and press Enter.\n\n"
                    f"[MAIN TOPIC] \"{obj.main_topic}\"\n"
                    f"[GLOSSARY-TERM] \"{obj.glossaryterm}\"\n"
                )

                payload = create_payload(prompt)
                headers = await get_api_headers()

                async with httpx.AsyncClient() as client:
                    response = await client.post(OPENAI_API_URL, headers=headers, json=payload, timeout=30.0)

                    response_data = response.json()
                    description = response_data["choices"][0]["message"]["content"]
                    obj.answer_1 = description

                    # Now generate data for the specific term
                    term_data_prompt = (
                        f"{obj.answer_1}\n"
                        f"Use the same term, '{obj.glossaryterm}', as above. Provide the following data:\n\n"
                        "- Exact match keyword\n"
                        "- N-gram classification\n"
                        "- Substring matches\n"
                        "- Category\n"
                        "- Search intent\n"
                        "- Semantic relevance\n"
                        "- Parent category\n"
                        "- Subcategories\n"
                        "- Synonyms\n"
                        "- Similar searches\n"
                        "- Related searches\n"
                        "- Geographic relevance\n"
                        "- Topically relevant entities\n\n"
                        "Provide only data, no explanations."
                    )

                    term_data_payload = create_payload(term_data_prompt)

                    response = await client.post(OPENAI_API_URL, headers=headers, json=term_data_payload, timeout=30.0)

                    response_data = response.json()
                    obj.answer_2 = response_data["choices"][0]["message"]["content"]

                    # Save answer_1 and answer_2
                    await sync_to_async(obj.save)()

                    # Generate and save the final answer
                    final_answer = f"{obj.answer_1}\n\n{obj.answer_2}"
                    obj.final_answer = final_answer
                    convert_html_prompt = (
                        "i have below readME.MD file text i want to convert that into HTML do it for me"
                    )
                    convert_html = create_payload(f"{convert_html_prompt}\n\n{final_answer}")
                    response = await client.post(OPENAI_API_URL, headers=headers, json=convert_html, timeout=30.0)

                    response_data = response.json()
                    html_response = response_data["choices"][0]["message"]["content"]
                    soup = BeautifulSoup(html_response, 'html.parser')
                    body_content = soup.find('body').prettify()
                    obj.html_answer = body_content
                    await sync_to_async(obj.save)()

                    obj.flag = False
                    await sync_to_async(obj.save)()

            except Exception as e:
                print(f"Error processing object: {e}")

        updated_objects = GlossaryTerm.objects.filter(flag=True)

        try:
            with ThreadPoolExecutor(max_workers=50) as executor:
                loop = asyncio.get_event_loop()
                tasks = [process_object(obj) for obj in updated_objects]
                loop.run_until_complete(asyncio.gather(*tasks))
        except Exception as e:
            print(f"Error processing tasks: {e}")
  
