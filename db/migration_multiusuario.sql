-- ============================================================================
-- Agente Financeiro — Multi-usuário + Orçamentos (limites)
-- Aplicar no banco "financeiro".
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Usuários: cada número de WhatsApp é um gestor financeiro independente.
-- O acesso é liberado por código de convite (ver tabela configuracoes).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usuarios (
  numero          TEXT PRIMARY KEY,          -- número do WhatsApp (só dígitos)
  nome            TEXT,
  ativo           BOOLEAN NOT NULL DEFAULT TRUE,
  admin           BOOLEAN NOT NULL DEFAULT FALSE,
  resumo_semanal  BOOLEAN NOT NULL DEFAULT TRUE,  -- recebe o resumo no domingo
  criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------------
-- Configurações globais do agente (ex.: código de convite)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS configuracoes (
  chave TEXT PRIMARY KEY,
  valor TEXT
);

INSERT INTO configuracoes (chave, valor) VALUES ('codigo_convite', 'FINANCAS2026')
ON CONFLICT (chave) DO NOTHING;

-- ---------------------------------------------------------------------------
-- Dono do agente (admin). TROQUE pelo SEU número de WhatsApp (só dígitos, com DDI).
-- O admin pode trocar o código de convite por comando no chat.
-- ---------------------------------------------------------------------------
INSERT INTO usuarios (numero, nome, ativo, admin)
VALUES ('5511999999999', 'Admin', TRUE, TRUE)
ON CONFLICT (numero) DO NOTHING;
