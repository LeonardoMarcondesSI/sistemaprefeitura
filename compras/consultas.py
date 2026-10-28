"""Filtros e totais compartilhados pela consulta, pelo relatório e pelo CSV."""
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum

from .forms import ConsultaForm
from .models import Pedido


def pedidos_do_usuario(usuario):
    pedidos = Pedido.objects.select_related('item__processo', 'item__fornecedor')
    if not usuario.is_superuser:
        pedidos = pedidos.filter(criado_por=usuario)
    return pedidos.order_by('-criado_em', '-pk')


def filtrar_pedidos(usuario, parametros):
    form = ConsultaForm(parametros)
    pedidos = pedidos_do_usuario(usuario)
    # Um filtro inválido nunca deve ampliar silenciosamente a consulta/exportação.
    if not form.is_valid():
        return form, pedidos.none()
    dados = form.cleaned_data
    if dados['busca']:
        pedidos = pedidos.filter(
            Q(solicitante__icontains=dados['busca'])
            | Q(destino__icontains=dados['busca'])
            | Q(item__descricao__icontains=dados['busca'])
        )
    if dados['processo']:
        pedidos = pedidos.filter(item__processo=dados['processo'])
    if dados['fornecedor']:
        pedidos = pedidos.filter(item__fornecedor=dados['fornecedor'])
    if dados['data_inicio']:
        pedidos = pedidos.filter(criado_em__date__gte=dados['data_inicio'])
    if dados['data_fim']:
        pedidos = pedidos.filter(criado_em__date__lte=dados['data_fim'])
    return form, pedidos


def expressao_valor():
    return ExpressionWrapper(
        F('quantidade') * F('item__valor_unitario'),
        output_field=DecimalField(max_digits=30, decimal_places=8),
    )


def totais_pedidos(pedidos):
    return pedidos.aggregate(
        total_pedidos=Count('pk'),
        total_processos=Count('item__processo', distinct=True),
        total_fornecedores=Count('item__fornecedor', distinct=True),
        valor_total=Sum(expressao_valor(), default=0),
    )


def resumo_por_fornecedor(pedidos):
    return pedidos.order_by().values(
        'item__fornecedor_id', 'item__fornecedor__nome',
    ).annotate(total_pedidos=Count('pk'), valor_total=Sum(expressao_valor())).order_by(
        'item__fornecedor__nome', 'item__fornecedor_id',
    )


def texto_csv(valor):
    """Evita interpretar nomes cadastrados como fórmulas em planilhas."""
    texto = str(valor)
    if texto.lstrip().startswith(('=', '+', '-', '@')) or texto.startswith(('\t', '\r', '\n')):
        return "'" + texto
    return texto
