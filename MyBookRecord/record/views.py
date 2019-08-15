from django.shortcuts import render
from django.template.response import TemplateResponse

# Create your views here.


def base(request):
    return TemplateResponse(request, 'record/base.html')

def book_detail(request):
    return TemplateResponse(request, 'record/book_detail.html')

def bookshelf(request):
    return TemplateResponse(request, 'record/bookshelf.html')

def data(request):
    return TemplateResponse(request, 'record/data.html')

def profile(request):
    return TemplateResponse(request, 'record/profile.html')

def recommend(request):
    return TemplateResponse(request, 'record/recommend.html')
