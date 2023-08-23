import pandas as pd
from .tasks import *
from .models import *
import concurrent.futures
from .serializers import *
from rest_framework import status
from .utils import checkChatGPTKey
from django.shortcuts import render
from django.http import JsonResponse
from .tasks import process_gmb_tasks
from rest_framework.views import APIView
from django.contrib.auth.models import User
from rest_framework.response import Response
from django.shortcuts import render, redirect
from rest_framework.permissions import AllowAny
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt


# def register(request):
#     if request.user.is_authenticated:
#         return redirect('home')

#     if request.method == 'POST':
#         username = request.POST.get('username')
#         email = request.POST.get('email')
#         password = request.POST.get('password1')

#         try:
#             user = User.objects.create_user(username=username, email=email, password=password)
#             # You can perform any additional operations or validations here

#             return redirect('login')
#         except Exception as e:
#             print(e)

#     return render(request, 'register.html')

# def user_login(request):
#     if request.user.is_authenticated:
#         return redirect('home')

#     if request.method == 'POST':
#         username = request.POST['username']
#         password = request.POST['password']
#         user = authenticate(request, username=username, password=password)
#         if user is not None:
#             login(request, user)
#             return redirect('home')
#         else:
#             return redirect('login')

#     return render(request, 'login.html')

# # @login_required(login_url="login")
# def user_logout(request):
#     logout(request)
#     return redirect('login')

# @login_required(login_url="login")
def home(request):
    return render(request, 'home.html')

# @login_required(login_url="login")
def postContent_tool(request):
    return render(request, "PostContentTool.html")

# @login_required(login_url="login")
def gmb_description(request):
    return render(request, "gmb_description.html")
@csrf_exempt
def process_data(data):
    try:
        Content.objects.create(
            company_name =data.get("company_name"),
            character_long = data.get("character_long"),
            category =  data.get("category"),
            keywords =data.get("keywords"),
            city = data.get("city"),
            tech_name =  data.get("tech_name"),
            stars =data.get("stars"),
            review_writing_style =data.get("review_writing_style"),
            flag=True,
        )
        process_object_content.delay()

    except Exception as e:
        raise Exception(f"Data processing error: {str(e)}")

@csrf_exempt
def process_file(file_obj):
    try:
        if not file_obj:
            raise Exception("No file provided.")

        if file_obj.name.endswith((".csv", ".xlsx")):
            df = (
                pd.read_csv(file_obj)
                if file_obj.name.endswith(".csv")
                else pd.read_excel(file_obj)
            )
            Content.objects.all().update(flag=False)
            for index, row in df.iterrows():
                company = Content(
                    company_name=row['Company Name'],
                    character_long=row['Character Long'],
                    keywords=row['Keywords'],
                    city=row['City'],
                    tech_name=row['Tech Name'],
                    stars=row['Stars'],
                    review_writing_style=row['Review Writing Style'],
                    category=row['Category'],
                    flag=True,
                )
                company.save()

            process_object_content.delay()
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

    def put(self, request):
        pk = request.data.get('id')
        content = request.data.get('content')
        
        if pk:
            if content:
                Content.objects.filter(id=pk).update(content=content)
                return Response({"message": "successfully"}, status=status.HTTP_204_NO_CONTENT)
            Content.objects.filter(id=pk).update(flag=True)
            process_object_content.delay()
            return Response({"message": "successfully"}, status=status.HTTP_204_NO_CONTENT)
        return Response({"message": "pk or content not found"}, status=status.HTTP_204_NO_CONTENT)

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

class GenerateGMBDescriptionAPIView(APIView):
    def post(self, request):
        if "file" in request.FILES:
            df = pd.read_csv(request.FILES["file"])

            json_data = df.to_json(orient="records")
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
            process_gmb_tasks.delay()  # Pass the file data to the Celery task

            return JsonResponse({"message": "GMB descriptions processing started."})
        else:
            data = request.POST  # Assuming request is the HTTP request object
            GMBDescription.objects.create(
                category=data.get('category'),
                location=data.get('location'),
                keyword=data.get('keyword'),
                brand_name=data.get('brand_name'),
                flag=True
            )
            process_gmb_tasks.delay()
            return JsonResponse({"message": "GMB descriptions processing started."})
    def get(self, request):
        gmb_descriptions = GMBDescription.objects.all().order_by("-id")
        serializer = GMBDescriptionSerializer(gmb_descriptions, many=True)
        return Response(serializer.data)

    def put(self, request):
        pk = request.data.get('id')
        description = request.data.get('description')
        if pk:
            if description:
                GMBDescription.objects.filter(id=pk).update(description=description)
                return Response({"message": "successfully"}, status=status.HTTP_204_NO_CONTENT)
            
            GMBDescription.objects.filter(id=pk).update(flag=True)
            process_gmb_tasks.delay()
            return Response({"message": "successfully"}, status=status.HTTP_204_NO_CONTENT)
        return Response({"message": "pk or description not found"}, status=status.HTTP_404_NOT_FOUND)

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


class GlossaryTermAPIView(APIView):
    def post(self, request):
        if "file" in request.FILES:
            # Process CSV file upload
            df = pd.read_csv(request.FILES["file"])

            # json_data = df.to_json()
            # data = json.loads(json_data)
            colum_header  = df.columns[0]
            objects_to_create = [
                GlossaryTerm(
                    main_topic=colum_header,
                    glossaryterm=row,
                    flag=True
                )
                for row in df[colum_header]
            ]

            GlossaryTerm.objects.bulk_create(objects_to_create)
            glossary_term.delay()  # Pass the file data to the Celery task

            return Response({"message": "Glossary terms processing started."}, status=status.HTTP_201_CREATED)
        else:
            data = request.data
            GlossaryTerm.objects.create(
                main_topic=data.get('main_topic'),
                glossaryterm=data.get('glossaryterm'),
                flag=True
            )
            glossary_term.delay()
            return Response({"message": "Glossary terms processing started."}, status=status.HTTP_201_CREATED)
    
    def get(self, request):
        glossary_terms = GlossaryTerm.objects.all().order_by("-id")
        serializer = GlossaryTermsSerializer(glossary_terms, many=True)
        return Response(serializer.data)
    
    def put(self, request):
        pk = request.data.get('id')
        html_answer = request.data.get('html_answer')
        if pk:
            if html_answer:
                GlossaryTerm.objects.filter(id=pk).update(html_answer=html_answer)
                return Response({"message": "successfully"}, status=status.HTTP_204_NO_CONTENT)
            
            GlossaryTerm.objects.filter(id=pk).update(flag=True)
            glossary_term.delay()
            return Response({"message": "successfully"}, status=status.HTTP_204_NO_CONTENT)
        return Response({"message": "pk or html_answer not found"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        pk = request.data.get('id')
        if pk:
            try:
                gmb_description = GlossaryTerm.objects.get(pk=pk)
                gmb_description.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            GlossaryTerm.objects.all().delete()
            return Response(status=status.HTTP_204_NO_CONTENT)