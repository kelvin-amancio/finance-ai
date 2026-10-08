-- ============================================================================
-- Agente Financeiro — Categorias extras (Financiamento e Pessoal)
-- ============================================================================
INSERT INTO categorias (nome, tipo, emoji) VALUES
  ('Financiamento', 'despesa', '💳'),  -- consórcio / financiamento de veículo
  ('Pessoal',       'despesa', '💇')   -- corte de cabelo, barbearia, salão, presentes
ON CONFLICT (nome) DO NOTHING;