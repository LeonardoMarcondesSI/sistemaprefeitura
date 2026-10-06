from django.core.exceptions import ValidationError
from django.db import models


class Fornecedor(models.Model):
    nome = models.CharField(max_length=180)
    documento = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'fornecedor'
        verbose_name_plural = 'fornecedores'

    def __str__(self):
        return self.nome


class ProcessoLicitatorio(models.Model):
    numero = models.CharField(max_length=30, unique=True)
    modalidade = models.CharField(max_length=80)
    numero_licitacao = models.CharField(max_length=30)
    saldo_atualizado_em = models.DateField(
        help_text='Data do relatório de saldo usado como referência.'
    )

    class Meta:
        ordering = ['-saldo_atualizado_em', 'numero']
        verbose_name = 'processo licitatório'
        verbose_name_plural = 'processos licitatórios'

    def __str__(self):
        return f'Processo {self.numero}'


class ItemLicitado(models.Model):
    processo = models.ForeignKey(
        ProcessoLicitatorio, on_delete=models.PROTECT, related_name='itens'
    )
    fornecedor = models.ForeignKey(
        Fornecedor, on_delete=models.PROTECT, related_name='itens'
    )
    numero = models.PositiveIntegerField()
    descricao = models.CharField(max_length=500)
    unidade = models.CharField(max_length=30)
    valor_unitario = models.DecimalField(max_digits=12, decimal_places=4)
    saldo_informado = models.DecimalField(max_digits=12, decimal_places=4)

    class Meta:
        ordering = ['processo__numero', 'numero']
        constraints = [
            models.UniqueConstraint(
                fields=['processo', 'numero'], name='item_unico_por_processo'
            )
        ]
        verbose_name = 'item licitado'
        verbose_name_plural = 'itens licitados'

    def __str__(self):
        return (
            f'{self.processo.numero} / item {self.numero:04d} - '
            f'{self.descricao} ({self.fornecedor.nome})'
        )

class Pedido(models.Model):
    item = models.ForeignKey(
        ItemLicitado, on_delete=models.PROTECT, related_name='pedidos'
    )
    solicitante = models.CharField(max_length=120)
    pessoa_retirada = models.CharField(max_length=120)
    destino = models.CharField(max_length=180)
    finalidade = models.TextField()
    quantidade = models.DecimalField(max_digits=12, decimal_places=4)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'pedido'
        verbose_name_plural = 'pedidos'

    def __str__(self):
        return f'Pedido {self.pk or "novo"} - {self.solicitante}'

    @property
    def valor_estimado(self):
        return self.quantidade * self.item.valor_unitario

    def clean(self):
        super().clean()
        if not self.item_id or self.quantidade is None:
            return
        if self.quantidade <= 0:
            raise ValidationError({'quantidade': 'Informe uma quantidade maior que zero.'})
        outros_pedidos = Pedido.objects.filter(item=self.item).exclude(pk=self.pk)
        comprometido = sum(pedido.quantidade for pedido in outros_pedidos)
        disponivel = self.item.saldo_informado - comprometido
        if self.quantidade > disponivel:
            raise ValidationError({
                'quantidade': (
                    f'A quantidade supera o saldo livre de {disponivel:.4f} '
                    'informado para este item.'
                )
            })
