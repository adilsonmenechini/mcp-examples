# Bonus Auth - Sistema de Autenticação JWT com Flask

Um sistema de autenticação seguro implementado com Flask, JWT (JSON Web Tokens) e SQLite. Este projeto demonstra um fluxo completo de autenticação, incluindo registro de usuários, login e proteção de rotas.

## 🚀 Funcionalidades

- ✅ Registro de novos usuários
- ✅ Autenticação com JWT
- ✅ Rotas protegidas
- ✅ Armazenamento seguro de senhas com bcrypt
- ✅ Integração com MCP (Microservice Communication Protocol)

## 🛠️ Pré-requisitos

- Python 3.10 ou superior
- `uv` (gerenciador de pacotes Python)
- Git (opcional)

## 🚀 Instalação

1. Clone o repositório:
   ```bash
   git clone <url-do-repositorio>
   cd bonus_auth
   ```

2. Crie um ambiente virtual e ative-o:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # ou
   .\.venv\Scripts\activate  # Windows
   ```

3. Instale as dependências:
   ```bash
   uv pip install -e .
   ```

4. Configure as variáveis de ambiente:
   ```bash
   cp .env-examples .env
   ```
   Edite o arquivo `.env` e adicione sua chave secreta JWT:
   ```
   JWT_SECRET_KEY=sua_chave_secreta_aqui
   ```

## 🚦 Como Usar

### Iniciando o Servidor de Autenticação

```bash
uv run auth/main.py
```

O servidor estará disponível em `http://127.0.0.1:5000`

### Endpoints da API

#### 1. Registrar Novo Usuário
```http
POST /register
Content-Type: application/json

{
  "username": "usuario_teste",
  "password": "senha_segura"
}
```

#### 2. Fazer Login
```http
POST /login
Content-Type: application/json

{
  "username": "usuario_teste",
  "password": "senha_segura"
}
```

#### 3. Acessar Perfil (Protegido)
```http
GET /profile
Authorization: Bearer <seu_token_jwt>
```

### Usando o Cliente MCP

O projeto inclui um cliente MCP que demonstra como se autenticar e chamar ferramentas protegidas:

```bash
uv run client/client.py
```

## 🔒 Segurança

- Todas as senhas são armazenadas com hash bcrypt
- Tokens JWT com expiração de 1 hora
- Rotas protegidas exigem autenticação
- Chave secreta armazenada em variáveis de ambiente

## 🛠️ Estrutura do Projeto

```
bonus_auth/
├── auth/
│   └── main.py          # Servidor de autenticação
├── client/
│   └── client.py        # Cliente MCP de exemplo
├── tools/
│   └── print.py         # Ferramenta de exemplo protegida
├── .env                 # Configurações de ambiente
├── .env-examples        # Exemplo de configuração
├── pyproject.toml       # Dependências do projeto
└── README.md            # Este arquivo
```
