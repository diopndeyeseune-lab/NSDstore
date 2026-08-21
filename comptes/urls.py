from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import views
from .forms import ConnexionForm

app_name = 'comptes'

urlpatterns = [
    path('inscription/', views.inscription, name='inscription'),
    path('confirmer/<str:token>/', views.confirmer_email, name='confirmer_email'),
    path('login/', auth_views.LoginView.as_view(authentication_form=ConnexionForm), name='login'),
    path('', include('django.contrib.auth.urls')),
]
