from django.urls import path
from . import views

app_name = 'record'
urlpatterns = [
     path('', views.base, name='base'),
     path('book_detail/', views.book_detail, name='book_detail'),
     path('bookshelf/', views.bookshelf, name='bookshelf'),
     path('data/', views.data, name='data'),
     path('profile/', views.profile, name='profile'),
     path('recommend/', views.recommend, name='recommend'),
]
