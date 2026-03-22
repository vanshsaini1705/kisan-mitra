from django.urls import path
from . import views

urlpatterns = [
    path('',                              views.home,              name='home'),
    path('register/',                     views.register_view,     name='register'),
    path('login/',                        views.login_view,        name='login'),
    path('logout/',                       views.logout_view,       name='logout'),
    path('farmer/dashboard/',             views.farmer_dashboard,  name='farmer_dashboard'),
    path('farmer/add/',                   views.add_product,       name='add_product'),
    path('farmer/delete/<int:pk>/',       views.delete_product,    name='delete_product'),
    path('farmer/roi/<int:pk>/',          views.roi_predictor,     name='roi_predictor'),
    # Kisan Mitra — page view + AJAX chat endpoint
    path('kisan-mitra/',                  views.kisan_mitra_view,  name='kisan_mitra'),
    path('kisan-mitra/chat/',             views.kisan_mitra_chat,  name='kisan_mitra_chat'),
]