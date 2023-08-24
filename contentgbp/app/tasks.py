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
    async def process_term(obj):
        async with httpx.AsyncClient(timeout=600) as client:
            prompt = (
                  f"[MAIN TOPIC] \"{obj.main_topic}\"\n"
                f"[GLOSSARY-TERM] \"{obj.glossaryterm}\"\n"
                
                '''
                you are as a role of my assistant, you have to write a article about [GLOSSARY-TERM] for [MAIN TOPIC] in 2000 characters.

                ***MOST IMPORTANT***
                0/ delete previous article if exist and create a new one
                1/ Generate an article with MAX 2000 characters long using the following prompt:

                ***IMPORTANT***
                Forget everything that came before.Write 10 h2 headings for 1 article. Article should be about [GLOSSARY-TERM]. The topic vector should slant the article towards "How [GLOSSARY-TERM] relates to [MAIN TOPIC]". The goal is to create headings that will very clearly define the [GLOSSARY-TERM] as it relates to the [MAIN TOPIC] in the form of a dictionary definition. Each heading should build on the idea in the previous heading. Write topic rich headings. Use NLP friendly headings. Use Professional neutral, scientific and professional language at all times. Do not write the answer in "quotes". Do not write numbers. Do not write conclusions. All headings should be topic rich. Format lists using bolded words, as well as appropriate h2 and h3 headings.Complete the [INSTRUCTIONS],

                "Provide a clear and concise definition of the term you want to define.
                Specify the 2 contexts and scopes in which the term is used.
                Identify 2 synonyms and antonyms of the term to understand its range of meanings.
                Explore 5 related concepts and terms that are closely connected to the term being defined.
                Gather 5 real-world examples and use cases of the term in various contexts.
                What 5 Specific industries is the term used in.
                What 5 specific use cases does the term have.
                List 5 key attributes and characteristics that define the term.
                Determine the 3 classifications or categories the term belongs to.
                Make comparisons with 3 similar concepts to highlight similarities and differences."

                [BLACKLISTED WORDS]
                The following list of words is blacklisted and you are not allowed to use them in the final output."Additionally","Moreover","Ultimately","Firstly","Secondly","Thirdly","Furthermore","Subsequently","For instance". Use the Oxford Dictionary rules of grammar for every sentence. Use high burstiness and perplexity for. When Done, ask me, "Would you like to do it again using different [GLOSSARY-TERM]? If so, just paste your new term below and Hit Enter."
                '''
                )

            payload = create_payload(prompt)
            headers = await get_api_headers()

            payload = create_payload(prompt)
            response1 = await client.post(OPENAI_API_URL, headers=headers, json=payload)
            response_data1 = response1.json()
            obj.answer_1 = response_data1["choices"][0]["message"]["content"]
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
            response2 = await client.post(OPENAI_API_URL, headers=headers, json=term_data_payload)
            response_data2 = response2.json()
            obj.answer_2 = response_data2["choices"][0]["message"]["content"]
            # Generate and save the final answer
            final_answer = f"{obj.answer_1}\n\n{obj.answer_2}"
            obj.final_answer = final_answer
            convert_html_prompt = (
                "convert this html5  and  give me full code"
            )
            convert_html = create_payload(f"{convert_html_prompt}\n\n{final_answer}")
            response3 = await client.post(OPENAI_API_URL, headers=headers, json=convert_html)

            response_data3 = response3.json()
            html_response = response_data3["choices"][0]["message"]["content"]
            soup = BeautifulSoup(html_response, 'html.parser')
            body_tag = soup.find('body')
            if body_tag:
                body_content = body_tag.prettify()
            else:
                body_content = "opps content was not found"
            obj.html_answer = body_content

            obj.flag = False
            await sync_to_async(obj.save)()

    while GlossaryTerm.objects.filter(flag=True).exists():
        updated_objects = GlossaryTerm.objects.filter(flag=True)
        loop = asyncio.get_event_loop()  # Get the event loop
        tasks = [process_term(obj) for obj in updated_objects]
        loop.run_until_complete(asyncio.gather(*tasks))
