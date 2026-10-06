# Controle de pedidos de materiais

Projeto Django local para registrar pedidos de material do setor de obras. Esta primeira etapa cobre a modelagem inicial, um painel com dados do banco e o CRUD completo de pedidos, seguindo o padrão Model–View–Template trabalhado na disciplina.

Os dados de exemplo são fictícios. Não coloque relatórios, autorizações assinadas ou dados reais da prefeitura no GitHub. Esta etapa ainda não importa PDFs nem emite autorizações; o saldo é cadastrado manualmente e precisa ser conferido com o relatório atualizado antes de qualquer uso real.

## Abrir nesta máquina

O ambiente virtual já está na pasta do projeto. No PowerShell, execute:

```powershell
cd C:\Users\Leonardo\Desktop\sistema_prefeitura
.\.venv\Scripts\python.exe manage.py runserver
```

Abra `http://127.0.0.1:8000/`.

## Preparar uma cópia nova no Windows

Com Python instalado, execute na pasta do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py loaddata exemplo
python manage.py runserver
```

O arquivo `compras/fixtures/exemplo.json` contém apenas dados fictícios para demonstração. Carregue-o somente em um banco de testes vazio.

Se o PowerShell bloquear a ativação, use o Python do ambiente diretamente: `.\.venv\Scripts\python.exe manage.py runserver`. Os demais comandos `python` podem ser executados do mesmo modo.

## O que foi implementado

- Quatro models: `Fornecedor`, `ProcessoLicitatorio`, `ItemLicitado` e `Pedido`.
- Relacionamentos 1:N: processo → itens, fornecedor → itens e item → pedidos.
- Painel inicial com contagens e valor estimado calculados a partir do banco.
- CRUD completo de `Pedido`: listagem, cadastro, edição e exclusão com confirmação.
- Formulário `ModelForm` e uma validação no model para impedir quantidade acima do saldo informado.
- Cadastro de processos, fornecedores e itens pelo Django Admin, para preparar os dados de referência.
- Busca visual na lista, feita apenas no navegador, sem ampliar o backend.

Cada pedido se refere a um item. A futura autorização poderá reunir vários pedidos do mesmo processo e fornecedor, como no pré-mockup fornecido para o projeto real.

## Organização do código

- `compras/models.py`: quatro tabelas e uma regra de validação do saldo.
- `compras/forms.py`: formulário do pedido.
- `compras/views.py`: funções que consultam os dados e mostram as telas.
- `compras/urls.py`: rotas do app.
- `templates/`: páginas HTML.
- `static/css/site.css` e `static/js/site.js`: interface e busca visual da lista.
- `compras/fixtures/exemplo.json`: registros fictícios de demonstração.

Para verificar a entrega:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
```

## Entrega semanal

O repositório deve incluir o código e `requirements.txt`. A pasta `.venv`, o banco local `db.sqlite3`, a chave local e arquivos reais ficam fora do Git. Além da tag da semana, o enunciado pede uma captura da funcionalidade funcionando e um checklist dos requisitos cumpridos.
