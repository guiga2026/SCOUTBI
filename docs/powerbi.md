# Power BI

O Power BI deve consumir as views Gold do PostgreSQL, e nao a API-Football diretamente.

## Conexao

- Servidor: host da VPS ou dominio interno do PostgreSQL
- Banco: `sports_bi`
- Views principais: `vw_matches`, `vw_team_performance`, `vw_standings`
- Auditoria: `vw_data_quality`

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
