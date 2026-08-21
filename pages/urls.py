from django.urls import path

from . import views

app_name = 'pages'

urlpatterns = [
    path('a-propos/', views.apropos, name='apropos'),
    path('contact/', views.contact, name='contact'),
]
