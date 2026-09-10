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
        formatarDataHora(dados.atualizado_em)
    );

    definirTexto("total", total);
    definirTexto("efetivos", efetivos);
    definirTexto(
        "comissionados",
        comissionados
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
        percentual(efetivos, total) + " do total"
    );

    definirTexto(
        "percentual-comissionados",
        percentual(comissionados, total)
        + " do total"
    );

    definirTexto("grafico-total", total);

    definirTexto(
        "legenda-efetivos",
        efetivos
    );

    definirTexto(
        "legenda-comissionados",
        comissionados
    );

    const grafico = elemento("grafico-rosca");

    const parteEfetivos = total
        ? (efetivos / total) * 100
        : 0;

    grafico.style.background = `
        conic-gradient(
            var(--verde) 0% ${parteEfetivos}%,
            var(--laranja) ${parteEfetivos}% 100%
        )
    `;

    const linkFonte = elemento("link-fonte");

    if (fonte.url) {
        linkFonte.href = fonte.url;
    }
}


function classeDaCategoria(categoria) {
    if (categoria === "Comissionado") {
        return "etiqueta comissionado";
    }

    if (
        categoria.includes("função")
        || categoria.includes("comissão")
    ) {
        return "etiqueta funcao";
    }

    return "etiqueta";
}


function criarCelula(texto) {
    const celula = document.createElement("td");
    celula.textContent = texto || "";
    return celula;
}


function mostrarEmpregados(empregados) {
    const corpo = elemento("tabela-empregados");
    corpo.replaceChildren();

    if (!empregados.length) {
        const linha = document.createElement("tr");
        const celula = document.createElement("td");

        celula.colSpan = 4;
        celula.textContent = (
            "Nenhum empregado encontrado."
        );

        linha.appendChild(celula);
        corpo.appendChild(linha);

        definirTexto(
            "quantidade-exibida",
            "0 empregados exibidos"
        );

        return;
    }

    empregados.forEach((empregado) => {
        const linha = document.createElement("tr");

        linha.appendChild(
            criarCelula(empregado.numero)
        );

        linha.appendChild(
            criarCelula(empregado.nome)
        );

        linha.appendChild(
            criarCelula(empregado.cargo)
        );

        const categoria = document.createElement(
            "td"
        );

        const etiqueta = document.createElement(
            "span"
        );

        etiqueta.className = classeDaCategoria(
            empregado.categoria
        );

        etiqueta.textContent = empregado.categoria;

        categoria.appendChild(etiqueta);
        linha.appendChild(categoria);
        corpo.appendChild(linha);
    });

    definirTexto(
        "quantidade-exibida",
        `${empregados.length} empregados exibidos`
    );
}


function aplicarFiltros() {
    const pesquisa = normalizar(
        elemento("pesquisa").value
    );

    const categoria = elemento("filtro").value;

    const resultado = todosOsEmpregados.filter(
        (empregado) => {

            const textoDaLinha = normalizar(
                empregado.nome
                + " "
                + empregado.cargo
            );

            const atendePesquisa = (
                textoDaLinha.includes(pesquisa)
            );

            const atendeCategoria = (
                !categoria
                || empregado.categoria === categoria
            );

            return (
                atendePesquisa
                && atendeCategoria
            );
        }
    );

    mostrarEmpregados(resultado);
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
            (a, b) => a.numero - b.numero
        );

        preencherInformacoes(dados);
        mostrarEmpregados(todosOsEmpregados);

        elemento("pesquisa").addEventListener(
            "input",
            aplicarFiltros
        );

        elemento("filtro").addEventListener(
            "change",
            aplicarFiltros
        );

    } catch (erro) {
        console.error(erro);

        elemento("mensagem-erro").hidden = false;

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
