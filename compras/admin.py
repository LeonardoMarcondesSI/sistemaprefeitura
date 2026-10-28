from django.contrib import admin

from .models import Fornecedor, ItemLicitado, Pedido, Perfil, ProcessoLicitatorio


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'documento', 'criado_por']
    list_filter = ['criado_por']
    search_fields = ['nome']


admin.site.register(ProcessoLicitatorio)
admin.site.register(ItemLicitado)
admin.site.register(Perfil)


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'solicitante', 'item', 'quantidade', 'criado_por']
    list_filter = ['criado_por']
    search_fields = ['solicitante', 'destino']
