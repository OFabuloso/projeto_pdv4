# Projeto PDV

Um ponto de venda (PDV) simples, que roda no terminal, feito em Python com SQLAlchemy e PostgreSQL.

## Antes de tudo: por que esse projeto existe

Esse projeto **não é um produto** e não foi feito para ser usado num comércio de verdade. Ele existe porque eu quero aprender, e um PDV me pareceu um bom pretexto: tem regra de negócio de verdade (estoque, troco, fechamento de caixa), tem banco de dados e tem bastante coisa que pode dar errado.

Os três assuntos que estou estudando aqui são:

- **Python**: escrever código organizado, com tipagem, testes e seguindo a PEP 8, em vez de "só funcionar".
- **ORM**: entender o SQLAlchemy 2.0 de verdade (models, relacionamentos, sessões, transações) e o Alembic para versionar o banco por migrações.
- **Uso de IA no desenvolvimento**: boa parte do código foi escrita junto com uma IA (o Claude Code). A ideia não é deixar ela fazer tudo, e sim aprender a trabalhar com ela: pedir uma revisão, entender por que ela sugeriu algo, discordar quando faz sentido e conferir tudo com testes. O arquivo `relatorio_projeto_pdv(1).txt` é um exemplo disso: é uma revisão que a IA fez do código, com os erros que ela encontrou e que depois foram corrigidos um por um.

Então, se você encontrar algo estranho por aqui, pode ser justamente a parte que eu ainda estou aprendendo. Sugestões são muito bem-vindas.

## O que ele faz hoje

- Abre e fecha o caixa, conferindo no fechamento se o dinheiro da gaveta bate com o esperado
- Registra vendas pelo código de barras, com quantidade, remoção de item e cancelamento
- Aceita dinheiro, Pix e cartão de débito ou crédito, e calcula o troco no dinheiro
- Cadastra produtos, altera preço, repõe estoque e desativa produtos
- Mostra um relatório das vendas do dia, separado por forma de pagamento
- Não deixa o estoque ficar negativo, nem quando dois caixas vendem o mesmo produto ao mesmo tempo

## O que você precisa ter instalado

- Python 3.12
- PostgreSQL rodando na sua máquina
- Git

## Como rodar

### 1. Clonar e criar o ambiente virtual

```bash
git clone git@github.com:OFabuloso/projeto_pdv4.git
cd projeto_pdv4

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Se quiser rodar os testes e as ferramentas de qualidade, instale também as dependências de desenvolvimento:

```bash
pip install -r requirements-dev.txt
```

### 2. Criar o banco

Crie um banco vazio no PostgreSQL (troque `postgres` pelo seu usuário, se for outro):

```bash
createdb -h localhost -U postgres projeto_pdv
```

### 3. Dizer ao projeto onde está o banco

A senha do banco não fica no código. O projeto lê a conexão da variável de ambiente `PDV_DATABASE_URL`:

```bash
export PDV_DATABASE_URL="postgresql+psycopg2://usuario:senha@localhost/projeto_pdv"
```

Para não precisar repetir isso toda vez, coloque essa linha no seu `~/.bashrc`. Só não coloque num arquivo que vá para o Git.

### 4. Criar as tabelas

As tabelas são criadas pelas migrações do Alembic:

```bash
alembic upgrade head
```

### 5. Abrir o PDV

```bash
python main.py
```

## Como usar

Ao abrir, aparece o menu principal:

```
=== PDV (caixa fechado) ===
1 - Nova venda
2 - Abrir caixa
3 - Produtos
4 - Relatório do dia
0 - Sair
```

Um caminho bom para testar pela primeira vez:

1. **Cadastre um produto** em `3 - Produtos` → `2 - Cadastrar produto`. Preço pode ser digitado com vírgula (`10,50`).
2. **Abra o caixa** em `2`, informando seu nome e quanto de troco tem na gaveta.
3. **Faça uma venda** em `1`. Dentro da venda:

   | O que digitar | O que acontece |
   | --- | --- |
   | `789` | adiciona 1 unidade do produto com código 789 |
   | `3*789` | adiciona 3 unidades |
   | `r` | remove um item (ou só algumas unidades dele) |
   | `c` | cancela a venda |
   | `f` | finaliza e vai para o pagamento |

   Se o pagamento for em dinheiro, o programa pede o valor recebido e mostra o troco.
4. **Veja o relatório** em `4` para conferir o que foi vendido no dia.
5. **Feche o caixa** em `2`, contando o dinheiro da gaveta. O programa diz se sobrou, se faltou ou se o caixa confere.

`Ctrl+C` cancela a operação atual e volta para o menu. No menu principal, ele fecha o programa.

## Testes e qualidade de código

Os testes usam um SQLite em memória, então não precisam do PostgreSQL:

```bash
pytest           # roda os testes
ruff check .     # aponta problemas de estilo e possíveis bugs
ruff format .    # formata o código
mypy --strict .  # confere a tipagem
```

## Como o código está organizado

Separei o projeto em camadas, porque essa foi uma das coisas que eu quis praticar:

```
models/        tabelas do banco (SQLAlchemy)
repositories/  consultas e gravações no banco, sem regra de negócio
services/      regras de negócio: venda, caixa, cadastro, relatório
interface/     telas do terminal (o que o operador vê e digita)
migrations/    histórico de mudanças do banco (Alembic)
tests/         testes automatizados (pytest)
main.py        menu principal
```

A regra que tento seguir: quem conversa com o operador é a `interface`, quem decide as coisas são os `services`, e só os `repositories` falam com o banco.

## Próximos passos (e próximos estudos)

Ainda não sei exatamente para onde isso vai, mas algumas ideias que quero explorar:

- Login de operadores
- Categorias de produtos
- Relatórios por período e produtos mais vendidos
- Talvez uma interface web, para estudar uma API em cima dessas mesmas camadas

Cada coisa nova vai entrar do mesmo jeito que as anteriores: estudando, testando e usando a IA como parceira de estudo, não como atalho.
