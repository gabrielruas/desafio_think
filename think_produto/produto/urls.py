from django.urls import path

from . import views


urlpatterns = [
    path('', views.home, name='home'),
    path('swagger/', views.swagger_ui, name='swagger-ui'),
    path('openapi.json', views.openapi_schema, name='openapi-schema'),
    path('auth/register', views.register, name='auth-register'),
    path('auth/login', views.login, name='auth-login'),
    path('auth/me', views.me, name='auth-me'),
    path('products', views.products, name='products'),
    path('products/<str:product_id>', views.product_detail, name='product-detail'),
]
