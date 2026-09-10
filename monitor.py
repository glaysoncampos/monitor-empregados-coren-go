import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from config import PASTA_SITE
from extrator import extrair_empregados
from portal import (
    baixar_pdf,
    criar_conexao,
    descobrir_lista_mais_nova,
    localizar_pdf_mais_recente
)


def calcular_totais(empregados):
    totais = {
        "total": len(empregados),

        "concursados_efetivos": sum(
            empregado["efetivo"]
            for empregado in empregados
        ),

        "comissionados": sum(
            empregado["comissionado"]
            for empregado in empregados
        ),

        "funcao_gratificada": sum(
            empregado["funcao_gratificada"]
            for empregado in empregados
        ),

        "efetivo_cargo_comissao": sum(
            empregado["efetivo_cargo_comissao"]
            for empregado in empregados
        ),

        "nao_identificados": sum(
            empregado["categoria"]
            == "Não identificado"
            for empregado in empregados
        )
    }

    soma_principal = (
        totais["concursados_efetivos"]
        + totais["comissionados"]
        + totais["nao_identificados"]
    )

    if soma_principal != totais["total"]:
        raise RuntimeError(
            "Os totalizadores não fecharam. "
            "A atualização foi interrompida."
        )

    return totais


def salvar_json(
    pasta,
    empregados,
    totais,
    fonte,
    ano,
    pdf_bytes
):
    horario_brasilia = ZoneInfo(
        "America/Sao_Paulo"
    )

    dados = {
        "atualizado_em": datetime.now(
            horario_brasilia
        ).isoformat(),

        "ano": ano,

        "fonte": fonte,

        "pdf_sha256": hashlib.sha256(
            pdf_bytes
        ).hexdigest(),

        "totais": totais,

        "empregados": empregados
    }

    caminho = pasta / "dados.json"

    caminho.write_text(
        json.dumps(
            dados,
            ensure_ascii=False,
            indent=2
        ),
        encoding="utf-8"
    )


def salvar_csv(pasta, empregados):
    caminho = pasta / "empregados.csv"

    with caminho.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as arquivo:

        colunas = [
            "numero",
            "nome",
            "cargo",
            "categoria",
            "efetivo",
            "comissionado",
            "funcao_gratificada",
            "efetivo_cargo_comissao"
        ]

        escritor = csv.DictWriter(
            arquivo,
            fieldnames=colunas,
            delimiter=";"
        )

        escritor.writeheader()
        escritor.writerows(empregados)


def executar_monitor():
    print("Iniciando o monitor...")

    conexao = criar_conexao()

    ano, lista_id = (
        descobrir_lista_mais_nova(
            conexao
        )
    )

    print(
        f"Ano mais novo encontrado: {ano}"
    )

    fonte = localizar_pdf_mais_recente(
        conexao,
        lista_id
    )

    print(
        "Relatório selecionado: "
        f"{fonte['nome']}"
    )

    pdf_bytes = baixar_pdf(
        conexao,
        fonte["url"]
    )

    empregados = extrair_empregados(
        pdf_bytes
    )

    totais = calcular_totais(
        empregados
    )

    pasta = Path(PASTA_SITE)

    pasta.mkdir(
        parents=True,
        exist_ok=True
    )

    salvar_json(
        pasta,
        empregados,
        totais,
        fonte,
        ano,
        pdf_bytes
    )

    salvar_csv(
        pasta,
        empregados
    )

    print("Monitor concluído.")
    print(
        json.dumps(
            totais,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    executar_monitor()
