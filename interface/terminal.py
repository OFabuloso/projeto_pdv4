"""Leitura de dados digitados pelo operador e formatação para exibição."""

from decimal import Decimal, InvalidOperation

CENTAVOS = Decimal("0.01")
SEPARADOR_QUANTIDADE = "*"


def formatar_moeda(valor: Decimal) -> str:
    # 1234.5 -> "R$ 1.234,50" (padrão brasileiro)
    texto = f"{valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {texto}"


def converter_decimal(texto: str) -> Decimal:
    """Converte "10,50" ou "10.50" em Decimal; aceita no máximo 2 casas."""
    try:
        valor = Decimal(texto.strip().replace(",", "."))
    except InvalidOperation as erro:
        raise ValueError("Valor inválido.") from erro
    if not valor.is_finite() or valor != valor.quantize(CENTAVOS):
        raise ValueError("Valor inválido.")
    return valor


def converter_inteiro(texto: str) -> int:
    texto = texto.strip()
    if not texto.lstrip("-").isdigit():
        raise ValueError("Número inválido.")
    return int(texto)


def separar_quantidade(entrada: str) -> tuple[str, int]:
    """Lê "3*789" como 3 unidades do código 789; sem "*", a quantidade é 1."""
    if SEPARADOR_QUANTIDADE not in entrada:
        return entrada.strip(), 1
    texto_quantidade, codigo_barras = entrada.split(SEPARADOR_QUANTIDADE, 1)
    return codigo_barras.strip(), converter_inteiro(texto_quantidade)


def ler_decimal(mensagem: str) -> Decimal:
    while True:
        try:
            return converter_decimal(input(mensagem))
        except ValueError as erro:
            print(erro)


def ler_inteiro(mensagem: str) -> int:
    while True:
        try:
            return converter_inteiro(input(mensagem))
        except ValueError as erro:
            print(erro)


def confirmar(mensagem: str) -> bool:
    return input(f"{mensagem} (s/n): ").strip().lower() == "s"
