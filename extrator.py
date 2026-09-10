import io
import re
import unicodedata

import pdfplumber


def normalizar(texto):
    texto = " ".join(
        str(texto or "")
        .replace("\n", " ")
        .split()
    ).lower()

    return "".join(
        caractere
        for caractere in unicodedata.normalize(
            "NFD",
            texto
        )
        if unicodedata.category(caractere) != "Mn"
    )


def identificar_colunas(cabecalho):
    colunas = {}

    for indice, celula in enumerate(cabecalho):
        texto = normalizar(celula)

        if indice == 0 and (
            "n" in texto
            or "numero" in texto
        ):
            colunas["numero"] = indice

        elif (
            "funcionario" in texto
            or "empregado" in texto
        ):
            colunas["funcionario"] = indice

        elif (
            "funcao" in texto
            and "gratificada" in texto
        ):
            colunas["funcao_gratificada"] = indice

        elif (
            "efetivo" in texto
            and "cargo" in texto
            and "comissao" in texto
        ):
            colunas["efetivo_cargo_comissao"] = indice

        elif texto in (
            "efetivos",
            "efetivo"
        ):
            colunas["efetivo"] = indice

        elif texto in (
            "comissionados",
            "comissionado"
        ):
            colunas["comissionado"] = indice

        elif "cargo" in texto:
            colunas["cargo"] = indice

    return colunas


def ler_celula(linha, indice):
    if indice is None or indice >= len(linha):
        return ""

    return " ".join(
        str(linha[indice] or "")
        .replace("\n", " ")
        .split()
    )


def classificar_linha(linha, colunas):
    numero = ler_celula(
        linha,
        colunas.get("numero")
    )

    if not re.fullmatch(r"\d+", numero):
        return None

    nome = ler_celula(
        linha,
        colunas.get("funcionario")
    )

    cargo = ler_celula(
        linha,
        colunas.get("cargo")
    )

    funcao = ler_celula(
        linha,
        colunas.get("funcao_gratificada")
    )

    cargo_comissao = ler_celula(
        linha,
        colunas.get(
            "efetivo_cargo_comissao"
        )
    )

    coluna_efetivo = ler_celula(
        linha,
        colunas.get("efetivo")
    )

    coluna_comissionado = ler_celula(
        linha,
        colunas.get("comissionado")
    )

    tem_funcao = bool(funcao.strip())

    tem_cargo_comissao = bool(
        cargo_comissao.strip()
    )

    e_efetivo = bool(
        coluna_efetivo.strip()
        or tem_funcao
        or tem_cargo_comissao
    )

    e_comissionado = bool(
        coluna_comissionado.strip()
    ) and not e_efetivo

    if tem_funcao:
        categoria = (
            "Efetivo com função gratificada"
        )

    elif tem_cargo_comissao:
        categoria = (
            "Efetivo com cargo em comissão"
        )

    elif e_efetivo:
        categoria = "Efetivo"

    elif e_comissionado:
        categoria = "Comissionado"

    else:
        categoria = "Não identificado"

    return {
        "numero": int(numero),
        "nome": nome,
        "cargo": cargo,
        "categoria": categoria,
        "efetivo": e_efetivo,
        "comissionado": e_comissionado,
        "funcao_gratificada": tem_funcao,
        "efetivo_cargo_comissao": (
            tem_cargo_comissao
        )
    }


def extrair_empregados(pdf_bytes):
    empregados = []
    colunas = None

    with pdfplumber.open(
        io.BytesIO(pdf_bytes)
    ) as documento:

        for pagina in documento.pages:
            tabelas = pagina.extract_tables()

            for tabela in tabelas:
                for linha in tabela:
                    if not linha:
                        continue

                    cabecalho = identificar_colunas(
                        linha
                    )

                    if (
                        "funcionario" in cabecalho
                        and "cargo" in cabecalho
                    ):
                        colunas = cabecalho
                        continue

                    if not colunas:
                        continue

                    empregado = classificar_linha(
                        linha,
                        colunas
                    )

                    if empregado:
                        empregados.append(
                            empregado
                        )

    empregados_unicos = {
        empregado["numero"]: empregado
        for empregado in empregados
    }

    resultado = [
        empregados_unicos[numero]
        for numero in sorted(
            empregados_unicos
        )
    ]

    if len(resultado) < 5:
        raise RuntimeError(
            "A estrutura da tabela mudou e "
            "os dados não puderam ser lidos "
            "com segurança."
        )

    return resultado
