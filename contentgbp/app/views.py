import pandas as pd
from .utils import checkChatGPTKey
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import YourModelSerializer
from .models import YourModel
from .tasks import call_chatgpt_api


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


def process_data(data):
    try:
        YourModel.objects.create(**data, flag=True)
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
            YourModel.objects.all().update(flag=False)
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

                YourModel.objects.create(
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
            queryset = YourModel.objects.all().order_by("-id")
            serializer = YourModelSerializer(queryset, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, 500)

    def post(self, request, format=None):
        try:
            if "file" in request.FILES:
                file_obj = request.FILES["file"]
                process_file(file_obj)
            else:
                data = request.data
                process_data(data)
                call_chatgpt_api.delay()

            return Response({"message": "Data uploaded successfully."}, 201)
        except Exception as e:
            return Response({"error": str(e)}, 400)
