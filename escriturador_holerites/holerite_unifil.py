#!/usr/bin/env python3

from dataclasses import dataclass
from decimal import Decimal
from typing import List
from datetime import date

from bs4 import BeautifulSoup, SoupStrainer
from babel.numbers import parse_decimal


@dataclass
class Entrada:
    codigo: int
    descricao: str
    referencia: Decimal
    valor: Decimal

    @staticmethod
    def construir_de_soup_tr(soup_tr):
        cod, desc, ref, vencimento, desconto = (
            td.string.strip() if td.string else "" for td in soup_tr.find_all("td")
        )

        valor = vencimento if vencimento else f"-{desconto}"

        return Entrada(int(cod), desc, Decimal(ref), _decimal_brl(valor))

    @staticmethod
    def construir_de_soup_table(soup_table):
        return [
            Entrada.construir_de_soup_tr(soup_tr) for soup_tr in soup_table.tbody("tr")
        ]


@dataclass
class Vencimento(Entrada):
    vencimento: Decimal


@dataclass
class Desconto(Entrada):
    desconto: Decimal


@dataclass
class HoleriteUniFil:
    referencia: date
    salario_base: Decimal
    base_contrib_inss: Decimal
    base_contrib_irrf: Decimal
    faixa_irrf: int
    base_calc_fgts: Decimal
    valor_fgts: Decimal
    registro_total_vencimentos: Decimal
    registro_total_descontos: Decimal
    registro_valor_liquido: Decimal
    entradas: List[Entrada]

    @staticmethod
    def construir_de_fonte(fonte_html):
        holerite_parser = BeautifulSoup(
            fonte_html, "html.parser", parse_only=SoupStrainer("table")
        )

        # A primeira contém o demonstrativo das entradas, e a segunda a sumarização
        tabela_entradas, tabela_sumario = holerite_parser.find_all("table")

        # Escolhendo todos os td's e filtrando os falsos-cabeçalhos
        celulas_sumario = [
            str(td.string)
            for td in _list_pop_range(tabela_sumario.tbody.find_all("td"), 5, 9)
        ]

        return HoleriteUniFil(
            referencia=date(2020, 5, 1),
            salario_base=_decimal_brl(celulas_sumario[0]),
            base_contrib_inss=_decimal_brl(celulas_sumario[1]),
            base_contrib_irrf=int(celulas_sumario[2]),
            faixa_irrf=_decimal_brl(celulas_sumario[3]),
            base_calc_fgts=_decimal_brl(celulas_sumario[4]),
            valor_fgts=_decimal_brl(celulas_sumario[5]),
            registro_total_vencimentos=_decimal_brl(celulas_sumario[6]),
            registro_total_descontos=_decimal_brl(celulas_sumario[7]),
            registro_valor_liquido=_decimal_brl(celulas_sumario[8]),
            entradas=Entrada.construir_de_soup_table(tabela_entradas),
        )


def _list_pop_range(xs, start, end):
    return xs[:start] + xs[end:]


def _decimal_brl(valor):
    return parse_decimal(valor, locale="pt_BR")
