from django.http import HttpResponse

def vocab_bee_home_page_view(request):
    return HttpResponse("Hello, World! Welcome to vocabulary bee practice!")