from django.http import HttpResponse


def spell_bee_home_page_view(request):
    return HttpResponse("Hello, World! Welcome to Spelling bee practice")