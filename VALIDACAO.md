# Verificação da entrega

Conferência executada em 03/10/2026 com os quatro arquivos de 2024 fornecidos na atividade.

- 505.950 registros importados e 117 unidades gestoras.
- Total líquido de ValorPago: 1.033.709.885.862 centavos, equivalente a R$ 10.337.098.858,62.
- Soma do ranking completo e soma dos 12 meses iguais ao total da base.
- 156.177 valores positivos, 339.887 zeros e 9.886 valores negativos preservados.
- Zero duplicatas completas, IDs de origem repetidos, datas inválidas ou valores monetários inválidos na carga recebida.
- Campo Orgao vazio nas 505.950 linhas. As consultas usam código e nome de UnidadeGestora.
- Integridade SQLite verificada. Recuperação da base compactada gera arquivo com o mesmo hash da base preparada.
- 14 testes automatizados aprovados: cálculos, filtros, paginação, rastreabilidade, exportação, erros e recuperação gzip.
- Consulta Fundo Estadual de Saúde (440901), dezembro: 7.790 registros e R$ 185.199.026,38, conferida na interface e na base.
- Consulta Polícia Penal (460113), janeiro: zero registros e estado vazio, sem confundir ausência com uma soma de zero.
- Registros de origem conferidos diretamente nos CSVs, com arquivo, linha, ID e ValorPago.
- Amostra interna de 10.000 IDs reproduzida com semente 2024. São 3.126 valores positivos; IC Wilson95% de 30,36% a 32,18%, restrito à base local.
- Relatório com 8 páginas e apresentação com 8 slides, revisados visualmente.

As verificações técnicas descritas não substituem a revisão e o ensaio pelos integrantes. Os papéis na proposta são sugestões e devem refletir o que cada pessoa assumir e validar. Os nomes dos quatro integrantes ainda precisam ser preenchidos. O enunciado pede grupo de cinco a oito pessoas, portanto a turma deve confirmar a exceção para quatro.

O trabalho recebeu assistência de IA na programação, análise e redação. Nenhum arquivo original foi alterado. O conjunto local não comprova a cobertura integral das despesas do Estado.
