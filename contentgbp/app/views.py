from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login as auth_login, logout as auth_logout
import pandas as pd
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import YourModelSerializer
from .models import YourModel

@login_required(login_url='login')
def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

def login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            auth_login(request, form.get_user())
            return redirect('home')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

@login_required(login_url='login')
def logout(request):
    auth_logout(request)
    return redirect('login')

@login_required
def postContent_tool(request):
    return render(request, 'PostContentTool.html')




class FileUploadAPIView(APIView):
    def get(self, request, format=None):
        queryset = YourModel.objects.all()
        serializer = YourModelSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        file_obj = request.FILES.get('file')

        if not file_obj:
            return Response({'error': 'No file provided.'}, status=400)

        try:
            if file_obj.name.endswith('.csv'):
                df = pd.read_csv(file_obj)
            elif file_obj.name.endswith('.xlsx'):
                df = pd.read_excel(file_obj)
            else:
                return Response({'error': 'Unsupported file format.'}, status=400)

            for _, row in df.iterrows():
                obj = YourModel(
                    company_name=row['Company Name'],
                    character_long=row['character Long'],
                    category=row['Category'],
                    keywords=row['Keywords'],
                    city=row['City'],
                    tech_name=row['Tech Name'],
                    stars=row['Stars'],
                    review_writing_style=row['Review writing Style']
                )
                obj.save()

                # Call ChatGPT API
                response = self.call_chatgpt_api(obj)

                # Save response in content field
                obj.content = response['content']
                obj.save()

            return Response({'message': 'Data uploaded successfully.'}, status=201)
        except Exception as e:
            return Response({'error': str(e)}, status=400)

    def call_chatgpt_api(self, obj):
        api_key = 'YOUR_API_KEY'  # Replace with your ChatGPT API key
        url = 'https://api.openai.com/v1/chat/completions'

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'messages': [
                {
                    'role': 'user',
                    'content': f"please write me a review for {obj.company_name} company\n"
                               f"Character Long: {obj.character_long}\n"
                               f"Category: {obj.category}\n"
                               f"Keywords: {obj.keywords}\n"
                               f"City: {obj.city}\n"
                               f"Tech Name: {obj.tech_name}\n"
                               f"Stars: {obj.stars}\n"
                               f"Review Writing Style: {obj.review_writing_style}"
                }
            ],
            'max_tokens': 50
        }

        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

        return response.json()


