from django import forms
from django.contrib.auth import get_user_model

from .models import Fornecedor, Pedido, Perfil, ProcessoLicitatorio


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


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome', 'documento']
        labels = {'documento': 'Documento (opcional)'}


class PerfilForm(forms.ModelForm):
    class Meta:
        model = Perfil
        fields = ['setor', 'telefone']


class UsuarioForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ['first_name', 'last_name', 'email']
        labels = {'first_name': 'Nome', 'last_name': 'Sobrenome', 'email': 'E-mail'}


class ConsultaForm(forms.Form):
    busca = forms.CharField(
        required=False, max_length=120, label='Solicitante, destino ou material',
        widget=forms.TextInput(attrs={'placeholder': 'Ex.: drenagem'}),
    )
    processo = forms.ModelChoiceField(
        queryset=ProcessoLicitatorio.objects.all(), required=False,
        empty_label='Todos os processos',
    )
    fornecedor = forms.ModelChoiceField(
        queryset=Fornecedor.objects.all(), required=False,
        empty_label='Todos os fornecedores',
    )
    data_inicio = forms.DateField(
        required=False, label='Data inicial', input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
    )
    data_fim = forms.DateField(
        required=False, label='Data final', input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
    )

    def clean(self):
        dados = super().clean()
        inicio, fim = dados.get('data_inicio'), dados.get('data_fim')
        if inicio and fim and inicio > fim:
            raise forms.ValidationError('A data inicial deve ser anterior ou igual à data final.')
        return dados
