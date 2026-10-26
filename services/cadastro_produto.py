from decimal import Decimal

from sqlalchemy.orm import Session

from models.produto import Produto
from repositories.produto_repo import ProdutoRepository


class CadastroProdutoService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.produtos = ProdutoRepository(session)

    def _obter_ativo(self, codigo_barras: str) -> Produto:
        produto = self.produtos.buscar_por_codigo(codigo_barras)
        if produto is None:
            raise ValueError("Produto não encontrado.")
        return produto

    def _confirmar(self) -> None:
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def listar(self) -> list[Produto]:
        return self.produtos.listar_ativos()

    def cadastrar(
        self, codigo_barras: str, nome: str, preco: Decimal, estoque_inicial: int = 0
    ) -> Produto:
        codigo_barras = codigo_barras.strip()
        nome = nome.strip()
        if not codigo_barras:
            raise ValueError("Informe o código de barras.")
        if not nome:
            raise ValueError("Informe o nome do produto.")
        if preco < 0:
            raise ValueError("O preço não pode ser negativo.")
        if estoque_inicial < 0:
            raise ValueError("O estoque inicial não pode ser negativo.")
        if self.produtos.codigo_em_uso(codigo_barras):
            raise ValueError("Já existe um produto com este código de barras.")
        produto = Produto(
            codigo_barras=codigo_barras,
            nome=nome,
            preco=preco,
            estoque_atual=estoque_inicial,
        )
        try:
            self.produtos.adicionar(produto)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        return produto

    def alterar_preco(self, codigo_barras: str, novo_preco: Decimal) -> Produto:
        if novo_preco < 0:
            raise ValueError("O preço não pode ser negativo.")
        produto = self._obter_ativo(codigo_barras)
        produto.preco = novo_preco
        self._confirmar()
        return produto

    def repor_estoque(self, codigo_barras: str, quantidade: int) -> Produto:
        if quantidade <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")
        produto = self._obter_ativo(codigo_barras)
        self.produtos.repor_estoque(produto.id, quantidade)
        self._confirmar()
        # o UPDATE foi feito direto no banco: recarrega o valor atualizado
        self.session.refresh(produto)
        return produto

    def desativar(self, codigo_barras: str) -> None:
        produto = self._obter_ativo(codigo_barras)
        self.produtos.desativar_produto(produto.id)
        self._confirmar()
