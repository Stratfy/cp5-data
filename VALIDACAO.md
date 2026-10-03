# Verificação da entrega

Conferências técnicas executadas em 03/10/2026 com os quatro arquivos de 2024 fornecidos na atividade. Este registro distingue os resultados verificados das pendências de revisão humana e entrega.

- 505.950 registros importados e 117 unidades gestoras.
- Total líquido de ValorPago: 1.033.709.885.862 centavos, equivalente a R$ 10.337.098.858,62.
- Soma do ranking completo e soma dos 12 meses iguais ao total da base.
- 156.177 valores positivos, 339.887 zeros e 9.886 valores negativos preservados.
- Zero duplicatas completas, IDs de origem repetidos, datas inválidas ou valores monetários inválidos na carga recebida.
- Campo Orgao vazio nas 505.950 linhas. As consultas usam código e nome de UnidadeGestora.
- Integridade SQLite verificada. Recuperação da base compactada gera arquivo com o mesmo hash da base preparada.
- 21 testes automatizados aprovados: cálculos, filtros, paginação, rastreabilidade, exportação, erros, recuperação gzip e sete casos adicionais de valores monetários ausentes e datas fora do calendário. Os testes verificam a diferença entre ausência, zero e valor negativo, sem substituir valores ausentes por zero.
- Consulta Fundo Estadual de Saúde (440901), dezembro: 7.790 registros e R$ 185.199.026,38, conferida na interface e na base.
- Consulta Polícia Penal (460113), janeiro: zero registros e estado vazio, sem confundir ausência com uma soma de zero.
- Registros de origem conferidos diretamente nos CSVs, com arquivo, linha, ID e ValorPago.
- Amostra interna de 10.000 IDs reproduzida com semente 2024. São 3.126 valores positivos; IC Wilson95% de 30,36% a 32,18%, restrito à base local.
- Relatório com 8 páginas e apresentação com 8 slides, revisados visualmente.

Após a revisão de design, a interface foi conferida em larguras de 390, 820, 1280 e 1440 pixels, sem rolagem horizontal da página. O gráfico e a tabela mantêm rolagem interna quando necessária. Total completo, rótulos, contraste, destaques e estado sem registros foram revisados. Alterar os controles conserva os filtros aplicados e pede uma nova consulta; os destaques de Saúde em dezembro correspondem aos 7.790 registros e R$ 185.199.026,38. Navegação por seções e foco das barras pelo teclado foram incluídos. O cronograma dos slides foi alinhado às seis etapas do relatório, e os materiais usam a mesma paleta navy/teal.

O enunciado define a fonte como **recorte sistemático**; todos os registros dos quatro arquivos locais foram analisados, sem extrapolação para o Estado. A amostra interna de 10.000 IDs é um sorteio aleatório distinto, restrito a essa base. Referências: [Portal de Dados Abertos ES, recurso de despesas 2024](https://dados2.es.gov.br/dataset/portal-da-transparencia-despesas-execucao-orcamentaria-e-financeira/resource/b34ae52a-a739-412a-9bab-80f53ba72f4f?inner_span=True) e [NIST, intervalo de Wilson](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm).

| Integrante informado | RM | Responsabilidade proposta |
|---|---|---|
| Luigi Mendes Cabrini | 563552 | Produto e gestão |
| Bruno Koeke | 561309 | Dados e análise |
| Rogério Cruz Arroyo | 563517 | Desenvolvimento |
| Anthony Sforzin | 562096 | Testes e documentação |

Os nomes e RMs estão confirmados no registro do grupo. Funções, dedicação e entregáveis são propostas; não há confirmação de que essas responsabilidades já foram assumidas ou cumpridas. A equipe mantém quatro integrantes por decisão do grupo, embora o enunciado indique cinco a oito e não haja autorização do professor registrada para a exceção.

Os nomes/RMs foram conferidos no relatório, no guia e na apresentação finais. As notas dos oito slides somam 150, 180, 210 e 180 segundos por integrante, totalizando 12 minutos; essa conferência de roteiro não substitui um ensaio real. O relatório tem 8 páginas, o guia 2 e a apresentação 8; as cópias entregues em docs correspondem às versões revisadas. O PPTX preserva dois gráficos e cinco tabelas editáveis.

A nova interface foi conferida no navegador com a base real e com uma base sintética de sete linhas. O aviso distinguiu valor ausente, zero e negativo, informou a diferença entre a série mensal e o total disponível e mostrou “Não informado” no recorte sem valores válidos. O aviso permaneceu legível em 390 pixels, sem rolagem horizontal da página. A base sintética foi usada somente para QA e não integra os dados da entrega.

Pendências que a verificação técnica não resolve: revisão dos quatro integrantes; distribuição real de responsabilidades; ensaio de 12 minutos e preparação das respostas; envio no canal indicado e comparecimento de todos em 06/10/2026. O prazo do relatório da turma 2ESPH é 04/10/2026 às 23h59. Nenhum registro deste arquivo comprova que a entrega foi enviada ou que os integrantes já ensaiaram.

Acesso da banca pendente: na verificação sem login de 03/10/2026, a API do GitHub retornou 404 para o repositório, embora a cópia autenticada tenha funcionado. É necessário conceder acesso à banca ou definir acesso público. Os links estão preenchidos; a visibilidade não foi alterada e o acesso público não está comprovado.

O trabalho recebeu assistência de IA na programação, análise e redação. Foram executadas auditoria dos dados, reconciliações, reprodução da amostra e do IC, testes do aplicativo, conferência de origem e revisão visual técnica. A revisão humana pelos integrantes segue pendente e deve validar os resultados e a contribuição de cada pessoa. A aplicação não utiliza IA em tempo de execução. Nenhum arquivo original foi alterado. O conjunto local não comprova a cobertura integral das despesas do Estado.
