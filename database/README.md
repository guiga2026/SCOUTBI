# Banco analitico

`views/power_bi.sql` contem as views Gold para o Power BI. Execute o arquivo depois da criacao das tabelas, pelo SQL Editor do PostgreSQL ou via migration.

A pasta `migrations` e reservada para Alembic. O MVP ainda cria tabelas automaticamente no startup para facilitar a primeira instalacao; antes de producao, o fluxo deve ser migrado para `alembic upgrade head`.

Os volumes `postgres_data` e `redis_data` precisam ser persistentes no Dokploy. Nunca remova o volume do PostgreSQL durante um redeploy.
