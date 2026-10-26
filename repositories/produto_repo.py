from sqlalchemy import select, update
from sqlalchemy.orm import Session

from models.produto import Produto


class ProdutoRepository:
    """Acesso a dados de Produto. Não faz commit: a transação é do serviço."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def buscar_por_codigo(self, codigo_barras: str) -> Produto | None:
        # produtos desativados não podem mais ser vendidos
        consulta = select(Produto).where(
            Produto.codigo_barras == codigo_barras, Produto.ativo.is_(True)
        )
        return self.session.scalars(consulta).first()

    def codigo_em_uso(self, codigo_barras: str) -> bool:
        # considera também os inativos, pois o código é único na tabela inteira
        consulta = select(Produto.id).where(Produto.codigo_barras == codigo_barras)
        return self.session.scalars(consulta).first() is not None

    def listar_ativos(self) -> list[Produto]:
        consulta = select(Produto).where(Produto.ativo.is_(True)).order_by(Produto.nome)
        return list(self.session.scalars(consulta))

    def adicionar(self, produto: Produto) -> None:
        self.session.add(produto)
        # flush gera o id sem encerrar a transação
        self.session.flush()

    def repor_estoque(self, produto_id: int, quantidade_reposta: int) -> None:
        """Soma ao estoque de forma atômica, sem sobrescrever vendas simultâneas."""
        comando = (
            update(Produto)
            .where(Produto.id == produto_id)
            .values(estoque_atual=Produto.estoque_atual + quantidade_reposta)
        )
        self.session.execute(comando)

    def baixar_estoque(self, produto_id: int, quantidade_vendida: int) -> bool:
        """Baixa o estoque de forma atômica; retorna False se não houver saldo.

        A subtração e a conferência acontecem num único UPDATE no banco, então
        dois caixas vendendo o mesmo produto ao mesmo tempo não se sobrescrevem.
        """
        comando = (
            update(Produto)
            .where(
                Produto.id == produto_id,
                Produto.estoque_atual >= quantidade_vendida,
            )
            .values(estoque_atual=Produto.estoque_atual - quantidade_vendida)
            .returning(Produto.id)
        )
        produto_atualizado = self.session.execute(comando).scalar_one_or_none()
        return produto_atualizado is not None

    def desativar_produto(self, produto_id: int) -> bool:
        """Exclusão lógica: marca o produto como inativo, sem apagar o histórico."""
        produto = self.session.get(Produto, produto_id)
        if produto is None or not produto.ativo:
            return False
        produto.ativo = False
        return True
