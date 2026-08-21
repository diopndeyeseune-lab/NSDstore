from django.urls import include, path

from . import views

app_name = 'comptes'

urlpatterns = [
    path('inscription/', views.inscription, name='inscription'),
    path('confirmer/<str:token>/', views.confirmer_email, name='confirmer_email'),
    path('', include('django.contrib.auth.urls')),
]
