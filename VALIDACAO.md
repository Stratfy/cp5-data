# Verificação da entrega

Revisão técnica e visual de 04/10/2026. Este registro separa os resultados verificados das ações que dependem dos integrantes e do envio à banca.

A revisão corporativa da interface, da captura e dos documentos foi concluída. As 18 páginas finais passaram por revisão visual e as quatro cópias dos materiais em docs e outputs são idênticas. Esta atualização alterou a apresentação visual; os resultados de dados e lógica permanecem como evidência técnica já obtida.

## Dados e funcionamento

- 505.950 registros importados, 117 unidades gestoras e 12 meses de 2024.
- Total líquido de ValorPago: 1.033.709.885.862 centavos, equivalente a R$ 10.337.098.858,62.
- Ranking completo e série mensal conciliados com o total da base.
- 156.177 valores positivos, 339.887 zeros e 9.886 negativos preservados.
- Nenhuma duplicata completa, repetição de ID de origem, data inválida ou valor monetário inválido na carga recebida.
- Campo Orgao vazio nas 505.950 linhas. O agrupamento usa código e nome de UnidadeGestora.
- Integridade SQLite verificada. A cópia compactada recupera a mesma base por SHA-256.
- 27 testes automatizados aprovados. Além dos 21 casos da aplicação, seis regressões exercitam a preparação completa com quatro ZIPs sintéticos.
- A preparação mantém null/vazio quando existem registros, mas nenhum ValorPago válido. Estatísticas consideram meses com valores disponíveis. Cargas vazias regravam os CSVs com cabeçalhos, sem conservar resultados anteriores.
- Em carga sintética completa de 144 linhas, os resultados anteriores e posteriores à correção foram idênticos, exceto pelo timestamp da análise.
- Saúde (440901) em dezembro: 7.790 registros e R$ 185.199.026,38, conferidos na base e na interface.
- Polícia Penal (460113) em janeiro: zero registros e mensagens de ausência de dados.
- A amostra interna de 10.000 IDs, semente 2024, tem 3.126 valores positivos. O IC Wilson de 95% é 30,36% a 32,18%, para a proporção na base local. A proporção exata é 30,87%.

## Interface revisada

- Identidade corporativa concluída: monograma ES geométrico, marinho e azul, superfícies claras e tipografia Segoe UI/system sem serifa e sem itálico decorativo. Fontes do sistema e ícones SVG funcionam offline.
- Ranking clicável para explorar uma unidade preservando o mês aplicado; filtros removíveis individualmente; detalhe mensal com valor exato, registros, foco de teclado e fechamento com Esc.
- Transições de entrada e atualização sem contagem progressiva dos indicadores. Movimento reduzido respeitado no CSS e JavaScript; modo apresentação desativa animações.
- Modo apresentação com até cinco unidades no ranking, números maiores, filtros recolhíveis e atalhos para os cenários demonstrados. A tela normal preserva até dez unidades e as exportações mantêm o ranking completo.
- Destaques calculados conforme o recorte: no panorama, as três primeiras unidades concentram 40,66% do total líquido e dezembro reúne 15,94%.
- Verificação adicional da lógica visual com 66 asserções e revisão independente das interações com 216 verificações: chaves de unidades, ranking, filtros, tooltips, foco, bloqueio de consulta, movimento reduzido, ausência de registros e valores null, zero e negativos.
- Consultas de exemplo, abertura dos filtros, retorno ao panorama, mudança de modo e exportações com filtros conferidos no navegador.
- Layout corporativo conferido em navegador real em 1440 × 900, 1366 × 768 (normal e apresentação), 390 × 844 e 320 × 800. Sem transbordamento horizontal da página nem dos indicadores nos cenários conferidos. Gráfico mensal e tabela preservam rolagem interna quando necessária.
- Total geral, Saúde em dezembro e retorno ao panorama conferidos após a atualização visual. Gráficos em azul e marinho legíveis, sem erros ou avisos no console do navegador.
- Em 1366 × 768, o modo apresentação permite visualizar os indicadores, as cinco unidades e o gráfico mensal na primeira tela. As ações de exportação e os registros seguem abaixo.
- Captura real do modo apresentação atualizada em docs/previa_painel.jpg, para contingência, com conteúdo idêntico a outputs/painel_apresentacao.jpg.

## Materiais e revisão humana

Relatório com oito páginas e guia com duas páginas. A apresentação mantém oito slides. Os materiais seguem a identidade corporativa do site, com marinho e azul, fundos claros, títulos sem serifa e gráficos e tabelas com hierarquia consistente. O roteiro prevê 660 segundos de conteúdo e 60 segundos de margem, dentro dos 12 minutos: Luigi 140 s, Bruno 170 s, Rogério 190 s e Anthony 160 s. Essa divisão de roteiro não comprova ensaio nem contribuição já realizada.

Todas as páginas e slides finais foram renderizados e revisados visualmente. Nomes, RMs, contagem de páginas e tempos das notas foram conferidos automaticamente. O PDF da apresentação contém texto selecionável e elementos vetoriais; apenas a captura do painel é uma imagem. O PPTX preserva dois gráficos com dados editáveis e uma tabela de orçamento. As quatro cópias em docs correspondem às versões em outputs por conteúdo.

| Integrante | RM | Responsabilidade proposta |
|---|---|---|
| Luigi Mendes Cabrini | 563552 | Produto e gestão |
| Bruno Koeke | 561309 | Dados e análise |
| Rogério Cruz Arroyo | 563517 | Desenvolvimento |
| Anthony Sforzin | 562096 | Testes e documentação |

Nomes e RMs foram informados pelo grupo. Responsabilidades, dedicação e entregáveis são propostas do planejamento simulado, sujeitas à revisão de cada integrante. O grupo confirmou a decisão de permanecer com quatro pessoas. O enunciado pede cinco a oito e não há autorização do professor registrada para a exceção.

O enunciado define os dados como recorte sistemático. Todos os registros dos quatro arquivos locais foram analisados, sem extrapolação para o Estado. A amostra aleatória interna é uma etapa didática distinta. Referências: [Portal de Dados Abertos ES](https://dados2.es.gov.br/dataset/portal-da-transparencia-despesas-execucao-orcamentaria-e-financeira/resource/b34ae52a-a739-412a-9bab-80f53ba72f4f?inner_span=True) e [NIST: intervalo de Wilson](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).

## Pendências externas

- Cada integrante precisa revisar sua parte, confirmar sua responsabilidade e ensaiar as respostas.
- Testar o pacote no computador da apresentação, com Python 3.10 ou superior. Neste computador, a execução usa o Python do ambiente Codex; isso não comprova que outro equipamento tenha Python instalado.
- Garantir acesso da banca aos links. A API pública do GitHub retornou 404 sem login em 04/10/2026; o acesso autenticado confirmou o repositório. A visibilidade não foi alterada por esta revisão.
- Enviar PDF e links pelo canal indicado em aula até 04/10/2026 às 23h59 e comparecer à apresentação de 06/10/2026. Este registro não comprova envio ou comparecimento.

O trabalho recebeu assistência de IA na programação, análise e redação. A aplicação não utiliza IA em tempo de execução e não envia registros a serviços externos. Auditoria técnica e testes não substituem a revisão humana. Os arquivos originais e a base real de referência foram preservados.
