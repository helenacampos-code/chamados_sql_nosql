
-- BANCO DE DADOS: SISTEMA DE SUPORTE TÉCNICO

-- TABELA DE USUÁRIOS
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL
);

-- TABELA DE CATEGORIAS
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE
);

-- TABELA DE CHAMADOS
CREATE TABLE IF NOT EXISTS chamados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    categoria_id INTEGER NOT NULL,
    equipamento TEXT NOT NULL,
    descricao TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Aberto',
    criado_em TEXT NOT NULL,

    FOREIGN KEY (usuario_id)
        REFERENCES usuarios(id),

    FOREIGN KEY (categoria_id)
        REFERENCES categorias(id)
);

-- CATEGORIAS INICIAIS
INSERT OR IGNORE INTO categorias (nome)
VALUES ('Hardware');

INSERT OR IGNORE INTO categorias (nome)
VALUES ('Software');

INSERT OR IGNORE INTO categorias (nome)
VALUES ('Rede/Internet');

INSERT OR IGNORE INTO categorias (nome)
VALUES ('Outro');
