let todosOsEmpregados = [];


function elemento(id) {
    return document.getElementById(id);
}


function percentual(valor, total) {
    if (!total) {
        return "0%";
    }

    return (
        (valor / total) * 100
    ).toFixed(1).replace(".", ",") + "%";
}


function normalizar(texto) {
    return String(texto || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase();
}


function formatarDataHora(dataISO) {
    const data = new Date(dataISO);

    if (Number.isNaN(data.getTime())) {
        return "Não informada";
    }

    return new Intl.DateTimeFormat(
        "pt-BR",
        {
            dateStyle: "short",
            timeStyle: "short"
        }
    ).format(data);
}


function definirTexto(id, texto) {
    const campo = elemento(id);

    if (campo) {
        campo.textContent = texto;
    }
}


function preencherInformacoes(dados) {
    const fonte = dados.fonte || {};
    const totais = dados.totais || {};

    const total = totais.total || 0;

    const efetivos = (
        totais.concursados_efetivos || 0
    );

    const comissionados = (
        totais.comissionados || 0
    );

    const estagiarios = (
        totais.estagiarios || 0
    );


    definirTexto(
        "relatorio",
        fonte.nome || "Não informado"
    );


    definirTexto(
        "data-publicacao",
        fonte.data_upload || "Não informada"
    );


    definirTexto(
        "ultima-verificacao",
        formatarDataHora(
            dados.atualizado_em
        )
    );


    definirTexto(
        "total",
        total
    );


    definirTexto(
        "efetivos",
        efetivos
    );


    definirTexto(
        "comissionados",
        comissionados
    );


    definirTexto(
        "estagiarios",
        estagiarios
    );


    definirTexto(
        "funcoes",
        totais.funcao_gratificada || 0
    );


    definirTexto(
        "efetivos-comissao",
        totais.efetivo_cargo_comissao || 0
    );


    definirTexto(
        "percentual-efetivos",
        percentual(
            efetivos,
            total
        ) + " do total"
    );


    definirTexto(
        "percentual-comissionados",
        percentual(
            comissionados,
            total
        ) + " do total"
    );


    definirTexto(
        "percentual-estagiarios",
        percentual(
            estagiarios,
            total
        ) + " do total"
    );


    definirTexto(
        "grafico-total",
        total
    );


    definirTexto(
        "legenda-efetivos",
        efetivos
    );


    definirTexto(
        "legenda-comissionados",
        comissionados
    );


    definirTexto(
        "legenda-estagiarios",
        estagiarios
    );


    const grafico = elemento(
        "grafico-rosca"
    );


    if (grafico) {

        const parteEfetivos = total
            ? (efetivos / total) * 100
            : 0;

        const parteComissionados = total
            ? (comissionados / total) * 100
            : 0;

        const fimEfetivos = (
            parteEfetivos
        );

        const fimComissionados = (
            parteEfetivos
            + parteComissionados
        );


        grafico.style.background = `
            conic-gradient(
                var(--verde)
                0%
                ${fimEfetivos}%,

                var(--laranja)
                ${fimEfetivos}%
                ${fimComissionados}%,

                var(--azul)
                ${fimComissionados}%
                100%
            )
        `;
    }


    const linkFonte = elemento(
        "link-fonte"
    );


    if (
        linkFonte
        && fonte.url
    ) {
        linkFonte.href = fonte.url;
    }
}


function classeDaCategoria(categoria) {

    if (
        categoria === "Comissionado"
    ) {
        return (
            "etiqueta comissionado"
        );
    }


    if (
        categoria === "Estagiário"
    ) {
        return (
            "etiqueta estagiario"
        );
    }


    if (
        categoria.includes("função")
        || categoria.includes("comissão")
    ) {
        return (
            "etiqueta funcao"
        );
    }


    return "etiqueta";
}


function criarCelula(texto) {

    const celula = document.createElement(
        "td"
    );

    celula.textContent = texto || "";

    return celula;
}


function mostrarEmpregados(empregados) {

    const corpo = elemento(
        "tabela-empregados"
    );


    if (!corpo) {
        return;
    }


    corpo.replaceChildren();


    if (!empregados.length) {

        const linha = document.createElement(
            "tr"
        );

        const celula = document.createElement(
            "td"
        );


        celula.colSpan = 4;

        celula.textContent = (
            "Nenhum empregado encontrado."
        );


        linha.appendChild(
            celula
        );

        corpo.appendChild(
            linha
        );


        definirTexto(
            "quantidade-exibida",
            "0 empregados exibidos"
        );


        return;
    }


    empregados.forEach(
        (empregado) => {

            const linha = (
                document.createElement(
                    "tr"
                )
            );


            linha.appendChild(
                criarCelula(
                    empregado.numero
                )
            );


            linha.appendChild(
                criarCelula(
                    empregado.nome
                )
            );


            linha.appendChild(
                criarCelula(
                    empregado.cargo
                )
            );


            const categoria = (
                document.createElement(
                    "td"
                )
            );


            const etiqueta = (
                document.createElement(
                    "span"
                )
            );


            etiqueta.className = (
                classeDaCategoria(
                    empregado.categoria
                )
            );


            etiqueta.textContent = (
                empregado.categoria
            );


            categoria.appendChild(
                etiqueta
            );


            linha.appendChild(
                categoria
            );


            corpo.appendChild(
                linha
            );
        }
    );


    definirTexto(
        "quantidade-exibida",
        `${empregados.length} empregados exibidos`
    );
}


function aplicarFiltros() {

    const campoPesquisa = elemento(
        "pesquisa"
    );

    const campoFiltro = elemento(
        "filtro"
    );


    const pesquisa = normalizar(
        campoPesquisa
            ? campoPesquisa.value
            : ""
    );


    const categoria = (
        campoFiltro
            ? campoFiltro.value
            : ""
    );


    const resultado = (
        todosOsEmpregados.filter(
            (empregado) => {

                const textoDaLinha = normalizar(
                    empregado.nome
                    + " "
                    + empregado.cargo
                );


                const atendePesquisa = (
                    textoDaLinha.includes(
                        pesquisa
                    )
                );


                const atendeCategoria = (
                    !categoria
                    || empregado.categoria
                    === categoria
                );


                return (
                    atendePesquisa
                    && atendeCategoria
                );
            }
        )
    );


    mostrarEmpregados(
        resultado
    );
}


async function carregarDados() {

    try {

        const resposta = await fetch(
            "dados.json",
            {
                cache: "no-store"
            }
        );


        if (!resposta.ok) {
            throw new Error(
                "Falha ao carregar dados.json"
            );
        }


        const dados = await resposta.json();


        todosOsEmpregados = (
            dados.empregados || []
        ).sort(
            (a, b) => (
                a.numero - b.numero
            )
        );


        preencherInformacoes(
            dados
        );


        mostrarEmpregados(
            todosOsEmpregados
        );


        const pesquisa = elemento(
            "pesquisa"
        );


        const filtro = elemento(
            "filtro"
        );


        if (pesquisa) {
            pesquisa.addEventListener(
                "input",
                aplicarFiltros
            );
        }


        if (filtro) {
            filtro.addEventListener(
                "change",
                aplicarFiltros
            );
        }


    } catch (erro) {

        console.error(
            erro
        );


        const mensagemErro = elemento(
            "mensagem-erro"
        );


        if (mensagemErro) {
            mensagemErro.hidden = false;
        }


        definirTexto(
            "relatorio",
            "Dados indisponíveis"
        );


        definirTexto(
            "data-publicacao",
            "Dados indisponíveis"
        );


        definirTexto(
            "ultima-verificacao",
            "Dados indisponíveis"
        );
    }
}


carregarDados();
