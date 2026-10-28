from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from . import views


app_name = 'compras'

urlpatterns = [
    path('login/', LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('sair/', LogoutView.as_view(), name='logout'),
    path('perfil/', views.perfil, name='perfil'),
    path('consultas/', views.consultas, name='consultas'),
    path('relatorios/', views.relatorio, name='relatorio'),
    path('fornecedores/', views.fornecedor_lista, name='fornecedor_lista'),
    path('fornecedores/novo/', views.fornecedor_criar, name='fornecedor_criar'),
    path('fornecedores/<int:pk>/editar/', views.fornecedor_editar, name='fornecedor_editar'),
    path('fornecedores/<int:pk>/excluir/', views.fornecedor_excluir, name='fornecedor_excluir'),
    path('', views.painel, name='painel'),
    path('pedidos/', views.pedido_lista, name='pedido_lista'),
    path('pedidos/novo/', views.pedido_criar, name='pedido_criar'),
    path('pedidos/<int:pk>/editar/', views.pedido_editar, name='pedido_editar'),
    path('pedidos/<int:pk>/excluir/', views.pedido_excluir, name='pedido_excluir'),
]
