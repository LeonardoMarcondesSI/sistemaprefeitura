# Controle de pedidos de materiais

Sistema acadêmico em Python/Django para pedidos de material do setor de obras. A entrega da semana 5 reúne os requisitos acumulados: painel, dois CRUDs, relacionamentos, autenticação, perfil, consultas e relatório com exportação CSV.

Os dados de exemplo são fictícios. O projeto continua configurado para execução local (`DEBUG=True`, SQLite); não é uma implantação de produção. Não coloque documentos nem dados reais da prefeitura no GitHub. O saldo é cadastrado manualmente e deve ser conferido com a referência atualizada. O sistema não importa PDFs nem emite autorizações.

## Preparar uma cópia nova no Windows

Requer Python 3.10 ou superior. Na pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py loaddata exemplo
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Abra http://127.0.0.1:8000/ e entre com a conta criada. A senha é definida interativamente; nenhuma conta ou senha pronta acompanha o repositório. O comando `loaddata exemplo` é opcional e deve ser usado somente em banco de demonstração vazio.

Para reproduzir os pedidos adicionais das capturas, depois da fixture inicial:

```powershell
.\.venv\Scripts\python.exe manage.py loaddata exemplo_semana5
```

Os exemplos não têm proprietário e ficam visíveis ao superusuário. Para usuários comuns, atribua os registros a uma conta no Admin ou crie novos pedidos pela interface.

## Atualizar uma instalação da semana 2

1. Pare o servidor e faça uma cópia de segurança de `db.sqlite3`.
2. Atualize o código e instale as dependências de `requirements.txt`.
3. Execute `python manage.py migrate`. A migração mantém os registros e adiciona os campos de proprietário, o perfil e a relação entre processos e fornecedores.
4. Se ainda não houver administrador, execute `python manage.py createsuperuser`.
5. Entre em `/admin/`. Crie as contas comuns em **Usuários** e atribua o campo **Criado por** dos pedidos/fornecedores antigos à conta correta.
6. Reinicie o servidor. Todas as páginas do sistema agora exigem login.

Não carregue as fixtures sobre um banco que já possui dados. Registros anteriores ficam com `criado_por` vazio até atribuição pelo administrador; não são atribuídos automaticamente a quem entrar primeiro. O perfil é criado no primeiro acesso à página **Meu perfil**.

## Funcionalidades

- Painel com contagens reais, atividade recente e valores estimados.
- CRUD completo de pedidos, com validação de quantidade positiva e saldo disponível.
- CRUD completo de fornecedores. A exclusão é bloqueada quando há itens licitados vinculados.
- Login e logout por POST, área restrita e edição do próprio perfil.
- Consulta separada das listagens, com filtros combináveis por solicitante/destino/material, processo, fornecedor e datas; resultados paginados em 20 registros.
- Relatório com contagens, totais e valores agrupados por fornecedor.
- CSV em UTF-8 com BOM, separador `;` e vírgula decimal, respeitando os mesmos filtros e permissões do relatório. Exporta todo o resultado, independentemente da paginação.
- 36 testes automatizados, incluindo modelos, formulários, views, templates, permissões e migração da semana 2.

As datas inicial e final são inclusivas no fuso de São Paulo. Filtros inválidos exibem erros e impedem a exportação. Os valores são estimativas calculadas a partir do preço atual do item; quantidades de unidades diferentes não são somadas.

## Regras de acesso

| Recurso | Usuário comum | Superusuário |
| --- | --- | --- |
| Pedidos, painel de pedidos, consultas e relatórios | Somente os próprios pedidos | Todos, inclusive antigos sem responsável |
| Fornecedores | Consulta o catálogo; cria e altera os próprios cadastros | Administra todos |
| Perfil | Consulta e edita somente o próprio perfil | Edita o próprio perfil na interface; administra usuários pelo Admin |
| Processos e itens de referência | Consulta ao selecionar itens e filtros | Cadastro pelo Django Admin |

O responsável é definido pelo servidor ao criar um registro. Campos enviados manualmente como `criado_por`, `usuario`, `is_staff` e `is_superuser` não são aceitos pelos formulários comuns. A verificação de acesso ocorre também nas URLs de edição e exclusão. O saldo considera todos os pedidos do item, mesmo os que pertencem a outras contas.

## Modelagem e formulários

| Model | Papel |
| --- | --- |
| `Fornecedor` | Cadastro da empresa e proprietário do registro |
| `ProcessoLicitatorio` | Referência do processo e data do saldo |
| `ItemLicitado` | Material, processo, fornecedor, preço, unidade e saldo |
| `Pedido` | Solicitação de um item vinculada ao usuário responsável |
| `Perfil` | Setor e telefone ligados a um único usuário |

Relações 1:N: processo → itens, fornecedor → itens, item → pedidos e usuário → pedidos. Relação 1:1: `User` → `Perfil`. Relação N:N: `ProcessoLicitatorio.fornecedores`, com `through='ItemLicitado'`; preço, unidade, descrição e saldo são dados extras da relação. Um fornecedor pode ter vários itens no mesmo processo; use `.distinct()` quando quiser contar fornecedores únicos.

Há quatro `ModelForm`: `PedidoForm`, `FornecedorForm`, `PerfilForm` e `UsuarioForm`. O filtro usa um `Form` comum, pois não grava registros.

## Organização e telas

- `compras/models.py`: modelagem e validação de saldo.
- `compras/forms.py`: cadastros, perfil e validação de filtros.
- `compras/consultas.py`: escopo por usuário, filtros e agregações compartilhados.
- `compras/views.py` e `compras/urls.py`: fluxo das telas e exportação.
- `compras/tests.py`: testes unitários e de integração com Django Client.
- `templates/`: painel; listar/criar/editar/excluir pedido; listar/criar/editar/excluir fornecedor; login; perfil; consultas; relatório.
- `static/css/site.css` e `static/js/site.js`: interface responsiva e busca visual da listagem original.
- `compras/fixtures/`: exemplos fictícios; sem usuários ou credenciais.

A consulta nova é processada no servidor e distinta da busca visual já existente na lista de pedidos. O sistema ultrapassa as dez telas/fluxos mínimos do enunciado.

## Verificar a entrega

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

O teste de migração cria registros com o esquema da semana 2 e verifica sua preservação após a atualização. Os demais testes verificam regressão do CRUD, saldo, autenticação, bloqueio entre contas, CSRF, perfil, filtros de datas, paginação, totalização, CSV e neutralização de fórmulas no nome do fornecedor.

Veja o checklist e as capturas em [ENTREGA_SEMANA_5.md](ENTREGA_SEMANA_5.md). A entrega anterior permanece documentada em [ENTREGA_SEMANA_2.md](ENTREGA_SEMANA_2.md).

## Referências técnicas

Implementação baseada nos recursos nativos do Django 5.2: [autenticação](https://docs.djangoproject.com/en/5.2/topics/auth/default/), [relações com tabela intermediária](https://docs.djangoproject.com/en/5.2/topics/db/models/#extra-fields-on-many-to-many-relationships) e [agregações](https://docs.djangoproject.com/en/5.2/topics/db/aggregation/).
