from sqlalchemy.orm import Session

from interface.terminal import confirmar, formatar_moeda, ler_decimal, ler_inteiro
from services.cadastro_produto import CadastroProdutoService


def listar_produtos(cadastro: CadastroProdutoService) -> None:
    produtos = cadastro.listar()
    if not produtos:
        print("Nenhum produto cadastrado.")
    for produto in produtos:
        print(
            f"  {produto.codigo_barras} | {produto.nome} | "
            f"{formatar_moeda(produto.preco)} | estoque: {produto.estoque_atual}"
        )


def cadastrar_produto(cadastro: CadastroProdutoService) -> None:
    codigo_barras = input("Código de barras: ")
    nome = input("Nome: ")
    preco = ler_decimal("Preço: ")
    estoque_inicial = ler_inteiro("Estoque inicial: ")
    produto = cadastro.cadastrar(codigo_barras, nome, preco, estoque_inicial)
    print(f"Produto '{produto.nome}' cadastrado.")


def alterar_preco(cadastro: CadastroProdutoService) -> None:
    codigo_barras = input("Código de barras: ")
    novo_preco = ler_decimal("Novo preço: ")
    produto = cadastro.alterar_preco(codigo_barras, novo_preco)
    print(f"Preço de '{produto.nome}' agora é {formatar_moeda(produto.preco)}.")


def repor_estoque(cadastro: CadastroProdutoService) -> None:
    codigo_barras = input("Código de barras: ")
    quantidade = ler_inteiro("Quantidade a repor: ")
    produto = cadastro.repor_estoque(codigo_barras, quantidade)
    print(f"Estoque de '{produto.nome}': {produto.estoque_atual}.")


def desativar_produto(cadastro: CadastroProdutoService) -> None:
    codigo_barras = input("Código de barras: ")
    if confirmar("O produto deixará de ser vendido. Confirma?"):
        cadastro.desativar(codigo_barras)
        print("Produto desativado.")


ACOES_PRODUTOS = {
    "1": ("Listar produtos", listar_produtos),
    "2": ("Cadastrar produto", cadastrar_produto),
    "3": ("Alterar preço", alterar_preco),
    "4": ("Repor estoque", repor_estoque),
    "5": ("Desativar produto", desativar_produto),
}


def menu_produtos(sessao: Session) -> None:
    cadastro = CadastroProdutoService(sessao)
    while True:
        print("\n--- Produtos ---")
        for opcao, (descricao, _acao) in ACOES_PRODUTOS.items():
            print(f"{opcao} - {descricao}")
        print("0 - Voltar")
        escolha = input("Opção: ").strip()
        if escolha == "0":
            return
        if escolha not in ACOES_PRODUTOS:
            print("Opção inválida.")
            continue
        _descricao, acao = ACOES_PRODUTOS[escolha]
        try:
            acao(cadastro)
        except ValueError as erro:
            print(f"Erro: {erro}")
