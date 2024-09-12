from django.urls import path
from .views import vocab_bee_home_page_view


urlpatterns = [
path("", vocab_bee_home_page_view, name="vocab_bee_home"),
]