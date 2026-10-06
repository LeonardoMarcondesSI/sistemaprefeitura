from django import forms

from .models import Pedido


class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = [
            'solicitante', 'pessoa_retirada', 'destino',
            'finalidade', 'item', 'quantidade',
        ]
        labels = {
            'solicitante': 'Solicitado por',
            'pessoa_retirada': 'Pessoa que vai retirar',
            'destino': 'Obra ou local de uso',
            'finalidade': 'Para que será usado?',
            'item': 'Item do processo',
            'quantidade': 'Quantidade solicitada',
        }
        widgets = {
            'finalidade': forms.Textarea(attrs={'rows': 3}),
            'quantidade': forms.NumberInput(attrs={'step': '0.0001', 'min': '0.0001'}),
        }
