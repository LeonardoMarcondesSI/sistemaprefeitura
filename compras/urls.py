from django.urls import path

from . import views


app_name = 'compras'

urlpatterns = [
    path('', views.painel, name='painel'),
    path('pedidos/', views.pedido_lista, name='pedido_lista'),
    path('pedidos/novo/', views.pedido_criar, name='pedido_criar'),
    path('pedidos/<int:pk>/editar/', views.pedido_editar, name='pedido_editar'),
    path('pedidos/<int:pk>/excluir/', views.pedido_excluir, name='pedido_excluir'),
]
