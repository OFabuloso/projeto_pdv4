from datetime import date

from sqlalchemy.orm import Session

from interface.terminal import formatar_moeda, ler_decimal
from models.turno_caixa import TurnoCaixa
from services.relatorio import RelatorioService, RelatorioVendas
from services.turno_caixa import TurnoCaixaService


def mostrar_relatorio(relatorio: RelatorioVendas) -> None:
    if not relatorio.linhas:
        print("Nenhuma venda.")
        return
    for linha in relatorio.linhas:
        print(
            f"  {linha.forma_pagamento.value}: {linha.quantidade_vendas} venda(s), "
            f"{formatar_moeda(linha.total)}"
        )
    print(
        f"  Total: {relatorio.quantidade_vendas} venda(s), "
        f"{formatar_moeda(relatorio.total_geral)}"
    )


def abrir_caixa(sessao: Session) -> None:
    operador = input("Nome do operador: ")
    valor_abertura = ler_decimal("Troco inicial na gaveta: ")
    turno = TurnoCaixaService(sessao).abrir(operador, valor_abertura)
    print(f"Caixa aberto por {turno.operador}.")


def fechar_caixa(sessao: Session, turno: TurnoCaixa) -> None:
    valor_contado = ler_decimal("Dinheiro contado na gaveta: ")
    resumo = TurnoCaixaService(sessao).fechar(turno, valor_contado)
    print("\n--- Fechamento de caixa ---")
    mostrar_relatorio(resumo.vendas)
    print(f"  Esperado em dinheiro: {formatar_moeda(resumo.esperado_em_dinheiro)}")
    print(f"  Contado: {formatar_moeda(valor_contado)}")
    if resumo.diferenca > 0:
        print(f"  Sobra: {formatar_moeda(resumo.diferenca)}")
    elif resumo.diferenca < 0:
        print(f"  Falta: {formatar_moeda(-resumo.diferenca)}")
    else:
        print("  Caixa confere.")


def relatorio_do_dia(sessao: Session) -> None:
    hoje = date.today()
    print(f"\n--- Vendas de {hoje:%d/%m/%Y} ---")
    mostrar_relatorio(RelatorioService(sessao).vendas_do_dia(hoje))
