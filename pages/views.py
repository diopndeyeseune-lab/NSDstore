from django.shortcuts import render


def apropos(request):
    return render(request, 'pages/apropos.html')


def contact(request):
    return render(request, 'pages/contact.html')
