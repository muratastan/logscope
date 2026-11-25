-- Run after Docker/PostgreSQL setup via psql -d logscope -f check_postgres.sql.
SELECT count(*) AS expected_27_tables
  FROM information_schema.tables
 WHERE table_schema='logscope' AND table_type='BASE TABLE';
SELECT count(*) AS expected_41_foreign_keys
  FROM pg_constraint AS c
  JOIN pg_namespace AS n ON n.oid=c.connamespace
 WHERE n.nspname='logscope' AND c.contype='f';
SELECT tablename,indexname FROM pg_indexes WHERE schemaname='logscope' ORDER BY tablename,indexname;
