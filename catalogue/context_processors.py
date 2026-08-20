from .models import Categorie


def categories_menu(request):
    return {'categories_menu': Categorie.objects.all().order_by('nom')}
