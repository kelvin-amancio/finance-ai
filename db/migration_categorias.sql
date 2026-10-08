-- ============================================================================
-- Agente Financeiro — Categorias extras (Financiamento, Consórcio e Pessoal)
-- ============================================================================
INSERT INTO categorias (nome, tipo, emoji) VALUES
  ('Financiamento', 'despesa', '💳'),  -- financiamento / prestação de veículo
  ('Consórcio',     'despesa', '🤝'),  -- consórcio (não é financiamento)
  ('Pessoal',       'despesa', '💇')   -- corte de cabelo, barbearia, salão, presentes
ON CONFLICT (nome) DO NOTHING;