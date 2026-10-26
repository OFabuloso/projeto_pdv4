from decimal import Decimal

from sqlalchemy.orm import Session

from interface.terminal import (
    SEPARADOR_QUANTIDADE,
    converter_inteiro,
    formatar_moeda,
    ler_decimal,
    separar_quantidade,
)
from models.turno_caixa import TurnoCaixa
from models.venda import FormaPagamento
from services.caixa import CaixaService

COMANDO_FINALIZAR = "f"
COMANDO_REMOVER = "r"
COMANDO_CANCELAR = "c"


def mostrar_carrinho(caixa: CaixaService) -> None:
    for item in caixa.itens:
        print(
            f"  {item.quantidade} x {item.produto.nome} "
            f"({formatar_moeda(item.produto.preco)}) = {formatar_moeda(item.subtotal)}"
        )
    print(f"  Total: {formatar_moeda(caixa.total())}")


def remover_do_carrinho(caixa: CaixaService) -> None:
    codigo_barras = input("Código do item a remover: ").strip()
    texto_quantidade = input("Quantidade a remover (Enter = todas): ").strip()
    quantidade = converter_inteiro(texto_quantidade) if texto_quantidade else None
    caixa.remover_item(codigo_barras, quantidade)


def registrar_itens(caixa: CaixaService) -> bool:
    """Lê itens até o operador finalizar (True) ou cancelar a venda (False)."""
    print(
        f"Digite o código de barras (ou quantidade{SEPARADOR_QUANTIDADE}código, "
        f"ex.: 3{SEPARADOR_QUANTIDADE}789). "
        f"Comandos: '{COMANDO_FINALIZAR}' finalizar, "
        f"'{COMANDO_REMOVER}' remover item, '{COMANDO_CANCELAR}' cancelar."
    )
    while True:
        entrada = input("> ").strip()
        comando = entrada.lower()
        try:
            if comando == COMANDO_FINALIZAR:
                if caixa.itens:
                    return True
                print("Nenhum item na venda.")
                continue
            if comando == COMANDO_CANCELAR:
                caixa.cancelar()
                return False
            if comando == COMANDO_REMOVER:
                remover_do_carrinho(caixa)
            elif entrada:
                codigo_barras, quantidade = separar_quantidade(entrada)
                caixa.adicionar_item(codigo_barras, quantidade)
            else:
                continue
            mostrar_carrinho(caixa)
        except ValueError as erro:
            print(f"Erro: {erro}")


def ler_forma_pagamento() -> FormaPagamento:
    opcoes = list(FormaPagamento)
    while True:
        for numero, forma in enumerate(opcoes, start=1):
            print(f"  {numero} - {forma.value}")
        escolha = input("Forma de pagamento: ").strip()
        if escolha.isdigit() and 1 <= int(escolha) <= len(opcoes):
            return opcoes[int(escolha) - 1]
        print("Opção inválida.")


def ler_valor_recebido(total_venda: Decimal) -> Decimal:
    while True:
        valor_recebido = ler_decimal("Valor recebido: ")
        if valor_recebido >= total_venda:
            return valor_recebido
        print(f"O valor deve ser de pelo menos {formatar_moeda(total_venda)}.")


def executar_venda(sessao: Session, turno: TurnoCaixa) -> None:
    caixa = CaixaService(sessao, turno)
    if not registrar_itens(caixa):
        print("Venda cancelada.")
        return
    forma_pagamento = ler_forma_pagamento()
    valor_recebido = None
    if forma_pagamento is FormaPagamento.DINHEIRO:
        valor_recebido = ler_valor_recebido(caixa.total())
    try:
        venda = caixa.finalizar(forma_pagamento, valor_recebido)
    except ValueError as erro:
        print(f"Erro: {erro} Venda cancelada.")
        return
    print(f"Venda #{venda.id} finalizada: {formatar_moeda(venda.total)}")
    if venda.troco > 0:
        print(f"Troco: {formatar_moeda(venda.troco)}")
