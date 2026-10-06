# Verificação da entrega

Revisão de **05/10/2026**, referente à POC **Pagamentos ES 2024 / cp5.data**, turma **2ESPH-2026**. Este registro distingue verificações técnicas executadas, evidências da preparação anterior e providências que dependem do grupo ou da entrega à banca.

## Código e dados verificados nesta revisão

- **27 testes automatizados aprovados**, executados com `python -m unittest discover -s tests -v`. Abrangem consultas, filtros, paginação, exportações, erros, recuperação da base compactada, valores ausentes e seis casos de preparação com arquivos sintéticos. Os testes não modificam a base real.
- `node --check static/app.js` e `node --check static/motion.js` concluídos sem erro de sintaxe.
- Base SQLite aberta em modo somente leitura: `PRAGMA integrity_check` retornou **ok**.
- O SHA-256 da base foi preservado durante a auditoria e corresponde ao conteúdo de `data/pagamentos_2024.sqlite3.gz` descompactado em memória.
- **505.950 registros**, **117 unidades gestoras** e **12 meses**. Total líquido: **1.033.709.885.862 centavos**, equivalente a **R$ 10.337.098.858,62**.
- O resumo da aplicação, o ranking completo e a série mensal foram recalculados sobre a base. Seus totais coincidem com o JSON de análise e os arquivos `ranking_unidades.csv` e `evolucao_mensal.csv`.
- Preservados **156.177 valores positivos**, **339.887 zeros** e **9.886 negativos**. Os campos utilizados pela POC não apresentaram valores monetários, datas ou meses ausentes na base recebida.
- **Saúde (440901) em dezembro:** 7.790 registros e **R$ 185.199.026,38**, reconfirmados pela consulta da aplicação à base.
- **Polícia Penal (460113) em janeiro:** zero registros, reconfirmados pela consulta.
- A amostra interna de **10.000 IDs**, semente **2024**, foi reproduzida e coincide com a tabela de amostra. Contém **3.126 valores positivos**; o IC de Wilson de 95% é **30,36% a 32,18%**. A proporção exata na base é **30,87%**.

A auditoria registrada na preparação dos quatro CSVs permanece em `data/resumo_analise.json` e `data/auditoria_arquivos.csv`: não registrou duplicatas completas, repetições do ID de origem ou datas e valores monetários inválidos. O campo original `Orgao` está vazio nas 505.950 linhas; o agrupamento usa código e nome da unidade gestora. Essa preparação integral dos arquivos de origem não foi executada novamente nesta revisão.

O enunciado caracteriza os arquivos fornecidos como **recorte sistemático**. A consulta integral desse recorte e a amostra aleatória interna são etapas diferentes; os resultados não representam uma estimativa da totalidade desconhecida do Estado.

## Interface conferida nesta sessão

A conferência no navegador, realizada nesta sessão, abrangeu **1366 × 768**, **390 × 844**, **320 × 720** e **778 × 764**, com as seguintes interações:

- Quatro telas distintas: **Visão geral**, **Distribuição**, **Registros** e **Metodologia**, com uma tela ativa por vez e rolagem interna.
- Navegação lateral e por **Anterior / Próxima** no rodapé; atalhos **Alt + 1–4** e histórico do navegador.
- Filtros globais de mês e unidade, acessíveis por **Abrir filtros**, preservados entre telas. A navegação não dispara uma nova consulta.
- Consultas de exemplo, alteração e remoção de filtros, paginação dos registros e retorno ao recorte completo.
- Carregamento com prévia estrutural e etapas correspondentes às respostas reais de indicadores, ranking, série mensal e registros. A tela **Metodologia** permanece acessível durante a consulta.
- Modo apresentação com as quatro telas e navegação no rodapé; ranking com até cinco unidades nesse modo e até dez no modo normal.
- Valores finais dos indicadores sem contagem artificial, ícones SVG e recursos visuais locais. A implementação respeita a preferência por movimento reduzido.

As verificações de interfaces anteriores não substituem as da versão atual. Não se atribuem à revisão de quatro telas as contagens antigas de 66 ou 216 asserções.

## Conteúdo distribuído e segurança

A varredura desta revisão examinou os arquivos de texto rastreados, o XML do PPTX e o texto/metadados dos PDFs. Não encontrou padrões de credenciais, chaves privadas ou CPF/CNPJ formatados. Essa verificação por padrões não é uma garantia de ausência de qualquer informação sensível.

O esquema da base compactada foi conferido por equivalência com a SQLite auditada: não inclui CPF/CNPJ/NIS, nomes de favorecidos, histórico livre ou dados bancários. Os CSVs derivados contêm agregados, auditoria de arquivos ou IDs locais da amostra. Os nomes e RMs dos integrantes fazem parte da identificação acadêmica informada pelo grupo.

Os quatro ZIPs originais, que contêm campos excluídos da POC, não estão entre os arquivos distribuídos. A captura de tela da interface anterior foi retirada dos materiais atuais.

O ZIP público gerado por `scripts/empacotar.py` foi extraído em uma pasta nova. A integridade do ZIP e os hashes de todos os arquivos do manifesto foram conferidos. A extração contém a base compactada, sem depender da SQLite já existente no projeto original. A função de recuperação do aplicativo extraído criou a base, confirmou sua integridade e produziu o mesmo SHA-256 da referência; uma segunda chamada preservou a base existente.

A aplicação da pasta extraída foi iniciada separadamente, sem abrir o navegador, na porta local 8768. A página servida contém as quatro telas; a API reproduziu o total anual, Saúde em dezembro e Polícia Penal em janeiro sem registros. Esse processo de teste foi encerrado ao concluir. A conferência utilizou o Python deste computador e não substitui o teste no equipamento da apresentação. O manifesto e o SHA-256 gerados junto ao pacote permitem conferir seu conteúdo e sua integridade.

## Materiais, equipe e apresentação

Os materiais atualizados contêm **relatório técnico de oito páginas**, **apresentação em PDF de oito páginas**, **PPTX de oito slides** e **roteiro de duas páginas**. Contagens, textos, notas de apresentação e referências às quatro telas foram conferidos. O PPTX preserva dois gráficos nativos com planilhas de dados incorporadas. A geração também passou por revisão de estrutura, disposição dos elementos e fontes.

O roteiro e as notas dos slides concordam na divisão proposta: **Luigi, dois minutos; Rogério, três; Bruno, quatro; Anthony, dois**. As notas somam **660 segundos**, com mais um minuto de margem dentro dos 12 minutos. Bruno conduz a demonstração da POC. Essa distribuição organiza o ensaio e não atribui autoria passada das partes.

O orçamento é um **planejamento simulado**, não um gasto realizado: pessoal de R$ 68.800 e infraestrutura de R$ 3.200 compõem subtotal de R$ 72.000; contingência de 20% acrescenta R$ 14.400, totalizando **R$ 86.400**. A operação estimada é **R$ 1.800/mês**. Essa memória de cálculo é aritmeticamente consistente, coincide entre os materiais finais e fica abaixo do teto acadêmico de R$ 180.000. Os números da base, dos cenários de demonstração e do exercício estatístico também foram conciliados com os resultados auditados.

| Integrante | RM | Responsabilidade proposta no planejamento |
|---|---|---|
| Luigi Mendes Cabrini | 563552 | Produto e gestão |
| Bruno Koeke | 561309 | Dados e análise |
| Rogério Cruz Arroyo | 563517 | Desenvolvimento |
| Anthony Sforzin | 562096 | Testes e documentação |

Nomes e RMs foram informados pelo grupo. Funções, dedicação e entregáveis descrevem a proposta simulada; não comprovam contribuições passadas nem substituem a descrição honesta do trabalho efetivamente realizado. Cada integrante precisa revisar o conteúdo, assumir sua parte e preparar a defesa.

O grupo decidiu manter quatro integrantes. O enunciado indica cinco a oito; não há autorização do professor registrada para essa diferença.

O **enunciado original do CP2**, seção 5, exige que todos conheçam a proposta e estejam preparados para responder sobre sua contribuição e as decisões do grupo. Não determina tempo mínimo individual de fala nem afirma literalmente que cada integrante precisa falar. A participação e a qualidade das respostas fazem parte da avaliação. Recomenda-se que todos estejam presentes e ensaiem uma parte da apresentação; essa é uma orientação de preparação, não uma exigência literal adicional.

## Acesso e providências externas

- A visibilidade **pública** do repositório `Stratfy/cp5-data` foi confirmada em **05/10/2026** pelo conector do GitHub.
- A aplicação continua sendo uma POC local. O endereço `http://127.0.0.1:8765/` funciona no computador que executa o servidor; não é um endereço público do dashboard.
- O enunciado do CP2 pede repositório com POC executável, README e instruções para reproduzir a demonstração, além de apresentação ao vivo e links acessíveis à banca. Não contém exigência explícita de hospedar o dashboard na internet.
- Testar o pacote no computador da apresentação, com **Python 3.10 ou superior**, e manter a janela do servidor aberta. O funcionamento neste computador não comprova a preparação de outro equipamento.
- Revisar as responsabilidades reais, compartilhar os materiais com o grupo e ensaiar a demonstração e as respostas.
- O prazo indicado para o relatório da turma 2ESPH era **04/10/2026 às 23h59**; a apresentação está indicada para **06/10/2026**. Este registro de 05/10 não comprova o envio no prazo. O grupo precisa conferir o comprovante de entrega e as orientações do canal indicado em aula.

A assistência de IA na programação, análise e redação está declarada. A aplicação não utiliza IA em tempo de execução. As verificações técnicas não substituem a revisão humana, o ensaio ou a confirmação do envio.

Os logs e resultados estruturados desta revisão estão em `work/delivery-2026-10-05/`, pasta de evidências locais que não integra automaticamente o repositório ou o pacote distribuído.
