from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PedidoForm
from .models import Fornecedor, ItemLicitado, Pedido, ProcessoLicitatorio


def painel(request):
    pedidos = Pedido.objects.all()
    valor_total = sum(pedido.valor_estimado for pedido in pedidos)
    contexto = {
        'total_pedidos': pedidos.count(),
        'total_processos': ProcessoLicitatorio.objects.count(),
        'total_fornecedores': Fornecedor.objects.count(),
        'total_itens': ItemLicitado.objects.count(),
        'valor_total': valor_total,
        'pedidos_recentes': pedidos[:5],
    }
    return render(request, 'compras/painel.html', contexto)


def pedido_lista(request):
    pedidos = Pedido.objects.all()
    return render(request, 'compras/pedido_lista.html', {'pedidos': pedidos})


def pedido_criar(request):
    form = PedidoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Pedido cadastrado.')
        return redirect('compras:pedido_lista')
    return render(request, 'compras/pedido_form.html', {
        'form': form, 'titulo': 'Novo pedido', 'botao': 'Cadastrar pedido',
    })


def pedido_editar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    form = PedidoForm(request.POST or None, instance=pedido)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Pedido atualizado.')
        return redirect('compras:pedido_lista')
    return render(request, 'compras/pedido_form.html', {
        'form': form, 'titulo': f'Editar pedido {pedido.pk}',
        'botao': 'Salvar alterações', 'pedido': pedido,
    })


def pedido_excluir(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == 'POST':
        pedido.delete()
        messages.success(request, 'Pedido excluído.')
        return redirect('compras:pedido_lista')
    return render(request, 'compras/pedido_confirmar_exclusao.html', {
        'pedido': pedido,
    })
