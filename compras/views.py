import csv
from decimal import Decimal, ROUND_HALF_UP

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .consultas import (
    filtrar_pedidos, pedidos_do_usuario, resumo_por_fornecedor, texto_csv, totais_pedidos,
)
from .forms import FornecedorForm, PedidoForm, PerfilForm, UsuarioForm
from .models import Fornecedor, ItemLicitado, Perfil, ProcessoLicitatorio


@login_required
def painel(request):
    pedidos = pedidos_do_usuario(request.user)
    contexto = totais_pedidos(pedidos)
    contexto.update({
        'total_processos': ProcessoLicitatorio.objects.count(),
        'total_fornecedores': Fornecedor.objects.count(),
        'total_itens': ItemLicitado.objects.count(),
        'pedidos_recentes': pedidos[:5],
    })
    return render(request, 'compras/painel.html', contexto)


@login_required
def pedido_lista(request):
    return render(request, 'compras/pedido_lista.html', {
        'pedidos': pedidos_do_usuario(request.user),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def pedido_criar(request):
    form = PedidoForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        pedido = form.save(commit=False)
        pedido.criado_por = request.user
        pedido.save()
        messages.success(request, 'Pedido cadastrado.')
        return redirect('compras:pedido_lista')
    return render(request, 'compras/pedido_form.html', {
        'form': form, 'titulo': 'Novo pedido', 'botao': 'Cadastrar pedido',
    })


@login_required
@require_http_methods(['GET', 'POST'])
def pedido_editar(request, pk):
    pedido = get_object_or_404(pedidos_do_usuario(request.user), pk=pk)
    form = PedidoForm(request.POST if request.method == 'POST' else None, instance=pedido)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Pedido atualizado.')
        return redirect('compras:pedido_lista')
    return render(request, 'compras/pedido_form.html', {
        'form': form, 'titulo': f'Editar pedido {pedido.pk}',
        'botao': 'Salvar alterações', 'pedido': pedido,
    })


@login_required
@require_http_methods(['GET', 'POST'])
def pedido_excluir(request, pk):
    pedido = get_object_or_404(pedidos_do_usuario(request.user), pk=pk)
    if request.method == 'POST':
        pedido.delete()
        messages.success(request, 'Pedido excluído.')
        return redirect('compras:pedido_lista')
    return render(request, 'compras/pedido_confirmar_exclusao.html', {'pedido': pedido})


def fornecedores_editaveis(usuario):
    fornecedores = Fornecedor.objects.all()
    return fornecedores if usuario.is_superuser else fornecedores.filter(criado_por=usuario)


@login_required
def fornecedor_lista(request):
    return render(request, 'compras/fornecedor_lista.html', {
        'fornecedores': Fornecedor.objects.select_related('criado_por').all(),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def fornecedor_criar(request):
    form = FornecedorForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        fornecedor = form.save(commit=False)
        fornecedor.criado_por = request.user
        fornecedor.save()
        messages.success(request, 'Fornecedor cadastrado.')
        return redirect('compras:fornecedor_lista')
    return render(request, 'compras/fornecedor_form.html', {
        'form': form, 'titulo': 'Novo fornecedor',
    })


@login_required
@require_http_methods(['GET', 'POST'])
def fornecedor_editar(request, pk):
    fornecedor = get_object_or_404(fornecedores_editaveis(request.user), pk=pk)
    form = FornecedorForm(request.POST if request.method == 'POST' else None, instance=fornecedor)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Fornecedor atualizado.')
        return redirect('compras:fornecedor_lista')
    return render(request, 'compras/fornecedor_form.html', {
        'form': form, 'titulo': 'Editar fornecedor',
    })


@login_required
@require_http_methods(['GET', 'POST'])
def fornecedor_excluir(request, pk):
    fornecedor = get_object_or_404(fornecedores_editaveis(request.user), pk=pk)
    if request.method == 'POST':
        try:
            fornecedor.delete()
        except ProtectedError:
            messages.error(request, 'Este fornecedor possui itens licitados vinculados e não pode ser excluído.')
        else:
            messages.success(request, 'Fornecedor excluído.')
        return redirect('compras:fornecedor_lista')
    return render(request, 'compras/fornecedor_confirmar_exclusao.html', {
        'fornecedor': fornecedor,
    })


@login_required
@require_http_methods(['GET', 'POST'])
def perfil(request):
    perfil_usuario, _ = Perfil.objects.get_or_create(usuario=request.user)
    dados = request.POST if request.method == 'POST' else None
    usuario_form = UsuarioForm(dados, instance=request.user)
    perfil_form = PerfilForm(dados, instance=perfil_usuario)
    if request.method == 'POST':
        usuario_valido = usuario_form.is_valid()
        perfil_valido = perfil_form.is_valid()
        if usuario_valido and perfil_valido:
            with transaction.atomic():
                usuario_form.save()
                perfil_form.save()
            messages.success(request, 'Seu perfil foi atualizado.')
            return redirect('compras:perfil')
    return render(request, 'compras/perfil.html', {
        'usuario_form': usuario_form, 'perfil_form': perfil_form,
        'perfil_usuario': perfil_usuario,
    })


@login_required
def consultas(request):
    form, pedidos = filtrar_pedidos(request.user, request.GET)
    pagina = Paginator(pedidos, 20).get_page(request.GET.get('page'))
    parametros = request.GET.copy()
    parametros.pop('page', None)
    return render(request, 'compras/consultas.html', {
        'form': form, 'pagina': pagina, 'totais': totais_pedidos(pedidos),
        'filtros_url': parametros.urlencode(),
    })


@login_required
def relatorio(request):
    form, pedidos = filtrar_pedidos(request.user, request.GET)
    totais = totais_pedidos(pedidos)
    grupos = resumo_por_fornecedor(pedidos)
    if request.GET.get('formato') == 'csv' and form.is_valid():
        resposta = HttpResponse(content_type='text/csv; charset=utf-8')
        resposta['Content-Disposition'] = 'attachment; filename="relatorio-pedidos.csv"'
        resposta.write('\ufeff')
        writer = csv.writer(resposta, delimiter=';')
        writer.writerow(['Fornecedor', 'Pedidos', 'Valor estimado (R$)'])
        for grupo in grupos:
            writer.writerow([
                texto_csv(grupo['item__fornecedor__nome']), grupo['total_pedidos'],
                moeda_csv(grupo['valor_total']),
            ])
        writer.writerow(['TOTAL', totais['total_pedidos'], moeda_csv(totais['valor_total'])])
        return resposta
    parametros = request.GET.copy()
    parametros.pop('formato', None)
    parametros.pop('page', None)
    return render(request, 'compras/relatorio.html', {
        'form': form, 'totais': totais, 'grupos': grupos,
        'filtros_url': parametros.urlencode(),
    }, status=400 if request.GET.get('formato') == 'csv' and not form.is_valid() else 200)


def moeda_csv(valor):
    return format(valor.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP), '.2f').replace('.', ',')
