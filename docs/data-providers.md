# Estrategia de fontes de dados

O Sports BI deve tratar cada fornecedor como uma fonte intercambiavel. A API-Football continua sendo a fonte inicial de homologacao, mas nao deve ser confundida com uma fonte completa de scouting profissional.

## Matriz de capacidade

| Necessidade | API-Football atual | Fonte profissional recomendada | Decisao |
|---|---|---|---|
| Competicoes, temporadas, times e jogos | Sim | Qualquer fornecedor | Usar agora |
| Resultados, calendario e classificacao | Sim, conforme cobertura/ plano | Qualquer fornecedor | Usar agora |
| Eventos basicos: gols, cartoes, substituicoes, VAR | Sim, conforme cobertura | Opta ou Hudl StatsBomb | Usar agora e registrar cobertura |
| Estatisticas agregadas de partida | Sim, conforme cobertura | Opta, StatsBomb ou Genius Sports | Usar agora |
| Escalacoes e jogadores de uma partida | Disponivel em endpoints da API, conforme cobertura | Opta ou StatsBomb | Implementar no proximo ciclo |
| Estatisticas de jogador por partida/temporada | Parcial e dependente do plano/cobertura | Opta ou Hudl StatsBomb | Validar endpoint antes de calcular score |
| Pressao, passe progressivo, conducoes e zonas | Nao suficiente como contrato atual | Hudl StatsBomb, Opta | Requer fonte de eventos rica |
| Tracking dos 22 jogadores | Nao | Opta Vision ou fornecedor de tracking | Integracao futura |
| xG/xA e modelos proprietarios | Parcial, conforme endpoint/plano | StatsBomb, Opta | Nao substituir por estimativa sem origem |
| Video e workflow de scout | Nao | Hudl Wyscout | Integracao separada |
| Valor de mercado e transferencias | Nao e uma fonte licenciada confiavel no nosso desenho | Fornecedor licenciado ou base contratada | Nao raspar Transfermarkt |

## Fornecedores avaliados

### API-Football / API-Sports

Boa fonte de entrada para competicoes, temporadas, equipes, fixtures, eventos, estatisticas de partida e standings. A cobertura e dependente da competicao, temporada e plano. O sistema deve consultar a cobertura e armazenar `NULL` quando um dado nao existir.

A API atual ja possui um adaptador para:

- `/leagues`;
- `/teams`;
- `/fixtures`;
- `/fixtures/events`;
- `/fixtures/statistics`;
- `/standings`.

Ainda faltam adaptadores e jobs especificos para lineups, player statistics, transfers e injuries. Esses dados so devem alimentar features depois de validar o payload real e a cobertura por liga.

Documentacao: https://www.api-football.com/documentation-v3

### Hudl StatsBomb

A pagina oficial informa dados de evento granulares, pressao, freeze frames, mais de 3.000 eventos por partida em produtos selecionados, modelos como xG e OBV e acesso via API/JSON/CSV conforme contrato. E uma candidata forte para progressao, pressao, contexto de acao e recrutamento.

Produto: https://www.hudl.com/products/statsbomb

### Stats Perform Opta

A pagina oficial descreve dados ao vivo e historicos, metricas avancadas, tracking e Opta Vision, que captura momentos on-ball e off-ball. E candidata para escala global e tracking, mas o acesso e comercial e deve ser negociado por competicao, licenca e uso.

Produto: https://www.statsperform.com/opta/

### Hudl Wyscout

Deve ser tratado principalmente como plataforma de video e scouting, com possivel integracao de dados/API conforme produto e contrato. Nao e substituto automatico do pipeline de eventos; a licenca e o formato de entrega precisam ser confirmados comercialmente.

Produto: https://www.hudl.com/products/wyscout

### Transfermarkt

Pode ser uma referencia exploratoria para pesquisa manual, mas nao deve ser tratado como API oficial nem raspado para alimentar o produto sem permissao. Para `market_opportunity_score`, usar uma fonte licenciada ou manter o campo nulo.

## Decisao de arquitetura

Criar adaptadores por fornecedor com o mesmo contrato logico:

```text
ProviderAdapter
  -> fetch raw payload
  -> CoverageRecord
  -> normalized facts
  -> feature engine
```

O modelo normalizado nunca deve depender do nome de um fornecedor. A tabela de ingestao deve guardar `source`, `endpoint`, parametros, payload, status e data. Features e scores devem guardar `source_type`, `metric_version` e metodologia.

## Roadmap de dados

1. API-Football: validar Serie B 2024 e demais ligas acessiveis no plano.
2. API-Football: adicionar lineups, player statistics, transfers e injuries com testes de payload.
3. Criar features por 90, percentis por posicao, liga e temporada somente quando minutos e amostra existirem.
4. Criar comparabilidade e scores explicaveis a partir dessas features.
5. Fazer um piloto comercial com Hudl StatsBomb ou Opta para eventos avancados.
6. Adicionar video/Wyscout e mercado como fontes independentes.
7. So depois habilitar modelos de ML e tracking.

## Regras de confiabilidade

- Nao preencher cobertura ausente com zero.
- Nao chamar score derivado de dado original.
- Nao comparar competicoes sem verificar cobertura e amostra.
- Nao misturar metricas de fornecedores sem documentar alinhamento e definicao.
- Nao usar valor de mercado sem licenca e data de referencia.
