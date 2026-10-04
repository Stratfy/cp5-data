# Pagamentos ES 2024

Turma **2ESPH-2026**. [Repositório de código e materiais](https://github.com/Stratfy/cp5-data).

- [Relatório técnico de 8 páginas](docs/relatorio_pagamentos_es_2024.pdf)
- [Apresentação editável de 8 slides](docs/apresentacao_pagamentos_es_2024.pptx)
- [Apresentação em PDF](docs/apresentacao_pagamentos_es_2024.pdf)
- [Roteiro de 11 minutos e 1 minuto de margem para quatro integrantes](docs/guia_apresentacao_pagamentos_es_2024.pdf)
- [Captura do painel para contingência](docs/previa_painel.jpg)
- [Conferência da entrega](VALIDACAO.md)

| Integrante | RM | Papel proposto | Dedicação estimada no ciclo de 16 semanas | Entregável proposto |
|---|---|---|---|---|
| Luigi Mendes Cabrini | 563552 | Produto e gestão | 160 h; 10 h/semana | Problema, requisitos, proposta técnica e organização dos marcos |
| Bruno Koeke | 561309 | Dados e análise | 240 h; 15 h/semana | Importação, auditoria, indicadores e verificação estatística |
| Rogério Cruz Arroyo | 563517 | Desenvolvimento | 320 h; 20 h/semana | Aplicação, integração da base e instruções de execução |
| Anthony Sforzin | 562096 | Testes e documentação | 160 h; 10 h/semana | Testes, reprodução, roteiro e preparação da demonstração |

Nomes e RMs foram informados pelo grupo. Papéis, entregáveis e horas são propostas para o planejamento simulado; não comprovam contribuições já realizadas nem responsabilidades aceitas. Cada integrante precisa revisar e assumir sua parte antes da apresentação.

A equipe mantém quatro integrantes por decisão do grupo. O enunciado indica cinco a oito; não há autorização do professor registrada para a exceção.

Prova de conceito acadêmica para investigar os pagamentos registrados nos quatro arquivos de despesas do Espírito Santo de 2024 fornecidos na atividade. Público inicial: gestores públicos e analistas de controle interno que precisam comparar unidades gestoras e períodos e conferir a origem dos números.

## Abrir a aplicação

1. Extraia a pasta completa do projeto. Mantenha `app.py`, `static/` e `data/` juntos.
2. No Windows, dê dois cliques em **iniciar.bat**. O navegador abre em **http://127.0.0.1:8765**.
3. Deixe a janela da aplicação aberta durante o uso. Para encerrar, pressione **Ctrl+C** nessa janela.

Requer **Python 3.10 ou superior**. Não precisa instalar bibliotecas, fazer login ou usar internet. O iniciador verifica a versão disponível, tenta `py -3`, depois `python` e, como alternativa, o Python do ambiente Codex na pasta do usuário. Em outro computador, use Python instalado normalmente. Teste a pasta extraída no equipamento da apresentação antes da aula.

Alternativa pelo terminal, na pasta do projeto:

```powershell
python app.py
```

Se a porta estiver ocupada, use `python app.py --port 8766`. A opção `--no-browser` evita a abertura automática do navegador. O servidor atende apenas no próprio computador por padrão (`127.0.0.1`). Esta POC não foi preparada para exposição pública na internet.

O projeto inclui a base pronta compactada `data/pagamentos_2024.sqlite3.gz`. Na primeira execução, a aplicação a descompacta automaticamente; não é preciso baixar novamente os ZIPs originais. Para publicação em repositório, a cópia de aproximadamente 138 MiB é ignorada pelo Git; publique `data/pagamentos_2024.sqlite3.gz`, de aproximadamente 18 MiB. Quando a base estiver ausente e a cópia compactada existir, a aplicação a recupera automaticamente na mesma pasta, verifica a integridade SQLite e só então publica o arquivo. Uma base existente é preservada. A primeira abertura nesse caso pode levar alguns segundos adicionais.

## O que demonstrar

O painel adota identidade corporativa: marinho e azul, superfícies brancas sobre fundo cinza-claro, tipografia sem serifa, navegação lateral e cartões com hierarquia visual. As transições de entrada e atualização são curtas; os números sempre aparecem no valor final. A preferência do sistema por movimento reduzido é respeitada. Fontes, ícones e gráficos funcionam sem internet.

Ative **Modo apresentação** no cabeçalho para destacar os indicadores e gráficos. Nesse modo, o ranking mostra até **cinco unidades**, com quantidade explícita; a exportação continua incluindo o ranking completo. Use **Ajustar filtros** para abrir os controles e **Sair da apresentação** para voltar à tela habitual, com até dez unidades. A tabela de registros e a metodologia continuam disponíveis abaixo.

Os atalhos **Saúde em dezembro**, **Polícia Penal em janeiro** e **Panorama completo** aplicam consultas prontas. O texto **Leitura do recorte** acompanha os filtros e destaca a participação das três primeiras unidades e do maior mês quando os dados permitem essa comparação. Dados incompletos, saldo zero, saldo negativo e ausência de registros recebem mensagens próprias. Os percentuais descrevem o total líquido do recorte, sem inferência sobre eficiência ou causalidade.

Clique em uma unidade do ranking para explorá-la, mantendo o mês já consultado. Os filtros aplicados podem ser removidos individualmente pelo **×**. No gráfico mensal, passe o mouse ou navegue pelo teclado para ver o valor exato e a quantidade de registros; **Esc** fecha o detalhe. A tabela mensal oferece os mesmos valores para consulta e acessibilidade.

1. Abra o painel com **Todas as unidades / Todos os meses**: total líquido **R$ 10.337.098.858,62**, **505.950 registros**, **117 unidades gestoras** e **9.886 registros negativos**.
2. Veja o ranking: Fundo Estadual de Saúde, Fundo Financeiro e Secretaria de Estado da Educação lideram o recorte.
3. Escolha uma unidade gestora e clique em **Consultar**. Os indicadores, os dois gráficos e a tabela passam a mostrar esse filtro.
4. Escolha um mês e consulte novamente. O gráfico mensal mostra apenas esse mês. Volte a **Todos os meses** para comparar o calendário.
5. Confira o nome do CSV e a linha de origem de um registro. Baixe o ranking, a série mensal ou os registros filtrados. As exportações correspondem aos filtros aplicados, e a de registros inclui todas as linhas do recorte, não apenas a página visível.
6. Use **Limpar** ou **Panorama completo** para retornar ao panorama. Para demonstrar ausência de dados, use o atalho **Polícia Penal em janeiro** ou escolha `460113 · POLÍCIA PENAL DO ESPIRITO SANTO` e `Janeiro`; essa combinação foi conferida no banco e na interface e não tem registros na base recebida. Uma soma zero com registros não é ausência de dados.

As duas perguntas investigadas são **quais unidades gestoras concentram a soma líquida de ValorPago no recorte** e **como essa soma varia entre os meses de 2024**. O painel oferece tabela de origem e exportações para tornar os resultados verificáveis.

A navegação lateral leva ao resumo, às análises, aos registros e à metodologia. Os destaques mostram a unidade com maior total e o mês com maior soma líquida no recorte aplicado. Ao alterar um filtro, a mensagem pede que você clique em **Consultar**; os dados e as exportações mantêm o recorte anterior até a consulta terminar. No celular, deslize o gráfico mensal para ver os demais meses ou abra **Ver valores mensais**. As barras também podem receber foco pelo teclado, com descrição acessível dos valores.

## Dados e reprodução

Entradas: os quatro ZIPs `despesas_es_2024_completo_parte_01.zip` até `despesas_es_2024_completo_parte_04.zip`. Os ZIPs de 2025 não entram nesta POC. O campo `Orgao` está vazio em todos os registros recebidos; por isso, a comparação usa `CodigoUnidadeGestora` e `UnidadeGestora` em conjunto.

O enunciado caracteriza os arquivos fornecidos como **recorte sistemático**. A preparação lê integralmente esse recorte local de 2024; isso não o transforma em amostra aleatória estadual nem comprova a base integral do Estado. O sorteio aleatório interno usado no exercício de intervalo de confiança é uma etapa distinta, restrita aos registros desta base.

Referências diretas: [recurso oficial de despesas de 2024 do Portal de Dados Abertos ES](https://dados2.es.gov.br/dataset/portal-da-transparencia-despesas-execucao-orcamentaria-e-financeira/resource/b34ae52a-a739-412a-9bab-80f53ba72f4f?inner_span=True) e [NIST: intervalo de Wilson para proporções](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm). O dicionário fornecido na atividade é `dicionario_despesas.pdf`, versão 1.0 de 13/07/2021, seção Despesa. A versão atual do recurso oficial não foi usada como substituta dos quatro ZIPs do professor; a auditoria dos arquivos originais está em `data/auditoria_arquivos.csv`.

Para reconstruir a base a partir dos arquivos originais, mantendo-os intactos:

```powershell
python preparar_dados.py --origem "C:\Users\bruno\Downloads"
```

Em outro computador, substitua o caminho pela pasta que contém os quatro ZIPs. A preparação lê diretamente os CSVs de cada ZIP, converte os valores com `Decimal`, armazena centavos inteiros, padroniza datas válidas, registra arquivo e linha de origem e produz auditoria. A linha 1 do CSV é o cabeçalho. O processo gera a base e os arquivos abaixo em `data/`:

| Arquivo | Uso |
|---|---|
| `pagamentos_2024.sqlite3` | Base da aplicação, com os campos necessários ao painel |
| `resumo_analise.json` | Resultados, cobertura, auditoria, estatística e reconciliações |
| `auditoria_arquivos.csv` | Contagem, tamanho e SHA-256 de cada parte |
| `ranking_unidades.csv` | Ranking completo das unidades |
| `evolucao_mensal.csv` | Valores agregados por mês |
| `amostra_estatistica.csv` | Amostra interna para reproduzir o exercício estatístico |

Após uma reconstrução, a base `.sqlite3` nova será utilizada pela aplicação. Se for redistribuir a cópia `.gz`, compacte a base atualizada para evitar que versões antigas sejam distribuídas. Não é necessário executar a preparação ao usar a base pronta incluída.

Na preparação, grupos que possuem registros, mas nenhum ValorPago válido, têm total `null` no JSON e célula vazia nos CSVs. Um conjunto sem registros tem contagem e total zero. Meses sem valores disponíveis não entram no cálculo das estatísticas monetárias mensais. Uma reconstrução sem resultados regrava os CSVs somente com os cabeçalhos, evitando que arquivos da carga anterior permaneçam como se fossem atuais.

O processo preserva todas as linhas do recorte, incluindo **156.177 valores positivos, 339.887 zeros e 9.886 negativos**. A carga recebida não apresentou duplicatas completas ou ausências nos campos essenciais. Identificadores repetidos são auditados e não provocam remoção automática de linhas. Outros campos originais podem estar vazios e constam na auditoria dos 71 campos.

## Como interpretar

- Métrica: **soma líquida de ValorPago registrado**, incluindo zeros e negativos. O saldo negativo registrado é **−R$ 381.794.044,19**.
- `Data` é referência da realização da despesa. A coluna técnica `data_pagamento` foi mantida no código, mas o painel e o CSV a apresentam como **Data do registro / DataRegistro**; ela não comprova a data de transferência bancária.
- `ValorEmpenho`, `ValorLiquidado` e `ValorRap` representam campos distintos e não são adicionados ao total de `ValorPago`.
- O calendário tem registros nos 12 meses, de **02/01/2024 a 31/12/2024**. Isso não comprova cobertura integral das despesas estaduais. O alcance da análise são os quatro arquivos recebidos.
- O ranking agrupa por código **e** nome da unidade. Espaços externos são removidos; códigos e nomes diferentes continuam separados.
- Um mês com soma zero pode ter registros de valor zero ou valores que se compensam. A tabela mensal informa a contagem e diferencia ausência de linhas.
- Se uma carga tiver valores ausentes, os totais somam os valores disponíveis e o painel informa quantos registros ficaram sem ValorPago válido. Um recorte sem nenhum valor válido aparece como **Não informado**. Ausências não são substituídas por zero. Registros sem mês válido continuam rastreáveis, mas ficam fora da série mensal; o aviso explica a diferença de valor entre a série e o total disponível.
- Os dados descrevem concentração e variação; não demonstram eficiência, irregularidade ou a causa de uma mudança.
- A base e os CSVs do painel excluem CPF/CNPJ/NIS, nomes dos favorecidos, histórico livre e dados bancários.

O relatório inclui um exercício de intervalo de confiança de 95% para a proporção de registros com valor positivo em uma amostra aleatória interna de 10.000 linhas, com semente 2024. Os limites de Wilson são **30,36% a 32,18%**, e a proporção exata nesta base é **30,87%**. Esse intervalo é didático e se refere à base recebida; não estima a totalidade desconhecida do Estado. O painel calcula os totais sobre todas as linhas do recorte, sem amostragem.

## Arquitetura

```text
4 ZIPs originais → preparar_dados.py → SQLite + auditoria + resultados
                                             ↓ somente leitura
Navegador ← HTML/CSS/JavaScript ← app.py / API local ← SQLite
```

Escolha técnica: **Python e sua biblioteca padrão**, com SQLite e uma interface web de uma tela. A proposta aceita outra tecnologia web mediante justificativa; esta opção elimina a instalação de pacotes externos e permite executar a demonstração offline. Os gráficos usam elementos HTML e SVG gerados pela própria interface, sem serviços ou arquivos externos.

O servidor é `ThreadingHTTPServer`. Cada consulta abre uma conexão SQLite somente leitura e a fecha ao finalizar. Os filtros usam parâmetros SQL; os valores monetários continuam inteiros em centavos nas consultas. A interface carrega os resultados de consulta em paralelo, indica carregamento, trata falhas e permite tentar novamente. A tabela exibe 20 registros por página, com ordem estável de data e ID local decrescentes.

| Endpoint GET | Resultado |
|---|---|
| `/api/opcoes` | Meses e unidades disponíveis |
| `/api/resumo` | Total, contagens, negativos, zeros e cobertura do filtro |
| `/api/ranking` | Até 10 maiores unidades por total líquido |
| `/api/mensal` | Meses do filtro, com valores e contagens |
| `/api/registros?pagina=1` | Registros paginados e origem verificável |
| `/api/exportar?tipo=mensal` | CSV mensal |
| `/api/exportar?tipo=ranking` | CSV do ranking completo |
| `/api/exportar?tipo=detalhes` | CSV com todos os registros filtrados |

Os filtros comuns são `mes=1` até `mes=12` e `unidade`, codificada como uma lista JSON `[codigo,nome]` enviada pela interface. Sem filtro, a consulta inclui todo o recorte de 2024. Parâmetros repetidos, desconhecidos ou inválidos recebem resposta 400; rota inexistente recebe 404; base indisponível recebe 503. Exportações usam UTF-8 com BOM, separador `;` e decimal `,`. Textos que poderiam virar fórmulas em uma planilha recebem um apóstrofo inicial; valores monetários negativos continuam numéricos.

## Verificação

Execute os testes na pasta do projeto:

```powershell
python -m unittest discover -s tests -v
```

Os **27 testes automatizados** cobrem centavos e ajustes negativos, zeros, recorte do ano, combinação de filtros, meses sem registros, valores monetários ausentes, registros fora do calendário, ranking e reconciliação, paginação sem perda de linhas, origem verificável e IDs repetidos, consultas inválidas, SQL parametrizado, exportações e proteção contra fórmulas, rotas/erros e recuperação gzip sem sobrescrita ou base parcial. Seis casos exercitam a preparação completa com quatro ZIPs sintéticos: cargas completas, valores ausentes, estatísticas com um único mês numérico, cargas vazias e substituição de CSVs antigos. Os testes usam bases pequenas temporárias; não modificam a base entregue. A conferência da versão auditada e as pendências estão em `VALIDACAO.md`.

Na base real, o total do painel, a soma de todas as unidades do ranking e a soma dos 12 meses foram conciliados em **1.033.709.885.862 centavos**. A preparação também realiza `PRAGMA integrity_check`. A interface foi conferida no navegador com a base real.

## Assistência de IA e revisão humana

IA foi usada para apoiar a programação, preparar a análise e redigir os materiais. A aplicação pronta não consulta modelos de IA, não envia registros a um serviço externo e não produz interpretações automáticas por IA.

A verificação técnica executada incluiu leitura do enunciado e do dicionário, auditoria completa dos quatro CSVs, reconciliação dos totais em centavos, reprodução do sorteio e do intervalo de Wilson, testes automatizados do aplicativo, conferência de registros nos arquivos de origem, inspeção visual dos documentos e consulta da interface com a base real. Essas checagens verificam o resultado técnico; não substituem a revisão de cada integrante.

A revisão humana pelos quatro integrantes, a confirmação dos papéis propostos e o ensaio conjunto ainda não estão comprovados. O roteiro prevê 11 minutos de conteúdo e 1 minuto de margem dentro do limite de 12 minutos. Cada pessoa deve revisar seu entregável e preparar a explicação de sua contribuição. A banca pode perguntar sobre a métrica, as limitações, a origem dos registros e a separação entre o recorte sistemático e a amostra aleatória interna.

## Conferência antes da entrega

- Conferir nomes, RMs e turma no relatório, na apresentação e no roteiro final.
- Revisar e assumir as responsabilidades propostas; a tabela não é um registro de trabalho já realizado.
- Ensaiar para 11 minutos, reservando 1 minuto de margem para alternar telas. Incluir resultado geral, Saúde em dezembro, rastreabilidade, exportação e Polícia Penal em janeiro sem registros.
- Levar o ZIP extraído, os slides em PDF e a captura de contingência; testar a aplicação no computador da apresentação.
- Conceder acesso à banca ao repositório e aos materiais vinculados ou definir acesso público. A verificação sem login de 04/10/2026 retornou 404 na API do GitHub, enquanto o acesso autenticado funcionou; o acesso da banca ainda não está confirmado. Os links já estão preenchidos, mas isso não comprova que a banca possa abri-los nem que a entrega foi enviada.
- Entregar PDF e links no canal indicado em aula até **04/10/2026 às 23h59**; apresentação da turma 2ESPH em **06/10/2026**. Todos os integrantes devem comparecer, conforme orientação da atividade.

## Limites e próximos passos

Esta versão tem uma tela, um ano e uma base estática. Não oferece autenticação, comparação com 2025, atualização automática, busca por favorecido ou detecção de irregularidades. Não foi testada para acesso público ou grande quantidade de usuários simultâneos. A exportação integral de mais de 500 mil registros é maior e pode demorar; para uma demonstração rápida, filtre uma unidade ou mês antes de baixá-la.

Evolução proposta: importar novas cargas com verificação de cobertura, ampliar os filtros, validar a experiência com usuários, medir desempenho e preparar hospedagem adequada. A escolha de manter o recorte pequeno favorece uma demonstração funcional e auditável.
