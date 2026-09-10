import re
import unicodedata
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from config import LISTA_FALLBACK_ID, PORTAL_HOME, TEMPO_LIMITE


def normalizar(texto):
    texto = " ".join(str(texto or "").split()).lower()

    return "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caractere) != "Mn"
    )


def criar_conexao():
    conexao = requests.Session()

    conexao.headers.update({
        "User-Agent": (
            "MonitorTransparenciaCorenGO/1.0 "
            "(auditoria de dados publicos)"
        )
    })

    return conexao


def descobrir_lista_mais_nova(conexao):
    try:
        resposta = conexao.get(
            PORTAL_HOME,
            timeout=TEMPO_LIMITE
        )

        resposta.raise_for_status()

        pagina = BeautifulSoup(
            resposta.text,
            "html.parser"
        )

        for item_menu in pagina.select("li"):
            link_principal = item_menu.find(
                "a",
                recursive=False
            )

            if not link_principal:
                continue

            titulo = normalizar(
                link_principal.get_text(
                    " ",
                    strip=True
                )
            )

            if "relacao dos empregados com cargos" not in titulo:
                continue

            anos_encontrados = []

            for link_ano in item_menu.select(
                "a[href*='publico/Listas?id=']"
            ):
                ano = link_ano.get_text(strip=True)

                lista = re.search(
                    r"id=([0-9a-f-]{36})",
                    link_ano.get("href", ""),
                    re.IGNORECASE
                )

                if (
                    ano.isdigit()
                    and len(ano) == 4
                    and lista
                ):
                    anos_encontrados.append(
                        (int(ano), lista.group(1))
                    )

            if anos_encontrados:
                return max(anos_encontrados)

    except requests.RequestException:
        pass

    return datetime.now().year, LISTA_FALLBACK_ID


def localizar_pdf_mais_recente(conexao, lista_id):
    endereco = (
        f"{PORTAL_HOME}"
        "Publico/Listas/BuscarEntity"
    )

    resposta = conexao.post(
        endereco,
        data={"id": lista_id},
        timeout=TEMPO_LIMITE
    )

    resposta.raise_for_status()

    dados = resposta.json().get("data") or {}

    arquivos = [
        item
        for item in dados.get("Itens", [])
        if item.get("Anexo")
    ]

    if not arquivos:
        raise RuntimeError(
            "Nenhum PDF foi encontrado no portal."
        )

    def converter_data(item):
        try:
            return datetime.strptime(
                item.get("DataUpload", ""),
                "%d/%m/%Y"
            )
        except ValueError:
            return datetime.min

    mais_recente = max(
        arquivos,
        key=converter_data
    )

    anexo = mais_recente["Anexo"]

    anexo_id = (
        anexo.get("IdArquivoAnexo")
        or anexo.get("Id")
    )

    url_pdf = (
        f"{PORTAL_HOME}"
        "Publico/ArquivosAnexos/Download"
        f"?idArquivoAnexo={anexo_id}"
    )

    return {
        "titulo_lista": dados.get(
            "TituloPagina",
            "Relação de empregados"
        ),
        "nome": anexo.get("Nome"),
        "data_upload": mais_recente.get(
            "DataUpload"
        ),
        "url": url_pdf
    }


def baixar_pdf(conexao, url):
    resposta = conexao.get(
        url,
        timeout=TEMPO_LIMITE
    )

    resposta.raise_for_status()

    if not resposta.content.startswith(b"%PDF"):
        raise RuntimeError(
            "O arquivo encontrado não é um PDF válido."
        )

    return resposta.content
