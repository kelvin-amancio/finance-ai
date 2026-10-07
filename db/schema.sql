-- ============================================================================
-- Agente Financeiro WhatsApp — schema base
-- Banco: financeiro (PostgreSQL)
-- ============================================================================

CREATE TABLE IF NOT EXISTS categorias (
  id       SERIAL PRIMARY KEY,
  nome     TEXT NOT NULL UNIQUE,
  tipo     TEXT NOT NULL DEFAULT 'despesa',   -- 'despesa' | 'receita'
  emoji    TEXT NOT NULL DEFAULT '💸',
  ativo    BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS gastos (
  id        BIGSERIAL PRIMARY KEY,
  numero    TEXT NOT NULL,                       -- número do WhatsApp (somente dígitos)
  descricao TEXT NOT NULL,
  valor     NUMERIC(12,2) NOT NULL CHECK (valor >= 0),
  categoria TEXT NOT NULL DEFAULT 'Outros',
  tipo      TEXT NOT NULL DEFAULT 'despesa',     -- 'despesa' | 'receita'
  data      DATE NOT NULL DEFAULT CURRENT_DATE,
  criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_gastos_numero_data ON gastos (numero, data DESC);
CREATE INDEX IF NOT EXISTS idx_gastos_categoria   ON gastos (numero, categoria);

CREATE TABLE IF NOT EXISTS orcamentos (
  id             SERIAL PRIMARY KEY,
  numero         TEXT NOT NULL,
  categoria      TEXT NOT NULL,
  limite_mensal  NUMERIC(12,2) NOT NULL CHECK (limite_mensal > 0),
  criado_em      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (numero, categoria)
);

-- ---------------------------------------------------------------------------
-- Seed de categorias (estilo Pierre Finance, PT-BR)
-- ---------------------------------------------------------------------------
INSERT INTO categorias (nome, tipo, emoji) VALUES
  ('Alimentação',  'despesa', '🍔'),
  ('Mercado',      'despesa', '🛒'),
  ('Transporte',   'despesa', '🚗'),
  ('Moradia',      'despesa', '🏠'),
  ('Contas fixas', 'despesa', '📄'),
  ('Saúde',        'despesa', '💊'),
  ('Educação',     'despesa', '📚'),
  ('Lazer',        'despesa', '🎉'),
  ('Compras',      'despesa', '🛍️'),
  ('Assinaturas',  'despesa', '📺'),
  ('Viagem',       'despesa', '✈️'),
  ('Pets',         'despesa', '🐾'),
  ('Outros',       'despesa', '📦'),
  ('Salário',      'receita', '💰'),
  ('Extra',        'receita', '🤑'),
  ('Investimento', 'receita', '📈')
ON CONFLICT (nome) DO NOTHING;
