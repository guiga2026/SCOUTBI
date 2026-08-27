# Power BI

O Power BI deve consumir as views Gold do PostgreSQL, e nao a API-Football diretamente.

## Conexao

- Servidor: host da VPS ou dominio interno do PostgreSQL
- Banco: `sports_bi`
- Views principais: `vw_matches`, `vw_team_performance`, `vw_standings`
- Auditoria: `vw_data_quality`
- Catalogo de metricas: `vw_metric_definitions`
- Features temporais: `vw_player_features`
- Explicabilidade: `vw_player_score_components`
- Rankings versionados: `vw_player_scores`

Por seguranca, nao exponha a porta do PostgreSQL na internet. Prefira VPN, tunel SSH ou uma rede privada. O usuario do Power BI deve ter permissao somente de leitura.

## Modelo

`vw_matches` e a tabela central de partidas. Relacione `home_team_id` e `away_team_id` a uma copia da dimensao de times, ou use duas referencias da mesma dimensao: `dim_home_team` e `dim_away_team`. `vw_team_performance` e uma tabela agregada por competicao, temporada e time; nao deve ser relacionada como detalhe de partida.

Filtros principais:

- `competition_id`
- `season_year`
- `match_date`
- `team_name`
- `status`

Nao trate uma ausencia de estatistica como zero. Valor ausente significa que a fonte nao forneceu aquela informacao.

## Inteligencia e governanca

Cada metrica possui `metric_key`, `version`, `source_type`, `formula` e `methodology`. Os valores de `source_type` distinguem dado original, derivado e modelo. O Power BI deve exibir a versao da metrica quando comparar temporadas. Scores de potencial e oportunidade de mercado permanecem nulos ate que exista amostra longitudinal e uma fonte de valor de mercado licenciada; nao substitua nulos por zero.

Os modelos de posicao usam pesos separados para `goalkeeper`, `center_back`, `full_back`, `midfielder` e `forward`. O score so deve ser calculado quando houver features observadas para o jogador. A confianca e derivada do tamanho da amostra e deve aparecer no relatorio junto do score. A explicacao deve ser lida a partir de `vw_player_score_components`, nunca reconstruida manualmente no Power BI.

## Medidas DAX

```DAX
Jogos = COUNTROWS(vw_matches)

Jogos Encerrados =
CALCULATE([Jogos], vw_matches[status] IN {"FT", "AET", "PEN"})

Gols Marcados = SUM(vw_matches[home_goals]) + SUM(vw_matches[away_goals])

Vitorias Casa =
CALCULATE([Jogos], vw_matches[result] = "H")

Vitorias Fora =
CALCULATE([Jogos], vw_matches[result] = "A")

Empates =
CALCULATE([Jogos], vw_matches[result] = "D")

Gols por Jogo = DIVIDE([Gols Marcados], [Jogos Encerrados])

Pontos = SUM(vw_team_performance[points])

Aproveitamento =
DIVIDE([Pontos], SUM(vw_team_performance[matches]) * 3)

Clean Sheet % =
DIVIDE(SUM(vw_team_performance[clean_sheets]), SUM(vw_team_performance[matches]))
```

## Paginas recomendadas

1. Visao geral: jogos, gols, forma e competicoes.
2. Competicao: classificacao, pontos, saldo e desempenho casa/fora.
3. Equipe: jogos, gols, forma recente e clean sheets.
4. Qualidade dos dados: ultima coleta, linhas coletadas, endpoints e status HTTP.

A pagina de qualidade deve ser obrigatoria antes de qualquer conclusao analitica. Uma liga com baixa cobertura nao deve ser comparada diretamente com uma liga com cobertura completa.
