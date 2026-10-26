# importa todos os modelos para registrar as tabelas no Base.metadata
from models.produto import Produto
from models.turno_caixa import TurnoCaixa
from models.venda import FormaPagamento, ItemVenda, Venda

__all__ = ["FormaPagamento", "ItemVenda", "Produto", "TurnoCaixa", "Venda"]
