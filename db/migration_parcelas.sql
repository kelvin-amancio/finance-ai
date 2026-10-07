-- ============================================================================
-- Agente Financeiro — Parcelas (migração)
-- Aplicar no banco "financeiro".
-- Semântica:
--   valor         = valor da PARCELA mensal (o que entra no mês)
--   valor_total   = total da compra (parcela x parcelas)
--   parcela_atual = parcela atual (ex.: 7 em "7/12")
--   parcelas_total= nº total de parcelas (ex.: 12)
-- ============================================================================
ALTER TABLE gastos ADD COLUMN IF NOT EXISTS parcela_atual INT;
ALTER TABLE gastos ADD COLUMN IF NOT EXISTS parcelas_total INT;
ALTER TABLE gastos ADD COLUMN IF NOT EXISTS valor_total NUMERIC(12,2);

-- Recorrência (assinaturas / contas fixas) e ciclo de vida (parcelas concluídas)
ALTER TABLE gastos ADD COLUMN IF NOT EXISTS recorrente BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE gastos ADD COLUMN IF NOT EXISTS ativo BOOLEAN NOT NULL DEFAULT TRUE;