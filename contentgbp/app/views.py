import pandas as pd
import requests
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
from .tasks import *
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



from django.http import JsonResponse
from .tasks import process_gmb_tasks
import concurrent.futures

class GenerateGMBDescriptionAPIView(APIView):
    def post(self, request):
        df = pd.read_csv(request.FILES["file"])

        # Convert the DataFrame to JSON
        json_data = df.to_json(orient="records")
        process_gmb_tasks.delay(json_data)  # Pass the file data to the Celery task

        return JsonResponse({"message": "GMB descriptions processing started."})

    def get(self, request):
        gmb_descriptions = GMBDescription.objects.all().order_by("-id")
        serializer = GMBDescriptionSerializer(gmb_descriptions, many=True)
        return Response(serializer.data)

    def put(self, request):
        pk = request.data.get('id')
        flag = request.data.get('flag')
        if pk:
            regenerate_description(pk)
            return Response({"message": "successfully"}, status=status.HTTP_204_NO_CONTENT)
        elif flag:
            objects = GMBDescription.objects.filter(flag=True)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for obj in objects:
                    executor.submit(regenerate_description, obj.id)

            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            objects = GMBDescription.objects.filter(flag=True)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                for obj in objects:
                    executor.submit(regenerate_description, obj.id)

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


