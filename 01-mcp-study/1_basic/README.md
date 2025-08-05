# MCP Basic Client-Server Example

## Índice
- [1. Visão Geral](#-1-visão-geral)
- [2. Clientes](#-2-clientes)
  - [2.1 Cliente Básico](#21-cliente-básico-1_client_basicpy)
  - [2.2 Cliente com Histórico](#22-cliente-com-histórico-2_client_historypy)
  - [2.3 Cliente com Roteamento](#23-cliente-com-roteamento-3_client_routepy)
  - [2.4 Cliente com Gemini](#24-cliente-com-gemini-4_client_geminipy)
- [3. Ferramentas](#-3-ferramentas)
  - [3.1 Calculadora](#31-calculadora-tool_calculator_serverpy)
  - [3.2 DuckDuckGo](#32-duckduckgo-tool_duckduckgopy)
- [4. Como Executar](#-4-como-executar)
- [5. Melhorias Futuras](#-5-melhorias-futuras)

## 1. Visão Geral
Este projeto demonstra diferentes implementações de clientes MCP (Model Control Protocol) que se conectam a servidores de ferramentas. Cada cliente mostra uma abordagem diferente de interação com as ferramentas disponíveis.

## 2. Clientes

### 2.1 Cliente Básico (`1_client_basic.py`)
**Objetivo**: Demonstra a conexão básica com um servidor MCP.
**Características**:
- Lista todas as ferramentas disponíveis no servidor
- Permite chamar ferramentas individualmente
- Interface de linha de comando simples
**Uso ideal**: Para testes iniciais e entendimento básico do MCP.

### 2.2 Cliente com Histórico (`2_client_history.py`)
**Objetivo**: Mantém um histórico das interações.
**Melhorias em relação ao básico**:
- Armazena o histórico das operações realizadas
- Permite visualizar o histórico durante a sessão
- Mantém o contexto das interações
**Uso ideal**: Quando é necessário rastrear as operações realizadas.

### 2.3 Cliente com Roteamento (`3_client_route.py`)
**Objetivo**: Gerencia múltiplas ferramentas de forma organizada.
**Características**:
- Roteamento inteligente para diferentes ferramentas
- Tratamento de erros aprimorado
- Interface mais amigável
**Uso ideal**: Para cenários com múltiplas ferramentas e necessidade de organização.

### 2.4 Cliente com Gemini (`4_client_gemini.py`)
**Objetivo**: Integração com a API do Google Gemini.
**Recursos avançados**:
- Processamento de linguagem natural
- Chamada automática de ferramentas baseada no contexto
- Gerenciamento de estado da conversa
**Uso ideal**: Para aplicações que requerem processamento de linguagem natural.

## 3. Ferramentas

### 3.1 Calculadora (`tool_calculator_server.py`)
**Função**: Avalia expressões matemáticas.
**Métodos**:
- `evaluate_expression(expression)`: Avalia uma expressão matemática
**Exemplo de uso**: `2 + 2 * 3` retorna `8`
**Segurança**: Usa `eval()` - não recomendado para produção

### 3.2 DuckDuckGo (`tool_duckduckgo.py`)
**Função**: Realiza buscas na web.
**Métodos**:
- `search(query)`: Busca um termo no DuckDuckGo
- `get_instant_answer(query)`: Obtém resposta direta para perguntas
**Dependências**: Requer conexão com a internet

## 4. Como Executar

1. Instale as dependências:
```bash
uv pip install -r requirements.txt
```

2. Execute o servidor desejado:
```bash
# Para o servidor de calculadora
uv run python tool_calculator_server.py

# Para o servidor DuckDuckGo
uv run python tool_duckduckgo.py
```

3. Execute o cliente desejado:
```bash
# Cliente básico
python 1_client_basic.py

# Cliente com histórico
python 2_client_history.py

# Cliente com roteamento
python 3_client_route.py

# Cliente com Gemini (requer chave de API)
python 4_client_gemini.py
```

## 5. Melhorias Futuras

### Segurança
- [ ] Substituir `eval()` por um parser matemático seguro
- [ ] Implementar autenticação
- [ ] Adicionar rate limiting

### Funcionalidades
- [ ] Interface gráfica
- [ ] Suporte a variáveis
- [ ] Histórico persistente

### Performance
- [ ] Cache de resultados
- [ ] Conexões persistentes
- [ ] Processamento em lote

## Licença
MIT