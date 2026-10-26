from decimal import Decimal

import pytest

from interface.terminal import converter_decimal, formatar_moeda, separar_quantidade


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        (Decimal("0"), "R$ 0,00"),
        (Decimal("10.5"), "R$ 10,50"),
        (Decimal("1234567.89"), "R$ 1.234.567,89"),
    ],
)
def test_formatar_moeda(valor: Decimal, esperado: str) -> None:
    assert formatar_moeda(valor) == esperado


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [("10,50", Decimal("10.50")), (" 3.2 ", Decimal("3.2")), ("7", Decimal("7"))],
)
def test_converter_decimal(texto: str, esperado: Decimal) -> None:
    assert converter_decimal(texto) == esperado


@pytest.mark.parametrize("texto", ["", "abc", "1,234", "NaN", "inf"])
def test_converter_decimal_invalido(texto: str) -> None:
    with pytest.raises(ValueError, match="Valor inválido"):
        converter_decimal(texto)


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [("789", ("789", 1)), ("3*789", ("789", 3)), (" 2 * 789 ", ("789", 2))],
)
def test_separar_quantidade(entrada: str, esperado: tuple[str, int]) -> None:
    assert separar_quantidade(entrada) == esperado


@pytest.mark.parametrize("entrada", ["a*789", "*789", "1.5*789"])
def test_separar_quantidade_invalida(entrada: str) -> None:
    with pytest.raises(ValueError, match="Número inválido"):
        separar_quantidade(entrada)
