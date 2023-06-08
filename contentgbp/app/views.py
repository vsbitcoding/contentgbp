import pandas as pd
from .utils import checkChatGPTKey
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import *
from .models import *
from .tasks import call_chatgpt_api,call_chatgpt_api_for_gmb_task
from rest_framework import status
from django.shortcuts import render
import openai

def home(request):
    return render(request, "home.html")


# def register(request):
#     if request.method == "POST":
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect("login")
#     else:
#         form = UserCreationForm()
#     return render(request, "register.html", {"form": form})


# def login(request):
#     if request.method == "POST":
#         form = AuthenticationForm(request, data=request.POST)
#         if form.is_valid():
#             auth_login(request, form.get_user())
#             return redirect("home")
#     else:
#         form = AuthenticationForm()
#     return render(request, "login.html", {"form": form})


# @login_required(login_url="login")
# def logout(request):
#     auth_logout(request)
#     return redirect("login")


def postContent_tool(request):
    return render(request, "PostContentTool.html")

def gmb_description(request):
    pending_content = GMBDescription.objects.filter(flag=True)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(call_chatgpt_api_for_gmb_task.delay, obj.id) for obj in pending_content]
        concurrent.futures.wait(futures)

    return render(request, "gmb_description.html")


def process_data(data):
    try:
        company_name = data.get("Company Name") or data.get("company_name")
        character_long = data.get("character Long") or data.get("character_long")
        category = data.get("Category") or data.get("category")
        keywords = data.get("Keywords") or data.get("keywords")
        city = data.get("City") or data.get("city")
        tech_name = data.get("Tech Name") or data.get("tech_name")
        stars = data.get("Stars") or data.get("stars")
        review_writing_style = data.get("Review writing Style") or data.get(
            "review_writing_style"
        )

        Content.objects.create(
            company_name=company_name,
            character_long=character_long,
            category=category,
            keywords=keywords,
            city=city,
            tech_name=tech_name,
            stars=stars,
            review_writing_style=review_writing_style,
            flag=True,  # Set flag=True for new object
        )
        call_chatgpt_api.delay()

    except Exception as e:
        raise Exception(f"Data processing error: {str(e)}")


def process_file(file_obj):
    try:
        if not file_obj:
            raise Exception("No file provided.")
        checkKey = checkChatGPTKey()
        if checkKey:
            raise Exception("Your gpt key expired")

        if file_obj.name.endswith((".csv", ".xlsx")):
            df = (
                pd.read_csv(file_obj)
                if file_obj.name.endswith(".csv")
                else pd.read_excel(file_obj)
            )
            Content.objects.all().update(flag=False)
            for _, row in df.iterrows():
                # Extract the necessary data from the row
                company_name = row.get("Company Name") or row.get("company_name")
                character_long = row.get("character Long") or row.get("character_long")
                category = row.get("Category") or row.get("category")
                keywords = row.get("Keywords") or row.get("keywords")
                city = row.get("City") or row.get("city")
                tech_name = row.get("Tech Name") or row.get("tech_name")
                stars = row.get("Stars") or row.get("stars")
                review_writing_style = row.get("Review writing Style") or row.get(
                    "review_writing_style"
                )
                Content.objects.create(
                    company_name=company_name,
                    character_long=character_long,
                    category=category,
                    keywords=keywords,
                    city=city,
                    tech_name=tech_name,
                    stars=stars,
                    review_writing_style=review_writing_style,
                    flag=True,  # Set flag=True for new object
                )
            call_chatgpt_api.delay()
        else:
            raise Exception("Unsupported file format.")
    except FileNotFoundError:
        raise Exception("File not found.")
    except Exception as e:
        raise Exception(str(e))


class FileUploadAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        try:
            queryset = Content.objects.all().order_by("-id")
            serializer = ContentSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, format=None):
        try:
            if "file" in request.FILES:
                file_obj = request.FILES["file"]
                process_file(file_obj)
            else:
                data = request.data
                process_data(data)

            return Response({"message": "Data uploaded successfully."}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        pk = request.data.get('id')
        if pk:
            try:
                content = Content.objects.get(pk=pk)
                content.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Content.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            Content.objects.all().delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

import concurrent.futures

from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import GMBDescription
from .serializers import GMBDescriptionSerializer
from .tasks import call_chatgpt_api_for_gmb_task

class GenerateGMBDescriptionAPIView(APIView):
    def post(self, request):
        file = request.FILES.get("file")
        if file:
            try:
                df = pd.read_csv(file)
                df.fillna("", inplace=True)  # Replace NaN values with empty strings

                objects_to_create = []
                for index, row in df.iterrows():
                    obj = GMBDescription(
                        keyword=row["Category"],
                        location=row["Location"],
                        brand_name=row["Keyword"],
                        category=row["Brand Name"],
                        flag=True,
                    )
                    objects_to_create.append(obj)

                GMBDescription.objects.bulk_create(objects_to_create)

                task_ids = [obj.id for obj in objects_to_create]
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    for obj_id in task_ids:
                        executor.submit(call_chatgpt_api_for_gmb_task, obj_id)

                pending_content = GMBDescription.objects.filter(flag=True)
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    for obj in pending_content:
                        executor.submit(call_chatgpt_api_for_gmb_task, obj_id)
                        
                pending_content = GMBDescription.objects.filter(flag=True)
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    for obj in pending_content:
                        executor.submit(call_chatgpt_api_for_gmb_task, obj_id)

                return Response({"message": "GMB descriptions saved successfully."})
            except Exception as e:
                return Response({"error": f"Error processing the file: {str(e)}"}, status=400)
        else:
            try:
                obj = GMBDescription(
                    keyword=request.data.get("keyword"),
                    location=request.data.get("location"),
                    brand_name=request.data.get("brand_name"),
                    category=request.data.get("category"),
                    flag=True,
                )
                obj.save()
                call_chatgpt_api_for_gmb_task.delay(obj.id)
                return Response({"message": "GMB descriptions saved successfully."})
            except Exception as e:
                return Response({"error": f"Data processing error: {str(e)}"}, status=400)
            
    def get(self, request):
        gmb_descriptions = GMBDescription.objects.all().order_by("-id")
        serializer = GMBDescriptionSerializer(gmb_descriptions, many=True)
        return Response(serializer.data)

    def put(self, request):
        pk = request.data.get('id')
        flag = request.data.get('flag')
        if pk:
            call_chatgpt_api_for_gmb_task.delay(pk)
            return Response({"message": "successfully"},status=status.HTTP_204_NO_CONTENT)
        elif flag:
            objects = GMBDescription.objects.filter(flag=True)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for obj in objects:
                    executor.submit(call_chatgpt_api_for_gmb_task, obj.id)

            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            objects = GMBDescription.objects.filter(flag=True)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for obj in objects:
                    executor.submit(call_chatgpt_api_for_gmb_task, obj.id)

            return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request):
        pk = request.data.get('id')
        if pk:
            try:
                gmb_description = GMBDescription.objects.get(pk=pk)
                gmb_description.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            GMBDescription.objects.all().delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

