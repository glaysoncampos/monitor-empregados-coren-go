import io
import re
import unicodedata

import pdfplumber


def normalizar(texto):
    """
    Padroniza o texto para facilitar comparações.

    Exemplo:
    'Função Gratificada' -> 'funcao gratificada'
    """

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


def limpar_texto(texto):
    """
    Remove quebras de linha e espaços desnecessários,
    mas mantém acentos e letras originais.
    """

    return " ".join(
        str(texto or "")
        .replace("\n", " ")
        .split()
    )


def identificar_colunas(cabecalho):
    """
    Identifica as colunas pelo nome do cabeçalho,
    sem depender da posição fixa delas.
    """

    colunas = {}

    for indice, celula in enumerate(cabecalho):
        texto = normalizar(celula)

        if indice == 0 and (
            texto in ("n", "nº", "numero")
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
            colunas[
                "efetivo_cargo_comissao"
            ] = indice

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
    """
    Retorna o conteúdo de uma célula.
    """

    if indice is None:
        return ""

    if indice >= len(linha):
        return ""

    return limpar_texto(
        linha[indice]
    )


def contem_estagiario(*textos):
    """
    Identifica estagiário ou estagiária
    pelo conteúdo publicado na tabela.
    """

    texto = normalizar(
        " ".join(
            str(valor or "")
            for valor in textos
        )
    )

    return "estagiari" in texto


def validar_funcao_gratificada(texto):
    """
    Só considera função gratificada quando
    o conteúdo realmente indicar essa condição.

    Evita interpretar palavras soltas que
    vazaram de outra linha do PDF.
    """

    texto = normalizar(texto)

    if not texto:
        return False

    return (
        "funcao" in texto
        or "gratificada" in texto
        or (
            "efetivo" in texto
            and "exercendo" in texto
        )
    )


def validar_cargo_comissao(texto):
    """
    Só considera efetivo em cargo em comissão
    quando há indicação real dessa condição.
    """

    texto = normalizar(texto)

    if not texto:
        return False

    return (
        "comissao" in texto
        or (
            "efetivo" in texto
            and "exercendo" in texto
        )
    )


def validar_efetivo(texto):
    """
    Verifica se a coluna de efetivos realmente
    informa vínculo efetivo.
    """

    texto = normalizar(texto)

    if not texto:
        return False

    return "efetivo" in texto


def validar_comissionado(texto):
    """
    Verifica se a coluna de comissionados
    realmente informa cargo comissionado.
    """

    texto = normalizar(texto)

    if not texto:
        return False

    return (
        "comissionado" in texto
        or "comissionados" in texto
    )


def classificar_linha(linha, colunas):
    """
    Interpreta uma linha da tabela.

    A classificação respeita o que está
    publicado na tabela mais recente.
    """

    numero = ler_celula(
        linha,
        colunas.get("numero")
    )

    if not re.fullmatch(
        r"\d+",
        numero
    ):
        return None

    nome = ler_celula(
        linha,
        colunas.get("funcionario")
    )

    cargo = ler_celula(
        linha,
        colunas.get("cargo")
    )

    coluna_funcao = ler_celula(
        linha,
        colunas.get(
            "funcao_gratificada"
        )
    )

    coluna_cargo_comissao = ler_celula(
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

    # ==============================
    # ESTAGIÁRIO
    # ==============================

    e_estagiario = contem_estagiario(
        cargo,
        coluna_efetivo,
        coluna_comissionado,
        coluna_funcao,
        coluna_cargo_comissao
    )

    # ==============================
    # INDICADORES DA LINHA
    # ==============================

    tem_comissionado = (
        validar_comissionado(
            coluna_comissionado
        )
    )

    tem_funcao = (
        validar_funcao_gratificada(
            coluna_funcao
        )
    )

    tem_cargo_comissao = (
        validar_cargo_comissao(
            coluna_cargo_comissao
        )
    )

    tem_efetivo = (
        validar_efetivo(
            coluna_efetivo
        )
    )

    # ==============================
    # REGRA DE CLASSIFICAÇÃO
    # ==============================

    if e_estagiario:
        categoria = "Estagiário"

        e_efetivo = False
        e_comissionado = False
        tem_funcao = False
        tem_cargo_comissao = False

    elif tem_comissionado:
        """
        A coluna oficial de Comissionados
        tem prioridade.

        Isso resolve casos como Fernanda
        Joyce, em que um texto da linha
        anterior invade outra coluna.
        """

        categoria = "Comissionado"

        e_efetivo = False
        e_comissionado = True

        tem_funcao = False
        tem_cargo_comissao = False

    elif tem_funcao:
        categoria = (
            "Efetivo com função gratificada"
        )

        e_efetivo = True
        e_comissionado = False

    elif tem_cargo_comissao:
        categoria = (
            "Efetivo com cargo em comissão"
        )

        e_efetivo = True
        e_comissionado = False

    elif tem_efetivo:
        categoria = "Efetivo"

        e_efetivo = True
        e_comissionado = False

    else:
        categoria = "Não identificado"

        e_efetivo = False
        e_comissionado = False

    return {
        "numero": int(numero),
        "nome": nome,
        "cargo": cargo,
        "categoria": categoria,
        "efetivo": e_efetivo,
        "comissionado": e_comissionado,
        "estagiario": e_estagiario,
        "funcao_gratificada": (
            tem_funcao
        ),
        "efetivo_cargo_comissao": (
            tem_cargo_comissao
        )
    }


def extrair_empregados(pdf_bytes):
    """
    Extrai todos os empregados do PDF.
    """

    empregados = []

    colunas = None

    with pdfplumber.open(
        io.BytesIO(pdf_bytes)
    ) as documento:

        for pagina in documento.pages:

            tabelas = (
                pagina.extract_tables()
                or []
            )

            for tabela in tabelas:

                for linha in tabela:

                    if not linha:
                        continue

                    # Verifica se esta linha
                    # é um cabeçalho
                    cabecalho = (
                        identificar_colunas(
                            linha
                        )
                    )

                    if (
                        "funcionario" in cabecalho
                        and "cargo" in cabecalho
                    ):
                        colunas = cabecalho
                        continue

                    if not colunas:
                        continue

                    empregado = (
                        classificar_linha(
                            linha,
                            colunas
                        )
                    )

                    if empregado:
                        empregados.append(
                            empregado
                        )

    # ==============================
    # REMOVER DUPLICIDADES
    # ==============================

    empregados_unicos = {}

    for empregado in empregados:

        nome_normalizado = normalizar(
            empregado["nome"]
        )

        if not nome_normalizado:
            continue

        """
        O nome é utilizado para evitar
        duplicidade.

        O número da primeira coluna NÃO
        é usado como identificador único,
        porque o documento pode possuir
        numeração repetida.
        """

        if (
            nome_normalizado
            not in empregados_unicos
        ):
            empregados_unicos[
                nome_normalizado
            ] = empregado

    resultado = list(
        empregados_unicos.values()
    )

    # ==============================
    # RENUMERAÇÃO INTERNA
    # ==============================

    for numero, empregado in enumerate(
        resultado,
        start=1
    ):
        empregado["numero"] = numero

    # ==============================
    # VALIDAÇÕES
    # ==============================

    if len(resultado) < 5:
        raise RuntimeError(
            "A estrutura da tabela mudou "
            "e os dados não puderam ser "
            "lidos com segurança."
        )

    nomes_vazios = [
        empregado
        for empregado in resultado
        if not empregado["nome"].strip()
    ]

    if nomes_vazios:
        raise RuntimeError(
            "Foram encontrados registros "
            "sem nome. A atualização foi "
            "interrompida."
        )

    return resultado
