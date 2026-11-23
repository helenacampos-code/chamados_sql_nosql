
# Sistema de Gerenciamento de Chamados

Projeto acadêmico de Desenvolvimento de Sistemas.

## Objetivo

Desenvolver um sistema de gerenciamento de chamados de suporte técnico utilizando simultaneamente bancos SQL e NoSQL.

## Tecnologias utilizadas

- Python
- Flask
- SQLite
- SQLAlchemy
- MongoDB
- PyMongo
- HTML
- CSS
- Git e GitHub

## Funcionalidades

- Cadastro de chamados.
- Listagem de chamados.
- Consulta dos detalhes.
- Alteração de status.
- Registro de comentários.
- Histórico de atendimento.

## Banco SQL

O SQLite armazena os usuários, categorias e chamados.

## Banco NoSQL

O MongoDB armazena o histórico de atendimento, incluindo data, responsável, ação e observações.

## Instalação

Instale as dependências:

pip install -r requirements.txt

Inicie o MongoDB e execute:

python app.py

Acesse:

http://127.0.0.1:5000

## Versionamento

O projeto utiliza Git para acompanhar as alterações do código e GitHub para hospedar o repositório.
