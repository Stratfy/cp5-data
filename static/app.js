"use strict";
const $ = (id) => document.getElementById(id);
const money = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const compact = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", notation: "compact", maximumFractionDigits: 1 });
const integer = new Intl.NumberFormat("pt-BR");
const percent = new Intl.NumberFormat("pt-BR", { style: "percent", minimumFractionDigits: 2, maximumFractionDigits: 2 });
const hasMoney = (cents) => typeof cents === "number" && Number.isFinite(cents);
const formatMoney = (cents) => hasMoney(cents) ? money.format(cents / 100) : "Não informado";
const formatDate = (date) => date ? date.split("-").reverse().join("/") : "—";
const state = { filters: { mes: "", unidade: "" }, page: 1, pages: 1, controller: null, ready: false, failed: false, busy: false };
let dismissActiveTooltip = null;

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
  state.busy = value;
  document.dispatchEvent(new CustomEvent("pagamentos:loading", { detail: { active: value } }));
  $("resultados").setAttribute("aria-busy", String(value));
  if (value) consultationStatus(state.ready ? "Consultando o recorte…" : "Preparando os dados de 2024…", "loading");
  for (const id of ["aplicar", "limpar", "mes", "unidade", "exemplo-panorama"]) $(id).disabled = value || !state.ready;
  for (const id of ["exemplo-saude", "exemplo-penal"]) $(id).disabled = value || !state.ready || !$(id).dataset.unit;
  document.querySelectorAll(".ranking-row, .context-chip.removable").forEach((button) => { button.disabled = value || !state.ready || button.dataset.unavailable === "true"; });
  $("anterior").disabled = value || state.page <= 1;
  $("proxima").disabled = value || state.page >= state.pages;
}
function consultationStatus(text, status) {
  const element = $("consulta-status");
  if (!element) return;
  element.textContent = text;
  element.dataset.state = status;
}
function filtersPending() {
  return $("mes").value !== state.filters.mes || $("unidade").value !== state.filters.unidade;
}
function updateConsultationStatus() {
  if (state.failed) {
    consultationStatus("Consulta não concluída. Revise os filtros ou tente novamente.", "error");
    return;
  }
  if (filtersPending()) consultationStatus("Filtros alterados. Clique em Consultar para atualizar.", "pending");
  else consultationStatus("Consulta atualizada", "ready");
}
function insight(id, label, value, detail) {
  const element = $(id);
  if (!element) return;
  element.replaceChildren(node("span", label, "insight-label"), node("strong", value, "insight-value"), node("span", detail, "insight-detail"));
}
function renderDataQuality(data) {
  const notice = $("qualidade-dados");
  if (!notice) return;
  const withoutValue = data.registros_sem_valor || 0;
  const withoutMonth = data.registros_sem_mes || 0;
  const withoutDate = data.registros_sem_data || 0;
  notice.hidden = !withoutValue && !withoutMonth && !withoutDate;
  if (notice.hidden) { notice.textContent = ""; return; }
  const messages = ["Recorte com dados incompletos."];
  if (withoutValue) {
    messages.push(`${integer.format(withoutValue)} registro(s) sem ValorPago válido.`);
    messages.push(data.registros_com_valor > 0
      ? "Os totais somam apenas os valores disponíveis; ausências não foram substituídas por zero."
      : "Nenhum registro possui ValorPago válido; o total permanece indisponível.");
  }
  if (withoutMonth) {
    messages.push(`${integer.format(withoutMonth)} registro(s) sem mês válido de 2024 não entram na série mensal${withoutDate ? `, incluindo ${integer.format(withoutDate)} sem data válida` : ""}.`);
    if (data.diferenca_serie_centavos) {
      messages.push(`A soma mensal dos valores disponíveis é ${formatMoney(data.total_com_mes_centavos)}. A diferença entre o total disponível e a série é ${formatMoney(data.diferenca_serie_centavos)}, referente aos registros sem mês válido.`);
    }
  } else if (withoutDate) messages.push(`${integer.format(withoutDate)} registro(s) sem Data do registro. Confira a origem antes de interpretar o período.`);
  notice.textContent = messages.join(" ");
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
  const month = [...$("mes").options].find((option) => option.value === state.filters.mes)?.textContent || "Todos os meses";
  const unit = state.filters.unidade ? [...$("unidade").options].find((option) => option.value === state.filters.unidade)?.textContent || "Unidade selecionada" : "Todas as unidades";
  $("recorte").textContent = `2024 · ${month} · ${unit} · ${integer.format(data.registros)} registro(s)`;
  const applied = $("filtros-aplicados");
  if (applied) applied.replaceChildren(node("span", "2024", "context-chip"), filterChip(month, "mes"), filterChip(unit, "unidade", "unit-chip"));
  $("mensal-descricao").textContent = state.filters.mes
    ? "O filtro de mês também se aplica a este gráfico. Escolha Todos os meses para comparar o ano."
    : "Meses de 2024, conforme a data de referência de cada registro. Meses sem linhas são identificados na tabela.";
  renderDataQuality(data);
}
function filterChip(label, key, className = "") {
  const selected = Boolean(state.filters[key]);
  const chip = node(selected ? "button" : "span", label, `context-chip ${className}${selected ? " removable" : ""}`);
  if (selected) {
    chip.type = "button";
    chip.setAttribute("aria-label", `Remover filtro: ${label}`);
    const close = node("span", "×", "chip-remove");
    close.setAttribute("aria-hidden", "true");
    chip.append(close);
    chip.addEventListener("click", () => applyFilters({ ...state.filters, [key]: "" }, true));
  }
  return chip;
}
async function applyFilters(filters, focusSummary = false) {
  if (state.busy || !state.ready) return;
  state.filters = { ...filters };
  $("mes").value = filters.mes;
  $("unidade").value = filters.unidade;
  const loaded = await load();
  if (loaded && focusSummary) $("panorama").focus({ preventScroll: true });
}
function unitKey(code, name) {
  return [...$("unidade").options].find((option) => {
    if (!option.value) return false;
    try {
      const pair = JSON.parse(option.value);
      return String(pair[0] ?? "") === String(code ?? "") && String(pair[1] ?? "") === String(name ?? "");
    } catch { return false; }
  })?.value;
}
function emptyChart(element, message = "Não há registros para desenhar este gráfico.") {
  element.replaceChildren(node("p", message, "empty-chart"));
}
function describeRecorte(summary, ranking, monthly, filters) {
  if (!summary.registros) return ["Nenhum registro neste recorte.", "Experimente outra combinação de unidade e mês."];
  if (!hasMoney(summary.total_centavos)) return ["Há registros, mas nenhum ValorPago disponível.", "Os valores ausentes não foram tratados como zero."];
  if (summary.registros_sem_valor || summary.registros_sem_mes) return ["Este recorte tem dados incompletos.", "Confira o aviso de cobertura antes de comparar os valores disponíveis."];
  if (summary.total_centavos === 0) return ["O saldo líquido deste recorte é zero.", "Há registros: valores zero ou compensações podem formar esse resultado."];
  if (summary.total_centavos < 0) return ["O recorte apresenta saldo líquido negativo.", "Os valores negativos foram preservados na soma. Consulte os registros de origem."];
  const readings = [];
  if (!filters.unidade && ranking.length >= 3) {
    const firstThree = ranking.slice(0, 3);
    const share = firstThree.reduce((total, row) => total + row.total_centavos, 0) / summary.total_centavos;
    if (firstThree.every((row) => hasMoney(row.total_centavos) && row.total_centavos >= 0) && share <= 1) {
      readings.push(`As 3 primeiras unidades concentram ${percent.format(share)} do total líquido.`);
    }
  }
  const measured = monthly.filter((row) => row.registros > 0 && hasMoney(row.total_centavos));
  if (!filters.mes && measured.length > 1) {
    const peak = measured.reduce((best, row) => row.total_centavos > best.total_centavos ? row : best);
    const share = peak.total_centavos / summary.total_centavos;
    if (share > 0 && share <= 1) readings.push(`${peak.nome} reúne ${percent.format(share)} do total líquido do recorte.`);
  }
  return readings.length ? readings : ["Consulta pronta para conferência.", "Os registros e as exportações abaixo correspondem ao recorte aplicado."];
}
function renderReading(summary, ranking, monthly) {
  $("leitura-recorte").replaceChildren(...describeRecorte(summary, ranking, monthly, state.filters).map((text, index) => node(index ? "span" : "strong", text)));
}
function updatePresentation() {
  const active = document.body.classList.contains("presentation-mode");
  $("modo-apresentacao").setAttribute("aria-pressed", String(active));
  $("modo-apresentacao").textContent = active ? "Sair da apresentação" : "Modo apresentação";
  const count = $("ranking").querySelectorAll(".ranking-row").length;
  const limit = active ? 5 : 10;
  const label = $("ranking").dataset.hasValues === "false" ? "unidades exibidas" : "maiores unidades";
  $("ranking-limite").textContent = count ? `${Math.min(count, limit)} ${count === 1 ? "unidade" : label}` : "Sem registros";
}
function renderRanking(rows) {
  const container = $("ranking");
  container.dataset.hasValues = String(rows.some((row) => hasMoney(row.total_centavos)));
  container.replaceChildren();
  if (!rows.length) {
    insight("ranking-destaque", "Recorte consultado", "Sem registros", "Escolha outra unidade ou mês.");
    return emptyChart(container);
  }
  const measured = rows.filter((row) => hasMoney(row.total_centavos));
  const leader = measured[0];
  if (leader) insight("ranking-destaque", state.filters.unidade ? (leader.registros_sem_valor ? "Total disponível da unidade" : "Total da unidade selecionada") : "Maior total no recorte", formatMoney(leader.total_centavos), `${leader.nome || "Unidade não informada"}${leader.registros_sem_valor ? ` · ${integer.format(leader.registros_sem_valor)} registro(s) sem ValorPago` : ""}`);
  else insight("ranking-destaque", "Registros sem valores disponíveis", "Não informado", "As unidades têm registros, mas nenhum ValorPago válido.");
  const hasNegative = measured.some((row) => row.total_centavos < 0);
  const max = Math.max(...measured.map((row) => Math.abs(row.total_centavos)), 1);
  rows.forEach((row, index) => {
    const wrapper = node("button", undefined, "ranking-row");
    wrapper.type = "button";
    const key = unitKey(row.codigo, row.nome);
    wrapper.dataset.unavailable = String(key === undefined);
    wrapper.disabled = key === undefined;
    wrapper.setAttribute("aria-label", `${row.nome || "Unidade não informada"}: ${formatMoney(row.total_centavos)}. Explorar esta unidade.`);
    wrapper.title = "Explorar esta unidade no mês consultado";
    wrapper.addEventListener("click", () => {
      if (key !== undefined) applyFilters({ mes: state.filters.mes, unidade: key }, true);
    });
    wrapper.append(node("span", String(index + 1).padStart(2, "0"), "rank-number"));
    const content = node("span", undefined, "rank-content");
    const top = node("span", undefined, "rank-top");
    const name = node("span", row.nome || "Unidade não informada", "rank-name");
    name.title = `${row.codigo || "Sem código"} · ${row.nome || "Unidade não informada"}${row.registros_sem_valor ? ` · ${integer.format(row.registros_sem_valor)} registro(s) sem ValorPago` : ""}`;
    const value = node("span", formatMoney(row.total_centavos), "rank-value");
    if (row.total_centavos < 0) value.classList.add("negative-value");
    top.append(name, value);
    const track = node("span", undefined, "rank-track");
    track.setAttribute("aria-hidden", "true");
    const fill = node("span", undefined, `rank-fill${row.total_centavos < 0 ? " negative" : ""}`);
    const width = hasMoney(row.total_centavos) ? Math.abs(row.total_centavos) / max * (hasNegative ? 50 : 100) : 0;
    fill.style.width = `${width}%`;
    fill.style.left = `${hasNegative ? row.total_centavos < 0 ? 50 - width : 50 : 0}%`;
    fill.style.setProperty("--bar-origin", row.total_centavos < 0 ? "right" : "left");
    fill.style.setProperty("--bar-delay", `${index * 30}ms`);
    track.append(fill);
    if (!hasMoney(row.total_centavos)) track.hidden = true;
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
function hideTooltip() {
  const tooltip = $("chart-tooltip");
  if (tooltip) tooltip.hidden = true;
  dismissActiveTooltip = null;
}
function monthlyTooltip(group, row) {
  let pointerInside = false;
  let dismissed = false;
  function show(event) {
    if (state.busy || dismissed) return;
    let tooltip = $("chart-tooltip");
    if (!tooltip) {
      tooltip = node("div", undefined, "chart-tooltip");
      tooltip.id = "chart-tooltip";
      tooltip.setAttribute("aria-hidden", "true");
      document.body.append(tooltip);
    }
    const detail = row.registros === 0 ? "Sem registros neste mês" : `${integer.format(row.registros)} registro(s) no mês`;
    tooltip.replaceChildren(node("span", `${row.nome} · 2024`, "tooltip-month"), node("strong", formatMoney(row.total_centavos), "tooltip-value"), node("span", detail, "tooltip-detail"));
    if (row.registros_sem_valor) tooltip.append(node("span", `${integer.format(row.registros_sem_valor)} sem ValorPago válido`, "tooltip-hint"));
    tooltip.hidden = false;
    dismissActiveTooltip = () => { dismissed = true; hideTooltip(); };
    const bounds = group.getBoundingClientRect();
    const x = event?.clientX ?? (bounds.left + bounds.width / 2);
    const y = event?.clientY ?? bounds.top;
    const box = tooltip.getBoundingClientRect();
    tooltip.style.left = `${Math.max(12, Math.min(x - box.width / 2, window.innerWidth - box.width - 12))}px`;
    tooltip.style.top = `${Math.max(12, Math.min(y < box.height + 24 ? y + 20 : y - box.height - 16, window.innerHeight - box.height - 12))}px`;
  }
  group.addEventListener("pointerenter", (event) => { pointerInside = true; dismissed = false; show(event); });
  group.addEventListener("pointermove", show);
  group.addEventListener("pointerleave", () => { pointerInside = false; if (document.activeElement !== group) hideTooltip(); });
  group.addEventListener("focus", () => { dismissed = false; show(); });
  group.addEventListener("blur", () => { if (!pointerInside) hideTooltip(); });
  group.addEventListener("keydown", (event) => { if (event.key === "Escape") { dismissed = true; hideTooltip(); } });
}
function renderMonthly(rows) {
  hideTooltip();
  const container = $("mensal");
  const table = $("mensal-tabela");
  const peakLegend = document.querySelector(".chart-legend .peak")?.parentElement;
  if (peakLegend) peakLegend.hidden = Boolean(state.filters.mes) || !rows.some((row) => row.registros > 0 && hasMoney(row.total_centavos));
  const unavailableLegend = document.querySelector(".chart-legend .unavailable")?.parentElement;
  if (unavailableLegend) unavailableLegend.hidden = !rows.some((row) => row.registros > 0 && !hasMoney(row.total_centavos));
  for (const [selector, visible] of [[".negative", rows.some((row) => hasMoney(row.total_centavos) && row.total_centavos < 0)], [".missing", rows.some((row) => row.registros === 0)]]) {
    const legend = document.querySelector(`.chart-legend ${selector}`)?.parentElement;
    if (legend) legend.hidden = !visible;
  }
  container.classList.toggle("is-single-month", Boolean(state.filters.mes));
  if ($("mensal-deslize")) $("mensal-deslize").hidden = Boolean(state.filters.mes) || !rows.some((row) => row.registros > 0 && hasMoney(row.total_centavos));
  table.replaceChildren();
  rows.forEach((row) => {
    const tr = node("tr");
    const value = node("td", formatMoney(row.total_centavos), "number");
    if (row.registros_sem_valor) value.append(node("span", `${integer.format(row.registros_sem_valor)} sem ValorPago válido`, "cell-secondary"));
    tr.append(node("td", `${row.nome}${row.registros === 0 ? " · sem registros" : ""}`), value,
      node("td", integer.format(row.registros), "number"));
    table.append(tr);
  });
  container.replaceChildren();
  const observed = rows.filter((row) => row.registros > 0);
  if (!observed.length) {
    insight("mensal-destaque", "Recorte consultado", "Sem registros", "Nenhum mês tem linhas neste recorte.");
    return emptyChart(container);
  }
  const measured = observed.filter((row) => hasMoney(row.total_centavos));
  if (!measured.length) {
    insight("mensal-destaque", "Valores indisponíveis no calendário", "Não informado", "Há registros, mas nenhum mês tem ValorPago válido.");
    return emptyChart(container, "Há registros neste recorte, mas não há valores disponíveis para desenhar o gráfico mensal.");
  }
  const peak = measured.reduce((highest, row) => row.total_centavos > highest.total_centavos ? row : highest);
  insight("mensal-destaque", state.filters.mes ? `Total de ${peak.nome.toLowerCase()}` : `Maior total mensal · ${peak.nome}`, formatMoney(peak.total_centavos), `${integer.format(peak.registros)} registros no mês · soma líquida${peak.registros_sem_valor ? ` · ${integer.format(peak.registros_sem_valor)} sem ValorPago` : ""}`);
  const width = 620, height = 320, left = 120, right = 20, top = 35, bottom = 272;
  const values = rows.filter((row) => hasMoney(row.total_centavos)).map((row) => row.total_centavos);
  let high = Math.max(0, ...values), low = Math.min(0, ...values);
  if (high === 0 && low === 0) high = 100;
  const rawStep = (high - low) / 4;
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const tickStep = [1, 2, 2.5, 5, 10].find((step) => step * magnitude >= rawStep) * magnitude;
  high = Math.ceil(high / tickStep) * tickStep;
  low = Math.floor(low / tickStep) * tickStep;
  const scale = (value) => bottom - ((value - low) / (high - low)) * (bottom - top);
  const baseline = scale(0);
  const svg = svgNode("svg", { viewBox: `0 0 ${width} ${height}`, role: "group", class: "monthly-svg", "aria-labelledby": "mensal-titulo-svg mensal-desc-svg" });
  svg.append(svgNode("title", { id: "mensal-titulo-svg" }, "Total pago líquido por mês"));
  svg.append(svgNode("desc", { id: "mensal-desc-svg" }, rows.map((row) => `${row.nome}: ${formatMoney(row.total_centavos)}, ${row.registros} registros`).join(". ")));
  const tickCount = Math.round((high - low) / tickStep);
  for (let index = 0; index <= tickCount; index++) {
    const value = low + tickStep * index;
    const y = scale(value);
    svg.append(svgNode("line", { x1: left, x2: width - right, y1: y, y2: y, stroke: "var(--line)", "stroke-dasharray": "3 4" }));
    svg.append(svgNode("text", { x: left - 10, y: y + 5, "text-anchor": "end", fill: "var(--muted)", "font-size": 16 }, compact.format(value / 100)));
  }
  svg.append(svgNode("line", { x1: left, x2: width - right, y1: baseline, y2: baseline, stroke: "var(--muted)" }));
  const step = (width - left - right) / rows.length;
  rows.forEach((row, index) => {
    const x = left + index * step + step * 0.21;
    const isPeak = !state.filters.mes && row === peak;
    const label = `${row.nome}: ${formatMoney(row.total_centavos)} · ${integer.format(row.registros)} registro(s)${row.registros === 0 ? " · sem registros" : ""}${row.registros_sem_valor ? ` · ${integer.format(row.registros_sem_valor)} sem ValorPago válido` : ""}`;
    const group = svgNode("g", { class: "bar-group", tabindex: "0", role: "img", "aria-label": label });
    group.append(svgNode("rect", { x: left + index * step, y: top, width: step, height: bottom - top, class: "bar-hit", fill: "transparent", "pointer-events": "all" }));
    monthlyTooltip(group, row);
    if (!hasMoney(row.total_centavos)) {
      group.append(svgNode("line", { x1: x, x2: x + step * 0.58, y1: baseline, y2: baseline, class: "unavailable-marker", stroke: "var(--muted)", "stroke-width": 2, "stroke-dasharray": "3 2" }));
      group.append(svgNode("text", { x: left + index * step + step / 2, y: Math.max(top, baseline - 8), "text-anchor": "middle", class: "unavailable-label" }, "—"));
      svg.append(group);
      svg.append(svgNode("text", { x: left + index * step + step / 2, y: bottom + 25, "text-anchor": "middle", fill: "var(--muted)", "font-size": 16 }, row.nome.slice(0, 3)));
      return;
    }
    const y = scale(row.total_centavos);
    const barHeight = Math.abs(y - baseline);
    const bar = svgNode("rect", { x, y: row.total_centavos >= 0 ? y : baseline,
      width: step * 0.58, height: Math.max(barHeight, 1), rx: Math.min(3, barHeight / 2),
      class: `month-bar${isPeak ? " is-peak" : ""}${row.total_centavos < 0 ? " is-negative" : ""}${row.registros === 0 ? " is-missing" : ""}`,
      fill: row.total_centavos < 0 ? "var(--negative)" : row.registros === 0 ? "var(--line)" : isPeak ? "var(--accent)" : "var(--navy-soft)" });
    bar.style.setProperty("--bar-origin", row.total_centavos < 0 ? "center top" : "center bottom");
    bar.style.setProperty("--bar-delay", `${index * 25}ms`);
    group.append(bar);
    if (isPeak) group.append(svgNode("text", { x: left + index * step + step / 2, y: Math.max(top - 10, y - 10), "text-anchor": "middle", class: `peak-label${row.total_centavos < 0 ? " negative-value" : ""}`, fill: row.total_centavos < 0 ? "var(--negative)" : "var(--accent-dark)", "font-size": 14, "font-weight": 700 }, compact.format(row.total_centavos / 100)));
    svg.append(group);
    svg.append(svgNode("text", { x: left + index * step + step / 2, y: bottom + 25, "text-anchor": "middle", fill: "var(--muted)", "font-size": 16 }, row.nome.slice(0, 3)));
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
      renderReading(summary, ranking.linhas, monthly.linhas); updatePresentation();
    } else renderRecords(await request("/api/registros", { pagina: page }));
    $("resultados").hidden = false;
    state.failed = false;
    updateConsultationStatus();
    updateNavigation();
    document.dispatchEvent(new CustomEvent("pagamentos:updated", { detail: { full } }));
    return true;
  } catch (error) {
    if (error.name !== "AbortError") {
      state.failed = true;
      $("erro-texto").textContent = error.message || "Não foi possível acessar o servidor local. Confira se a janela da aplicação continua aberta.";
      $("erro").hidden = false;
      $("alerta").hidden = true;
      if ($("qualidade-dados")) $("qualidade-dados").hidden = true;
      $("resultados").hidden = true;
      $("recorte").textContent = "Consulta não concluída. Tente novamente.";
      consultationStatus("Consulta não concluída", "error");
    }
    return false;
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
    for (const [id, code, name] of [["exemplo-saude", "440901", "FUNDO ESTADUAL DE SAÚDE"], ["exemplo-penal", "460113", "POLÍCIA PENAL DO ESPIRITO SANTO"]]) {
      const unit = options.unidades.find((row) => String(row.codigo) === code && row.nome === name);
      $(id).dataset.unit = unit?.chave || "";
      $(id).hidden = !unit;
    }
    state.ready = true;
    await load();
  } catch (error) {
    state.failed = true;
    $("erro-texto").textContent = error.message || "Não foi possível carregar a base. Confira se a aplicação continua aberta.";
    $("erro").hidden = false; $("resultados").hidden = true;
    if ($("qualidade-dados")) $("qualidade-dados").hidden = true;
    $("recorte").textContent = "Base indisponível.";
    consultationStatus("Base indisponível", "error");
    busy(false);
  }
}
$("filtros").addEventListener("submit", (event) => { event.preventDefault(); applyFilters({ mes: $("mes").value, unidade: $("unidade").value }); });
$("limpar").addEventListener("click", () => applyFilters({ mes: "", unidade: "" }));
$("anterior").addEventListener("click", () => load(state.page - 1, false));
$("proxima").addEventListener("click", () => load(state.page + 1, false));
$("tentar").addEventListener("click", () => state.ready ? load() : initialize());
$("modo-apresentacao").addEventListener("click", () => {
  document.body.classList.toggle("presentation-mode");
  document.body.classList.remove("filters-expanded");
  $("abrir-filtros").setAttribute("aria-expanded", "false");
  $("abrir-filtros").textContent = "Ajustar filtros";
  updatePresentation();
  hideTooltip();
  document.dispatchEvent(new CustomEvent("pagamentos:presentation", { detail: { active: document.body.classList.contains("presentation-mode") } }));
  window.scrollTo({ top: 0, behavior: "instant" });
});
$("abrir-filtros").addEventListener("click", () => {
  const expanded = document.body.classList.toggle("filters-expanded");
  $("abrir-filtros").setAttribute("aria-expanded", String(expanded));
  $("abrir-filtros").textContent = expanded ? "Recolher filtros" : "Ajustar filtros";
  if (expanded) $("unidade").focus();
});
$("exemplo-panorama").addEventListener("click", () => $("limpar").click());
for (const [id, month] of [["exemplo-saude", "12"], ["exemplo-penal", "1"]]) $(id).addEventListener("click", () => {
  applyFilters({ mes: month, unidade: $(id).dataset.unit });
});
for (const id of ["mes", "unidade"]) $(id).addEventListener("change", updateConsultationStatus);
function updateNavigation() {
  const links = [...document.querySelectorAll(".sidebar nav a")];
  let active = links[0];
  for (const link of links) {
    const section = document.querySelector(link.getAttribute("href"));
    if (section && section.getBoundingClientRect().top <= 125) active = link;
  }
  for (const link of links) {
    if (link === active) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  }
}
let navigationQueued = false;
window.addEventListener("scroll", () => {
  if (navigationQueued) return;
  navigationQueued = true;
  requestAnimationFrame(() => { navigationQueued = false; updateNavigation(); });
}, { passive: true });
window.addEventListener("resize", updateNavigation);
window.addEventListener("resize", hideTooltip);
window.addEventListener("scroll", hideTooltip, { passive: true, capture: true });
document.addEventListener("pagamentos:loading", (event) => { if (event.detail.active) hideTooltip(); });
document.addEventListener("keydown", (event) => { if (event.key === "Escape") dismissActiveTooltip?.(); });
document.addEventListener("pointerdown", (event) => { if (!event.target.closest?.(".bar-group")) hideTooltip(); });
updateNavigation();
initialize();
