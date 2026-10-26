from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from interface.caixa import abrir_caixa, fechar_caixa, relatorio_do_dia
from interface.produtos import menu_produtos
from interface.venda import executar_venda
from models.base import criar_engine, criar_fabrica_sessoes
from services.turno_caixa import TurnoCaixaService

OPCAO_VENDA = "1"
OPCAO_CAIXA = "2"
OPCAO_PRODUTOS = "3"
OPCAO_RELATORIO = "4"
OPCAO_SAIR = "0"


def executar_opcao(sessao: Session, escolha: str) -> None:
    turno = TurnoCaixaService(sessao).turno_aberto()
    if escolha == OPCAO_VENDA:
        if turno is None:
            print("Abra o caixa antes de vender.")
        else:
            executar_venda(sessao, turno)
    elif escolha == OPCAO_CAIXA:
        if turno is None:
            abrir_caixa(sessao)
        else:
            fechar_caixa(sessao, turno)
    elif escolha == OPCAO_PRODUTOS:
        menu_produtos(sessao)
    elif escolha == OPCAO_RELATORIO:
        relatorio_do_dia(sessao)
    else:
        print("Opção inválida.")


def mostrar_menu(sessao: Session) -> None:
    turno = TurnoCaixaService(sessao).turno_aberto()
    situacao = f"aberto por {turno.operador}" if turno else "fechado"
    print(f"\n=== PDV (caixa {situacao}) ===")
    print(f"{OPCAO_VENDA} - Nova venda")
    print(f"{OPCAO_CAIXA} - {'Fechar' if turno else 'Abrir'} caixa")
    print(f"{OPCAO_PRODUTOS} - Produtos")
    print(f"{OPCAO_RELATORIO} - Relatório do dia")
    print(f"{OPCAO_SAIR} - Sair")


def main() -> None:
    fabrica_sessoes = criar_fabrica_sessoes(criar_engine())
    with fabrica_sessoes() as sessao:
        while True:
            try:
                mostrar_menu(sessao)
                escolha = input("Opção: ").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                return
            except SQLAlchemyError as erro:
                print(f"Erro no banco de dados: {erro}")
                return
            if escolha == OPCAO_SAIR:
                return
            try:
                executar_opcao(sessao, escolha)
            except (KeyboardInterrupt, EOFError):
                print("\nOperação cancelada.")
            except ValueError as erro:
                print(f"Erro: {erro}")
            except SQLAlchemyError as erro:
                sessao.rollback()
                print(f"Erro no banco de dados: {erro}")


if __name__ == "__main__":
    main()
