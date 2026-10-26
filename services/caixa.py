from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.orm import Session

from models.produto import Produto
from models.turno_caixa import TurnoCaixa
from models.venda import FormaPagamento, ItemVenda, Venda
from repositories.produto_repo import ProdutoRepository


@dataclass
class ItemCarrinho:
    produto: Produto
    quantidade: int

    @property
    def subtotal(self) -> Decimal:
        return self.produto.preco * self.quantidade


class CaixaService:
    def __init__(self, session: Session, turno: TurnoCaixa) -> None:
        self.session = session
        self.turno = turno
        self.produtos = ProdutoRepository(session)
        self.itens: list[ItemCarrinho] = []

    def _buscar_item_no_carrinho(self, produto: Produto) -> ItemCarrinho | None:
        for item in self.itens:
            if item.produto.id == produto.id:
                return item
        return None

    def adicionar_item(self, codigo_barras: str, quantidade: int = 1) -> Produto:
        if quantidade <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")
        produto = self.produtos.buscar_por_codigo(codigo_barras)
        if produto is None:
            raise ValueError("Produto não encontrado.")

        # o estoque precisa cobrir o que já está no carrinho mais o novo item
        item_existente = self._buscar_item_no_carrinho(produto)
        quantidade_no_carrinho = item_existente.quantidade if item_existente else 0
        if produto.estoque_atual < quantidade_no_carrinho + quantidade:
            raise ValueError("Estoque insuficiente.")

        # o mesmo produto bipado de novo soma na mesma linha
        if item_existente:
            item_existente.quantidade += quantidade
        else:
            self.itens.append(ItemCarrinho(produto, quantidade))
        return produto

    def remover_item(self, codigo_barras: str, quantidade: int | None = None) -> None:
        """Tira unidades do carrinho; sem quantidade, remove a linha inteira."""
        item = next(
            (
                item_carrinho
                for item_carrinho in self.itens
                if item_carrinho.produto.codigo_barras == codigo_barras
            ),
            None,
        )
        if item is None:
            raise ValueError("Produto não está na venda.")
        if quantidade is None or quantidade == item.quantidade:
            self.itens.remove(item)
            return
        if quantidade <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")
        if quantidade > item.quantidade:
            raise ValueError(f"A venda tem só {item.quantidade} unidade(s) do produto.")
        item.quantidade -= quantidade

    def total(self) -> Decimal:
        return sum((item.subtotal for item in self.itens), Decimal("0"))

    def cancelar(self) -> None:
        self.itens.clear()

    def finalizar(
        self, forma_pagamento: FormaPagamento, valor_recebido: Decimal | None = None
    ) -> Venda:
        """Grava a venda. Em dinheiro, valor_recebido é obrigatório (para o troco)."""
        if not self.itens:
            raise ValueError("Venda vazia.")
        if not self.turno.aberto:
            raise ValueError("O caixa está fechado.")
        total_venda = self.total()
        if forma_pagamento is FormaPagamento.DINHEIRO:
            if valor_recebido is None or valor_recebido < total_venda:
                raise ValueError("Valor recebido menor que o total da venda.")
        else:
            # cartão e pix são cobrados no valor exato: não há troco
            valor_recebido = None
        try:
            venda = Venda(
                total=total_venda,
                forma_pagamento=forma_pagamento,
                valor_recebido=valor_recebido,
                turno_caixa_id=self.turno.id,
            )
            for item in self.itens:
                # confere de novo no banco: outro caixa pode ter vendido antes
                if not self.produtos.baixar_estoque(item.produto.id, item.quantidade):
                    raise ValueError(f"Estoque insuficiente para {item.produto.nome}.")
                venda.itens.append(
                    ItemVenda(
                        produto_id=item.produto.id,
                        quantidade=item.quantidade,
                        preco_unitario=item.produto.preco,
                    )
                )
            self.session.add(venda)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        self.itens.clear()
        return venda
