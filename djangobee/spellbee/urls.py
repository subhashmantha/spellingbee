from django.urls import path
from .views import spell_bee_home_page_view


urlpatterns = [
path("", spell_bee_home_page_view, name="spell_bee_home"),
]