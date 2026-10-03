# Pagamentos ES 2024

Turma **2ESPH-2026**. Código e materiais: https://github.com/Stratfy/cp5-data

- [Relatório técnico de 8 páginas](docs/relatorio_pagamentos_es_2024.pdf)
- [Apresentação editável de 8 slides](docs/apresentacao_pagamentos_es_2024.pptx)
- [Apresentação em PDF](docs/apresentacao_pagamentos_es_2024.pdf)
- [Roteiro de 12 minutos para quatro integrantes](docs/guia_apresentacao_pagamentos_es_2024.pdf)
- [Conferência da entrega](VALIDACAO.md)

Os nomes ainda estão como **Integrante 1–4**. As responsabilidades são propostas. Confirmar com o professor a exceção para quatro integrantes, pois o enunciado pede cinco a oito.

Prova de conceito acadêmica para investigar os pagamentos registrados nos quatro arquivos de despesas do Espírito Santo de 2024 fornecidos na atividade. Público inicial: gestores públicos e analistas de controle interno que precisam comparar unidades gestoras e períodos e conferir a origem dos números.

## Abrir a aplicação

1. Extraia a pasta completa do projeto. Mantenha `app.py`, `static/` e `data/` juntos.
2. No Windows, dê dois cliques em **iniciar.bat**. O navegador abre em **http://127.0.0.1:8765**.
3. Deixe a janela da aplicação aberta durante o uso. Para encerrar, pressione **Ctrl+C** nessa janela.

Requer **Python 3.10 ou superior**. Não precisa instalar bibliotecas, fazer login ou usar internet. O iniciador tenta `py -3`, depois `python` e, como alternativa neste computador, o Python do ambiente Codex. Em outro computador, use Python instalado normalmente.

Alternativa pelo terminal, na pasta do projeto:

```powershell
python app.py
```

Se a porta estiver ocupada, use `python app.py --port 8766`. A opção `--no-browser` evita a abertura automática do navegador. O servidor atende apenas no próprio computador por padrão (`127.0.0.1`). Esta POC não foi preparada para exposição pública na internet.

O projeto inclui a base pronta compactada `data/pagamentos_2024.sqlite3.gz`. Na primeira execução, a aplicação a descompacta automaticamente; não é preciso baixar novamente os ZIPs originais. Para publicação em repositório, a cópia de aproximadamente 138 MiB é ignorada pelo Git; publique `data/pagamentos_2024.sqlite3.gz`, de aproximadamente 18 MiB. Quando a base estiver ausente e a cópia compactada existir, a aplicação a recupera automaticamente na mesma pasta, verifica a integridade SQLite e só então publica o arquivo. Uma base existente é preservada. A primeira abertura nesse caso pode levar alguns segundos adicionais.

## O que demonstrar

1. Abra o painel com **Todas as unidades / Todos os meses**: total líquido **R$ 10.337.098.858,62**, **505.950 registros**, **117 unidades gestoras** e **9.886 registros negativos**.
2. Veja o ranking: Fundo Estadual de Saúde, Fundo Financeiro e Secretaria de Estado da Educação lideram o recorte.
3. Escolha uma unidade gestora e clique em **Consultar**. Os indicadores, os dois gráficos e a tabela passam a mostrar esse filtro.
4. Escolha um mês e consulte novamente. O gráfico mensal mostra apenas esse mês. Volte a **Todos os meses** para comparar o calendário.
5. Confira o nome do CSV e a linha de origem de um registro. Baixe o ranking, a série mensal ou os registros filtrados. As exportações correspondem aos filtros aplicados, e a de registros inclui todas as linhas do recorte, não apenas a página visível.
6. Use **Limpar** para retornar ao panorama. Para demonstrar ausência de dados, escolha `460113 · POLÍCIA PENAL DO ESPIRITO SANTO` e `Janeiro`; essa combinação foi conferida no banco e na interface e não tem registros na base recebida. Uma soma zero com registros não é ausência de dados.

As duas perguntas investigadas são **quais unidades gestoras concentram a soma líquida de ValorPago no recorte** e **como essa soma varia entre os meses de 2024**. O painel oferece tabela de origem e exportações para tornar os resultados verificáveis.

## Dados e reprodução

Entradas: os quatro ZIPs `despesas_es_2024_completo_parte_01.zip` até `despesas_es_2024_completo_parte_04.zip`. Os ZIPs de 2025 não entram nesta POC. O campo `Orgao` está vazio em todos os registros recebidos; por isso, a comparação usa `CodigoUnidadeGestora` e `UnidadeGestora` em conjunto.

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

O processo preserva todas as linhas do recorte, incluindo **156.177 valores positivos, 339.887 zeros e 9.886 negativos**. A carga recebida não apresentou duplicatas completas ou ausências nos campos essenciais. Identificadores repetidos são auditados e não provocam remoção automática de linhas. Outros campos originais podem estar vazios e constam na auditoria dos 71 campos.

## Como interpretar

- Métrica: **soma líquida de ValorPago registrado**, incluindo zeros e negativos. O saldo negativo registrado é **−R$ 381.794.044,19**.
- `Data` é referência da realização da despesa. A coluna técnica `data_pagamento` foi mantida no código, mas o painel e o CSV a apresentam como **Data do registro / DataRegistro**; ela não comprova a data de transferência bancária.
- `ValorEmpenho`, `ValorLiquidado` e `ValorRap` representam campos distintos e não são adicionados ao total de `ValorPago`.
- O calendário tem registros nos 12 meses, de **02/01/2024 a 31/12/2024**. Isso não comprova cobertura integral das despesas estaduais. O alcance da análise são os quatro arquivos recebidos.
- O ranking agrupa por código **e** nome da unidade. Espaços externos são removidos; códigos e nomes diferentes continuam separados.
- Um mês com soma zero pode ter registros de valor zero ou valores que se compensam. A tabela mensal informa a contagem e diferencia ausência de linhas.
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

São **14 testes automatizados**, que cobrem centavos e ajustes negativos, zeros, recorte do ano, combinação de filtros, meses sem registros, ranking e reconciliação, paginação sem perda de linhas, origem verificável e IDs repetidos, consultas inválidas, SQL parametrizado, exportações e proteção contra fórmulas, rotas/erros e recuperação gzip sem sobrescrita ou base parcial. Os testes usam uma base pequena temporária; não modificam a base entregue.

Na base real, o total do painel, a soma de todas as unidades do ranking e a soma dos 12 meses foram conciliados em **1.033.709.885.862 centavos**. A preparação também realiza `PRAGMA integrity_check`. A interface foi conferida no navegador com a base real.

## Limites e próximos passos

Esta versão tem uma tela, um ano e uma base estática. Não oferece autenticação, comparação com 2025, atualização automática, busca por favorecido ou detecção de irregularidades. Não foi testada para acesso público ou grande quantidade de usuários simultâneos. A exportação integral de mais de 500 mil registros é maior e pode demorar; para uma demonstração rápida, filtre uma unidade ou mês antes de baixá-la.

Evolução proposta: importar novas cargas com verificação de cobertura, ampliar os filtros, validar a experiência com usuários, medir desempenho e preparar hospedagem adequada. A escolha de manter o recorte pequeno favorece uma demonstração funcional e auditável.
