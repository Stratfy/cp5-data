"use strict";
const $ = (id) => document.getElementById(id);
const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const compact = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", notation: "compact", maximumFractionDigits: 1 });
const integer = new Intl.NumberFormat("pt-BR");
const formatMoney = (cents) => money.format(cents / 100);
const formatDate = (date) => date ? date.split("-").reverse().join("/") : "—";
const state = { filters: { mes: "", unidade: "" }, page: 1, pages: 1, controller: null, ready: false };

function node(tag, text, className) {
  const element = document.createElement(tag);
  if (text !== undefined) element.textContent = text;
  if (className) element.className = className;
  return element;
}
function query(extra = {}) {
  const parameters = new URLSearchParams();
  for (const [key, value] of Object.entries({ ...state.filters, ...extra })) {
    if (value !== "" && value !== null && value !== undefined) parameters.set(key, value);
  }
  return parameters.toString();
}
async function request(endpoint, extra = {}) {
  const response = await fetch(`${endpoint}?${query(extra)}`, { signal: state.controller.signal });
  const data = await response.json();
  if (!response.ok) throw new Error(data.erro || "Não foi possível completar a consulta.");
  return data;
}
function busy(value) {
  $("resultados").setAttribute("aria-busy", String(value));
  for (const id of ["aplicar", "limpar", "mes", "unidade"]) $(id).disabled = value || !state.ready;
  $("anterior").disabled = value || state.page <= 1;
  $("proxima").disabled = value || state.page >= state.pages;
}
function renderSummary(data) {
  $("total").textContent = formatMoney(data.total_centavos);
  $("registros").textContent = integer.format(data.registros);
  $("unidades").textContent = integer.format(data.unidades);
  $("ajustes").textContent = integer.format(data.ajustes);
  $("zeros").textContent = `${integer.format(data.zeros)} registro(s) com valor zero`;
  $("ajustes-valor").textContent = `${formatMoney(data.ajustes_centavos)} incorporados ao total`;
  $("alerta").hidden = data.registros !== 0;
  $("alerta").textContent = "Nenhum registro encontrado com estes filtros. Escolha outra combinação ou use Limpar.";
  const month = $("mes").selectedOptions[0]?.textContent || "Todos os meses";
  const unit = state.filters.unidade ? $("unidade").selectedOptions[0]?.textContent : "Todas as unidades";
  $("recorte").textContent = `2024 · ${month} · ${unit} · ${integer.format(data.registros)} registro(s)`;
  $("mensal-descricao").textContent = state.filters.mes
    ? "O filtro de mês também se aplica a este gráfico. Escolha Todos os meses para comparar o ano."
    : "Meses de 2024, conforme a data de referência de cada registro. Meses sem linhas são identificados na tabela.";
}
function emptyChart(element) {
  element.replaceChildren(node("p", "Não há registros para desenhar este gráfico.", "empty-chart"));
}
function renderRanking(rows) {
  const container = $("ranking");
  container.replaceChildren();
  if (!rows.length) return emptyChart(container);
  const hasNegative = rows.some((row) => row.total_centavos < 0);
  const max = Math.max(...rows.map((row) => Math.abs(row.total_centavos)), 1);
  rows.forEach((row, index) => {
    const wrapper = node("div", undefined, "ranking-row");
    wrapper.append(node("span", String(index + 1).padStart(2, "0"), "rank-number"));
    const content = node("div", undefined, "rank-content");
    const top = node("div", undefined, "rank-top");
    const name = node("span", row.nome || "Unidade não informada", "rank-name");
    name.title = `${row.codigo || "Sem código"} · ${row.nome || "Unidade não informada"}`;
    const value = node("span", formatMoney(row.total_centavos), "rank-value");
    if (row.total_centavos < 0) value.classList.add("negative-value");
    top.append(name, value);
    const track = node("div", undefined, "rank-track");
    track.setAttribute("aria-hidden", "true");
    const fill = node("span", undefined, `rank-fill${row.total_centavos < 0 ? " negative" : ""}`);
    const width = Math.abs(row.total_centavos) / max * (hasNegative ? 50 : 100);
    fill.style.width = `${width}%`;
    fill.style.left = `${hasNegative ? row.total_centavos < 0 ? 50 - width : 50 : 0}%`;
    track.append(fill);
    if (hasNegative) { const baseline = node("span", undefined, "rank-baseline"); baseline.style.left = "50%"; track.append(baseline); }
    content.append(top, track);
    wrapper.append(content);
    container.append(wrapper);
  });
}
function svgNode(tag, attributes = {}, text) {
  const element = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
  if (text !== undefined) element.textContent = text;
  return element;
}
function renderMonthly(rows) {
  const container = $("mensal");
  const table = $("mensal-tabela");
  table.replaceChildren();
  rows.forEach((row) => {
    const tr = node("tr");
    tr.append(node("td", `${row.nome}${row.registros === 0 ? " · sem registros" : ""}`),
      node("td", formatMoney(row.total_centavos), "number"), node("td", integer.format(row.registros), "number"));
    table.append(tr);
  });
  container.replaceChildren();
  if (!rows.some((row) => row.registros > 0)) return emptyChart(container);
  const width = 580, height = 300, left = 78, right = 18, top = 23, bottom = 255;
  const values = rows.map((row) => row.total_centavos);
  let high = Math.max(0, ...values), low = Math.min(0, ...values);
  if (high === 0 && low === 0) high = 100;
  const range = high - low;
  if (high > 0) high += range * 0.08;
  if (low < 0) low -= range * 0.08;
  const scale = (value) => bottom - ((value - low) / (high - low)) * (bottom - top);
  const baseline = scale(0);
  const svg = svgNode("svg", { viewBox: `0 0 ${width} ${height}`, role: "img", "aria-labelledby": "mensal-titulo-svg mensal-desc-svg" });
  svg.append(svgNode("title", { id: "mensal-titulo-svg" }, "Total pago líquido por mês"));
  svg.append(svgNode("desc", { id: "mensal-desc-svg" }, rows.map((row) => `${row.nome}: ${formatMoney(row.total_centavos)}, ${row.registros} registros`).join(". ")));
  for (let index = 0; index <= 4; index++) {
    const value = low + (high - low) * index / 4;
    const y = scale(value);
    svg.append(svgNode("line", { x1: left, x2: width - right, y1: y, y2: y, stroke: "#e4ede8", "stroke-dasharray": "3 4" }));
    svg.append(svgNode("text", { x: left - 10, y: y + 4, "text-anchor": "end", fill: "#748b81", "font-size": 10 }, compact.format(value / 100)));
  }
  svg.append(svgNode("line", { x1: left, x2: width - right, y1: baseline, y2: baseline, stroke: "#9db9ac" }));
  const step = (width - left - right) / rows.length;
  rows.forEach((row, index) => {
    const x = left + index * step + step * 0.21;
    const y = scale(row.total_centavos);
    const barHeight = Math.abs(y - baseline);
    const bar = svgNode("rect", { x, y: row.total_centavos >= 0 ? y : baseline,
      width: step * 0.58, height: Math.max(barHeight, 1), rx: Math.min(3, barHeight / 2),
      fill: row.total_centavos < 0 ? "#b34740" : row.registros === 0 ? "#d5e1da" : "#087d73" });
    bar.append(svgNode("title", {}, `${row.nome}: ${formatMoney(row.total_centavos)} · ${integer.format(row.registros)} registro(s)`));
    svg.append(bar);
    svg.append(svgNode("text", { x: left + index * step + step / 2, y: bottom + 21, "text-anchor": "middle", fill: "#597669", "font-size": 11 }, row.nome.slice(0, 3)));
  });
  container.append(svg);
}
function renderRecords(data) {
  const table = $("registros-tabela");
  table.replaceChildren();
  state.page = data.pagina;
  state.pages = data.paginas;
  if (!data.linhas.length) { const row = node("tr"); const cell = node("td", "Nenhum registro nesta página."); cell.colSpan = 5; row.append(cell); table.append(row); }
  data.linhas.forEach((record) => {
    const row = node("tr");
    const unit = node("td", record.unidade_gestora || "Unidade não informada");
    unit.append(node("span", `Código ${record.codigo_unidade_gestora || "não informado"}`, "cell-secondary"));
    const value = node("td", formatMoney(record.valor_centavos), `number${record.valor_centavos < 0 ? " negative-value" : ""}`);
    const documentCell = node("td", record.tipo_documento || "—");
    documentCell.append(node("span", record.numero_documento || "Número não informado", "cell-secondary"));
    const origin = node("td");
    origin.append(node("span", record.arquivo_origem, "file-name"), node("span", `Linha ${record.linha_origem} · ID origem ${record.id_origem || "não informado"}`, "cell-secondary"));
    row.append(node("td", formatDate(record.data_pagamento)), unit, value, documentCell, origin);
    table.append(row);
  });
  const start = data.linhas.length ? (data.pagina - 1) * data.tamanho + 1 : 0;
  const end = data.linhas.length ? start + data.linhas.length - 1 : 0;
  $("pagina-info").textContent = `${integer.format(start)}–${integer.format(end)} de ${integer.format(data.total)} registros · Mais recentes primeiro`;
  $("pagina-atual").textContent = `Página ${data.pagina} de ${integer.format(data.paginas)}`;
}
function updateDownloads() {
  for (const kind of ["ranking", "mensal", "detalhes"]) $("exportar-" + kind).href = `/api/exportar?${query({ tipo: kind })}`;
}
async function load(page = 1, full = true) {
  state.controller?.abort();
  const current = new AbortController();
  state.controller = current;
  busy(true);
  $("erro").hidden = true;
  try {
    if (full) {
      const [summary, ranking, monthly, records] = await Promise.all([
        request("/api/resumo"), request("/api/ranking"), request("/api/mensal"), request("/api/registros", { pagina: page })]);
      renderSummary(summary); renderRanking(ranking.linhas); renderMonthly(monthly.linhas); renderRecords(records); updateDownloads();
    } else renderRecords(await request("/api/registros", { pagina: page }));
    $("resultados").hidden = false;
  } catch (error) {
    if (error.name !== "AbortError") {
      $("erro-texto").textContent = error.message || "Não foi possível acessar o servidor local. Confira se a janela da aplicação continua aberta.";
      $("erro").hidden = false;
      $("alerta").hidden = true;
      $("resultados").hidden = true;
      $("recorte").textContent = "Consulta não concluída. Tente novamente.";
    }
  } finally { if (state.controller === current) busy(false); }
}
async function initialize() {
  state.controller?.abort();
  state.controller = new AbortController();
  busy(true);
  try {
    const options = await request("/api/opcoes");
    $("mes").replaceChildren(new Option("Todos os meses", ""));
    $("unidade").replaceChildren(new Option("Todas as unidades", ""));
    options.meses.forEach((month) => $("mes").add(new Option(month.nome, String(month.valor))));
    options.unidades.forEach((unit) => $("unidade").add(new Option(`${unit.codigo || "Sem código"} · ${unit.nome}`, unit.chave)));
    state.ready = true;
    await load();
  } catch (error) {
    $("erro-texto").textContent = error.message || "Não foi possível carregar a base. Confira se a aplicação continua aberta.";
    $("erro").hidden = false; $("resultados").hidden = true;
    $("recorte").textContent = "Base indisponível.";
    busy(false);
  }
}
$("filtros").addEventListener("submit", (event) => { event.preventDefault(); state.filters = { mes: $("mes").value, unidade: $("unidade").value }; load(); });
$("limpar").addEventListener("click", () => { $("mes").value = ""; $("unidade").value = ""; state.filters = { mes: "", unidade: "" }; load(); });
$("anterior").addEventListener("click", () => load(state.page - 1, false));
$("proxima").addEventListener("click", () => load(state.page + 1, false));
$("tentar").addEventListener("click", () => state.ready ? load() : initialize());
initialize();
