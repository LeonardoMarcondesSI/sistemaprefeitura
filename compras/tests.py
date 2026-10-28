import csv
import io
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TestCase, TransactionTestCase

from .consultas import texto_csv
from .models import Fornecedor, ItemLicitado, Pedido, Perfil, ProcessoLicitatorio


class DadosTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = get_user_model().objects.create_user('ana', password='Senha-teste-934!')
        cls.beto = get_user_model().objects.create_user('beto', password='Senha-teste-935!')
        cls.admin = get_user_model().objects.create_superuser('admin', password='Senha-teste-936!')
        cls.fornecedor = Fornecedor.objects.create(nome='Serralheria Exemplo', criado_por=cls.ana)
        cls.outro_fornecedor = Fornecedor.objects.create(nome='Materiais Exemplo', criado_por=cls.beto)
        cls.processo = ProcessoLicitatorio.objects.create(
            numero='001/2026', modalidade='Pregão', numero_licitacao='01/2026',
            saldo_atualizado_em='2026-10-28',
        )
        cls.outro_processo = ProcessoLicitatorio.objects.create(
            numero='002/2026', modalidade='Pregão', numero_licitacao='02/2026',
            saldo_atualizado_em='2026-10-28',
        )
        cls.item = ItemLicitado.objects.create(
            processo=cls.processo, fornecedor=cls.fornecedor, numero=1,
            descricao='Grade metálica', unidade='unidade', valor_unitario=Decimal('125'),
            saldo_informado=Decimal('100'),
        )
        cls.outro_item = ItemLicitado.objects.create(
            processo=cls.outro_processo, fornecedor=cls.outro_fornecedor, numero=1,
            descricao='Areia', unidade='m³', valor_unitario=Decimal('80.50'),
            saldo_informado=Decimal('100'),
        )
        cls.pedido = cls.novo_pedido(cls.ana, cls.item, 'Ana', 'Drenagem', '2')
        cls.outro_pedido = cls.novo_pedido(cls.beto, cls.outro_item, 'Beto exclusivo', 'Praça', '3')
        cls.pedido_areia = cls.novo_pedido(cls.ana, cls.outro_item, 'Ana', 'Praça', '1.5')
        cls.legado = cls.novo_pedido(None, cls.item, 'Legado exclusivo', 'Antigo', '1')
        fuso = ZoneInfo('America/Sao_Paulo')
        Pedido.objects.filter(pk=cls.pedido.pk).update(criado_em=datetime(2026, 10, 28, 23, 59, tzinfo=fuso))
        Pedido.objects.filter(pk=cls.pedido_areia.pk).update(criado_em=datetime(2026, 10, 27, 0, 0, tzinfo=fuso))

    @staticmethod
    def novo_pedido(usuario, item, nome, destino, quantidade):
        return Pedido.objects.create(
            criado_por=usuario, item=item, solicitante=nome, destino=destino,
            pessoa_retirada='Pessoa exemplo', finalidade='Manutenção', quantidade=Decimal(quantidade),
        )

    def setUp(self):
        self.client.force_login(self.ana)

    def dados_pedido(self, **alteracoes):
        dados = {
            'item': self.item.pk, 'solicitante': 'Nova solicitação',
            'pessoa_retirada': 'Retirada', 'destino': 'Obra',
            'finalidade': 'Manutenção', 'quantidade': '2',
        }
        dados.update(alteracoes)
        return dados


class ModelosTests(DadosTestCase):
    def test_valor_estimado_preserva_decimais(self):
        self.assertEqual(self.pedido_areia.valor_estimado, Decimal('120.750'))

    def test_quantidade_deve_ser_positiva(self):
        for quantidade in ['0', '-1']:
            with self.subTest(quantidade=quantidade):
                self.pedido.quantidade = Decimal(quantidade)
                with self.assertRaises(ValidationError):
                    self.pedido.full_clean()

    def test_saldo_considera_pedidos_de_todos_os_usuarios_e_legados(self):
        self.pedido.quantidade = Decimal('100')
        with self.assertRaises(ValidationError):
            self.pedido.full_clean()

    def test_edicao_nao_desconta_o_proprio_pedido_duas_vezes(self):
        self.pedido.quantidade = Decimal('99')
        self.pedido.full_clean()

    def test_perfil_um_para_um(self):
        Perfil.objects.create(usuario=self.ana, setor='Obras')
        self.assertEqual(self.ana.perfil.setor, 'Obras')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Perfil.objects.create(usuario=self.ana)

    def test_relacao_many_to_many_usa_itens_com_dados_extras(self):
        ItemLicitado.objects.create(
            processo=self.processo, fornecedor=self.outro_fornecedor, numero=2,
            descricao='Cimento', unidade='saco', valor_unitario=Decimal('30'), saldo_informado=Decimal('10'),
        )
        self.assertEqual(self.processo.fornecedores.distinct().count(), 2)
        self.assertEqual(self.outro_fornecedor.processos.distinct().count(), 2)
        self.assertEqual(self.processo.itens.get(numero=2).unidade, 'saco')

    def test_csv_neutraliza_formulas(self):
        for texto in ['=1+1', '+1', '-1', '@SOMA(A1)', '  =1', '\ttexto', '\rtexto', '\ntexto']:
            with self.subTest(texto=texto):
                self.assertTrue(texto_csv(texto).startswith("'"))
        self.assertEqual(texto_csv('Fornecedor normal'), 'Fornecedor normal')


class AutenticacaoTests(DadosTestCase):
    def test_paginas_exigem_login(self):
        self.client.logout()
        urls = ['/', '/pedidos/', '/pedidos/novo/', '/fornecedores/', '/fornecedores/novo/',
                '/perfil/', '/consultas/', '/relatorios/', '/relatorios/?formato=csv',
                f'/pedidos/{self.pedido.pk}/editar/', f'/pedidos/{self.pedido.pk}/excluir/',
                f'/fornecedores/{self.fornecedor.pk}/editar/', f'/fornecedores/{self.fornecedor.pk}/excluir/']
        for url in urls:
            with self.subTest(url=url):
                resposta = self.client.get(url)
                self.assertEqual(resposta.status_code, 302)
                self.assertTrue(resposta.url.startswith('/login/?next='))

    def test_login_valido_e_logout_por_post(self):
        self.client.logout()
        resposta = self.client.post('/login/?next=/consultas/', {
            'username': 'ana', 'password': 'Senha-teste-934!', 'next': '/consultas/',
        })
        self.assertRedirects(resposta, '/consultas/')
        self.assertEqual(self.client.get('/sair/').status_code, 405)
        self.assertRedirects(self.client.post('/sair/'), '/login/')
        self.assertEqual(self.client.get('/perfil/').status_code, 302)

    def test_senha_incorreta_e_redirecionamento_externo(self):
        self.client.logout()
        resposta = self.client.post('/login/', {'username': 'ana', 'password': 'errada'})
        self.assertEqual(resposta.context['form'].non_field_errors().as_data()[0].code, 'invalid_login')
        self.assertNotIn('_auth_user_id', self.client.session)
        resposta = self.client.post('/login/', {
            'username': 'ana', 'password': 'Senha-teste-934!', 'next': 'https://example.org/',
        })
        self.assertRedirects(resposta, '/')

    def test_perfil_edita_apenas_usuario_logado(self):
        self.assertContains(self.client.get('/perfil/'), 'Meu perfil')
        resposta = self.client.post('/perfil/', {
            'first_name': 'Ana Maria', 'last_name': 'Exemplo', 'email': 'ana@example.org',
            'setor': 'Obras', 'telefone': '(00) 0000-0000',
            'usuario': self.beto.pk, 'is_superuser': 'on', 'is_staff': 'on',
        })
        self.assertRedirects(resposta, '/perfil/')
        self.ana.refresh_from_db()
        self.beto.refresh_from_db()
        self.assertEqual(self.ana.first_name, 'Ana Maria')
        self.assertEqual(self.ana.perfil.setor, 'Obras')
        self.assertFalse(self.ana.is_superuser)
        self.assertFalse(self.ana.is_staff)
        self.assertEqual(self.beto.first_name, '')
        self.assertContains(self.client.get('/perfil/'), 'Obras')

    def test_perfil_invalido_nao_salva_parcialmente(self):
        resposta = self.client.post('/perfil/', {
            'first_name': 'Nome novo', 'email': 'invalido', 'setor': 'Alterado',
        })
        self.assertEqual(resposta.status_code, 200)
        self.ana.refresh_from_db()
        self.assertEqual(self.ana.first_name, '')
        self.assertEqual(self.ana.perfil.setor, '')

    def test_csrf_bloqueia_alteracoes_sem_token(self):
        cliente = Client(enforce_csrf_checks=True)
        cliente.force_login(self.ana)
        for url in ['/perfil/', '/sair/', '/pedidos/novo/', '/fornecedores/novo/',
                    f'/pedidos/{self.pedido.pk}/excluir/', f'/fornecedores/{self.fornecedor.pk}/excluir/']:
            with self.subTest(url=url):
                self.assertEqual(cliente.post(url, {}).status_code, 403)


class PedidoTests(DadosTestCase):
    def test_criar_define_dono_no_servidor(self):
        resposta = self.client.post('/pedidos/novo/', self.dados_pedido(criado_por=self.beto.pk))
        self.assertRedirects(resposta, '/pedidos/')
        self.assertEqual(Pedido.objects.get(solicitante='Nova solicitação').criado_por, self.ana)

    def test_editar_e_excluir_proprio_pedido(self):
        resposta = self.client.post(f'/pedidos/{self.pedido.pk}/editar/', self.dados_pedido(quantidade='4'))
        self.assertRedirects(resposta, '/pedidos/')
        self.pedido.refresh_from_db()
        self.assertEqual(self.pedido.quantidade, Decimal('4'))
        self.assertEqual(self.client.get(f'/pedidos/{self.pedido.pk}/excluir/').status_code, 200)
        self.assertTrue(Pedido.objects.filter(pk=self.pedido.pk).exists())
        self.assertRedirects(self.client.post(f'/pedidos/{self.pedido.pk}/excluir/'), '/pedidos/')
        self.assertFalse(Pedido.objects.filter(pk=self.pedido.pk).exists())

    def test_outro_dono_e_legados_nao_podem_ser_editados(self):
        for pedido in [self.outro_pedido, self.legado]:
            for acao in ['editar', 'excluir']:
                for metodo in ['get', 'post']:
                    with self.subTest(pedido=pedido.pk, acao=acao, metodo=metodo):
                        self.assertEqual(getattr(self.client, metodo)(f'/pedidos/{pedido.pk}/{acao}/').status_code, 404)
        self.assertTrue(Pedido.objects.filter(pk=self.outro_pedido.pk).exists())

    def test_painel_e_lista_nao_expoem_outros_pedidos(self):
        for url in ['/', '/pedidos/']:
            resposta = self.client.get(url)
            self.assertNotContains(resposta, 'Beto exclusivo')
            self.assertNotContains(resposta, 'Legado exclusivo')
        resposta = self.client.get('/')
        self.assertEqual(resposta.context['total_pedidos'], 2)
        self.assertEqual(resposta.context['valor_total'], Decimal('370.75'))

    def test_superusuario_acessa_pedidos_antigos(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get('/pedidos/'), 'Legado exclusivo')
        self.assertEqual(self.client.get(f'/pedidos/{self.legado.pk}/editar/').status_code, 200)

    def test_saldo_invalido_nao_cadastra(self):
        total = Pedido.objects.count()
        resposta = self.client.post('/pedidos/novo/', self.dados_pedido(quantidade='101'))
        self.assertContains(resposta, 'supera o saldo livre')
        self.assertEqual(Pedido.objects.count(), total)

    def test_post_vazio_mostra_erros(self):
        resposta = self.client.post('/pedidos/novo/', {})
        self.assertTrue(resposta.context['form'].errors)


class FornecedorTests(DadosTestCase):
    def test_crud_completo(self):
        resposta = self.client.post('/fornecedores/novo/', {
            'nome': 'Novo fornecedor', 'documento': '', 'criado_por': self.beto.pk,
        })
        self.assertRedirects(resposta, '/fornecedores/')
        fornecedor = Fornecedor.objects.get(nome='Novo fornecedor')
        self.assertEqual(fornecedor.criado_por, self.ana)
        resposta = self.client.post(f'/fornecedores/{fornecedor.pk}/editar/', {'nome': 'Nome editado'})
        self.assertRedirects(resposta, '/fornecedores/')
        self.assertContains(self.client.get('/fornecedores/'), 'Nome editado')
        self.client.get(f'/fornecedores/{fornecedor.pk}/excluir/')
        self.assertTrue(Fornecedor.objects.filter(pk=fornecedor.pk).exists())
        self.assertRedirects(self.client.post(f'/fornecedores/{fornecedor.pk}/excluir/'), '/fornecedores/')
        self.assertFalse(Fornecedor.objects.filter(pk=fornecedor.pk).exists())

    def test_outro_usuario_so_consulta(self):
        self.assertContains(self.client.get('/fornecedores/'), self.outro_fornecedor.nome)
        for acao in ['editar', 'excluir']:
            for metodo in ['get', 'post']:
                with self.subTest(acao=acao, metodo=metodo):
                    self.assertEqual(getattr(self.client, metodo)(f'/fornecedores/{self.outro_fornecedor.pk}/{acao}/').status_code, 404)

    def test_fornecedor_com_itens_tem_exclusao_protegida(self):
        resposta = self.client.post(f'/fornecedores/{self.fornecedor.pk}/excluir/', follow=True)
        self.assertContains(resposta, 'não pode ser excluído')
        self.assertTrue(Fornecedor.objects.filter(pk=self.fornecedor.pk).exists())

    def test_nome_obrigatorio(self):
        resposta = self.client.post('/fornecedores/novo/', {})
        self.assertIn('nome', resposta.context['form'].errors)


class ConsultaRelatorioTests(DadosTestCase):
    def test_filtros_combinados(self):
        resposta = self.client.get('/consultas/', {
            'busca': 'Grade', 'processo': self.processo.pk, 'fornecedor': self.fornecedor.pk,
            'data_inicio': '2026-10-28', 'data_fim': '2026-10-28',
        })
        self.assertEqual(list(resposta.context['pagina']), [self.pedido])
        self.assertEqual(resposta.context['totais']['valor_total'], Decimal('250'))

    def test_busca_por_solicitante_e_destino(self):
        for busca, quantidade in [('Ana', 2), ('Praça', 1), ('Grade', 1)]:
            with self.subTest(busca=busca):
                resposta = self.client.get('/consultas/', {'busca': busca})
                self.assertEqual(resposta.context['totais']['total_pedidos'], quantidade)

    def test_datas_inclusivas_no_fuso_local(self):
        resposta = self.client.get('/consultas/', {'data_inicio': '2026-10-27', 'data_fim': '2026-10-28'})
        self.assertEqual(resposta.context['totais']['total_pedidos'], 2)
        resposta = self.client.get('/consultas/', {'data_fim': '2026-10-27'})
        self.assertEqual(list(resposta.context['pagina']), [self.pedido_areia])

    def test_filtros_invalidos_nao_ampliam_resultados(self):
        for filtros in [
            {'data_inicio': '2026-10-29', 'data_fim': '2026-10-28'},
            {'data_inicio': 'nao-e-data'}, {'processo': '99999'}, {'fornecedor': 'abc'},
        ]:
            with self.subTest(filtros=filtros):
                resposta = self.client.get('/consultas/', filtros)
                self.assertTrue(resposta.context['form'].errors)
                self.assertEqual(resposta.context['totais']['total_pedidos'], 0)
                resposta = self.client.get('/relatorios/', {**filtros, 'formato': 'csv'})
                self.assertEqual(resposta.status_code, 400)
                self.assertNotIn('Content-Disposition', resposta)

    def test_consulta_e_relatorio_vazios(self):
        for url in ['/consultas/', '/relatorios/']:
            resposta = self.client.get(url, {'busca': 'inexistente'})
            self.assertContains(resposta, 'Nenhum pedido encontrado')
            self.assertEqual(resposta.context['totais']['valor_total'], 0)
        resposta = self.client.get('/relatorios/', {'busca': 'inexistente', 'formato': 'csv'})
        self.assertIn('TOTAL;0;0,00', resposta.content.decode('utf-8-sig'))

    def test_relatorio_agrega_e_csv_corresponde_aos_filtros(self):
        resposta = self.client.get('/relatorios/')
        grupos = list(resposta.context['grupos'])
        self.assertEqual(len(grupos), 2)
        self.assertEqual(resposta.context['totais']['total_pedidos'], 2)
        self.assertEqual(resposta.context['totais']['valor_total'], Decimal('370.75'))
        resposta = self.client.get('/relatorios/', {'fornecedor': self.fornecedor.pk, 'formato': 'csv'})
        linhas = list(csv.reader(io.StringIO(resposta.content.decode('utf-8-sig')), delimiter=';'))
        self.assertEqual(linhas[1], ['Serralheria Exemplo', '1', '250,00'])
        self.assertEqual(linhas[2], ['TOTAL', '1', '250,00'])
        self.assertEqual(resposta['Content-Type'], 'text/csv; charset=utf-8')

    def test_fornecedores_homonimos_nao_se_misturam(self):
        self.outro_fornecedor.nome = self.fornecedor.nome
        self.outro_fornecedor.save()
        resposta = self.client.get('/relatorios/')
        self.assertEqual(len(resposta.context['grupos']), 2)

    def test_exportacao_neutraliza_nome_malicioso(self):
        self.fornecedor.nome = '=1+1'
        self.fornecedor.save()
        resposta = self.client.get('/relatorios/', {'formato': 'csv'})
        self.assertIn("'=1+1;1;250,00", resposta.content.decode('utf-8-sig'))

    def test_paginacao_preserva_filtros_e_csv_exporta_todos(self):
        for _ in range(21):
            self.novo_pedido(self.ana, self.item, 'Ana', 'Drenagem', '1')
        resposta = self.client.get('/consultas/', {'busca': 'Drenagem', 'page': 2})
        self.assertEqual(len(resposta.context['pagina']), 2)
        self.assertEqual(resposta.context['totais']['total_pedidos'], 22)
        self.assertContains(resposta, 'busca=Drenagem')
        resposta = self.client.get('/relatorios/', {'busca': 'Drenagem', 'formato': 'csv', 'page': 2})
        self.assertIn('TOTAL;22;2875,00', resposta.content.decode('utf-8-sig'))

    def test_usuario_nao_consegue_filtrar_pedidos_de_outra_conta(self):
        for url in ['/consultas/', '/relatorios/']:
            resposta = self.client.get(url, {'busca': 'Beto exclusivo'})
            self.assertEqual(resposta.context['totais']['total_pedidos'], 0)
        resposta = self.client.get('/relatorios/', {'busca': 'Beto exclusivo', 'formato': 'csv'})
        self.assertIn('TOTAL;0;0,00', resposta.content.decode('utf-8-sig'))

    def test_todas_as_telas_renderizam(self):
        for url in ['/', '/pedidos/', '/pedidos/novo/', f'/pedidos/{self.pedido.pk}/editar/',
                    f'/pedidos/{self.pedido.pk}/excluir/', '/fornecedores/', '/fornecedores/novo/',
                    f'/fornecedores/{self.fornecedor.pk}/editar/', f'/fornecedores/{self.fornecedor.pk}/excluir/',
                    '/perfil/', '/consultas/', '/relatorios/']:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)


class MigracaoTests(TransactionTestCase):
    def test_atualizacao_preserva_registros_da_semana_2(self):
        anterior = [('compras', '0001_initial')]
        atual = [('compras', '0002_fornecedor_criado_por_pedido_criado_por_and_more')]
        executor = MigrationExecutor(connection)
        executor.migrate(anterior)
        try:
            apps = executor.loader.project_state(anterior).apps
            fornecedor = apps.get_model('compras', 'Fornecedor').objects.create(nome='Fornecedor legado')
            processo = apps.get_model('compras', 'ProcessoLicitatorio').objects.create(
                numero='LEGADO/2026', modalidade='Pregão', numero_licitacao='01',
                saldo_atualizado_em='2026-10-07',
            )
            item = apps.get_model('compras', 'ItemLicitado').objects.create(
                processo=processo, fornecedor=fornecedor, numero=1, descricao='Material legado',
                unidade='unidade', valor_unitario=Decimal('10'), saldo_informado=Decimal('20'),
            )
            pedido = apps.get_model('compras', 'Pedido').objects.create(
                item=item, solicitante='Solicitante legado', pessoa_retirada='Retirada',
                destino='Obra', finalidade='Manutenção', quantidade=Decimal('2'),
            )
        finally:
            MigrationExecutor(connection).migrate(atual)
        preservado = Pedido.objects.get(pk=pedido.pk)
        self.assertEqual(preservado.solicitante, 'Solicitante legado')
        self.assertEqual(preservado.valor_estimado, Decimal('20'))
        self.assertIsNone(preservado.criado_por_id)
        self.assertEqual(ProcessoLicitatorio.objects.get(pk=processo.pk).fornecedores.get().pk, fornecedor.pk)
