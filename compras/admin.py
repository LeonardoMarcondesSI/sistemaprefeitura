from django.contrib import admin

from .models import Fornecedor, ItemLicitado, Pedido, ProcessoLicitatorio


admin.site.register(Fornecedor)
admin.site.register(ProcessoLicitatorio)
admin.site.register(ItemLicitado)
admin.site.register(Pedido)
