# Sports BI

MVP de uma plataforma de dados historicos de futebol brasileiro, usando API-Football como fonte externa, PostgreSQL como historico e Redis preparado para cache.

## Executar com Docker

1. Copie `.env.example` para `.env` e preencha `API_FOOTBALL_KEY`.
2. Suba os servicos: `docker compose up --build -d`.
3. Abra o Swagger em `http://localhost:8000/docs`.
4. Execute o primeiro sync: `docker compose exec api python pipiline.py`.
5. Consulte `GET /api/v1/competitions`.

A chave e enviada no header oficial `x-apisports-key`; ela nunca deve ser commitada, retornada pela API ou colocada no frontend. A API externa pode ter cobertura diferente por competicao e temporada; o ETL deve preservar valores ausentes como `NULL`.

## Deploy com Dokploy

1. Crie uma aplicacao do tipo `Compose` no Dokploy e conecte o repositorio Git.
2. Use a raiz do repositorio como `Compose Path` e mantenha o arquivo `docker-compose.yml` selecionado.
3. Cadastre em `Environment` as variaveis `API_FOOTBALL_KEY`, `DATABASE_URL`, `REDIS_URL` e `CORS_ORIGINS`. Nao coloque a chave no Git.
4. Faça o deploy e configure o dominio apontando para o servico `api`, na porta interna `8000`.
5. Ative HTTPS pelo proxy do Dokploy e valide `https://api.seudominio.com/api/v1/health`.

O Compose foi configurado para receber as variaveis do ambiente do Dokploy; nao e necessario criar um arquivo `.env` na VPS. Neste ambiente, PostgreSQL e Redis devem ser servicos internos ja provisionados no Dokploy. Para executar o primeiro sync, use o terminal do container `api` e rode `python pipiline.py`.

O comando de inicializacao do servico `api` deve ser `uvicorn sports_bi.app.main:app --host 0.0.0.0 --port 8000`. Nao use somente `python3`, pois esse processo termina imediatamente e gera `502 Bad Gateway`. O `Dockerfile` tambem define esse comando por padrao.

### Exportar todos os dados para XLSX

Depois de executar o sync e aplicar as views, abra o terminal do container `api` e execute:

```bash
python export_xlsx.py --output /tmp/sports_bi_export.xlsx
```

O arquivo inclui todas as tabelas e views do schema `public`, incluindo dados brutos e views Gold. Para copiar o arquivo da API para a VPS, execute no terminal da VPS:

```bash
docker cp $(docker ps -q --filter "name=sqlbi-compose-8zyus6" | head -1):/tmp/sports_bi_export.xlsx /root/sports_bi_export.xlsx
```

Depois baixe `/root/sports_bi_export.xlsx` por SFTP. O exportador nao inclui senhas nem variaveis de ambiente.

### Deploy automatico pelo GitHub Actions

O workflow em `.github/workflows/deploy-dokploy.yml` dispara um novo deploy a cada push na branch `main`. No repositorio GitHub, cadastre em `Settings > Secrets and variables > Actions`:

```text
DOKPLOY_URL=https://dokploy.seudominio.com
DOKPLOY_API_KEY=chave-gerada-no-Dokploy
DOKPLOY_COMPOSE_ID=id-do-servico-compose
```

O `DOKPLOY_URL` deve ser a URL base do Dokploy, sem `/api` e sem barra final. O `DOKPLOY_COMPOSE_ID` e o ID do servico Compose no Dokploy, nao o ID do projeto. Esses valores sao secrets do GitHub e nao devem ser adicionados ao `.env`, ao codigo ou aos logs.

## Escopo atual

O MVP cobre health, competicoes, times, jogos e sync idempotente de competicoes brasileiras. A base esta pronta para temporadas, eventos, estatisticas, standings, migrations Alembic, jobs agendados e views dimensionais para Power BI.