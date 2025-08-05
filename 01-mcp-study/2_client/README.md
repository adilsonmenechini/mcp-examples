# MCP Client with Tool Integration

## 🧩 1. Contexto e Propósito

### Problema Resolvido
Este projeto implementa um cliente MCP (Model Control Protocol) que permite a integração de ferramentas externas com modelos de linguagem, criando uma interface de chat interativa que pode executar diversas funcionalidades através de comandos naturais.

### Propósito do Código
O código serve como uma camada intermediária entre o usuário e ferramentas remotas, fornecendo:
- Gerenciamento de conexões com servidores MCP
- Descoberta e invocação dinâmica de ferramentas
- Processamento de linguagem natural para interpretação de comandos
- Interface de linha de comando interativa

### Casos de Uso
- Automação de tarefas através de comandos em linguagem natural
- Chatbots com capacidade de executar ações externas
- Prototipagem rápida de assistentes de IA com funcionalidades estendidas
- Integração de múltiplos serviços em uma única interface

## 🔍 2. Análise do Código

### Estrutura Principal
```python
class MCPClient:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.sessions: Dict[str, ClientSession] = {}
        self.tool_map = {}
        self.llm = GeminiClient()
```

**Perguntas Reflexivas:**
- Por que usar `AsyncExitStack`?
  - Gerencia corretamente o ciclo de vida de recursos assíncronos
- Como o `tool_map` é estruturado?
  - Mapeia nomes de ferramentas para suas sessões e metadados

### Gerenciamento de Ferramentas
```python
async def connect_all_servers(self, server_params_map: Dict[str, StdioServerParameters]):
    for name, params in server_params_map.items():
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(params))
        read, write = stdio_transport
        session = await self.exit_stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self.sessions[name] = session
        # ... registro de ferramentas ...
```
**Análise:**
- Conexão assíncrona com múltiplos servidores
- Descoberta automática de ferramentas
- Tratamento de erros implícito

## 🧠 3. Análise Conceitual

### Princípios de Design
- **Baixo Acoplamento**: Ferramentas são descobertas dinamicamente
- **Alta Coesão**: Cada método tem uma responsabilidade clara
- **Extensibilidade**: Fácil adição de novas ferramentas
- **Assincronia**: Uso eficiente de recursos

### Complexidade
- Conexão com servidores: O(n) onde n é o número de servidores
- Processamento de comandos: O(1) para comandos diretos
- Busca de ferramentas: O(1) com dicionário

### Efeitos Colaterais
- Dependência de servidores MCP externos
- Chamadas de rede assíncronas
- Consumo de tokens da API do Gemini

## 🧪 4. Testabilidade e Segurança

### Casos de Teste
**Positivos:**
- Coneexão com servidores
- Execução de ferramentas
- Processamento de comandos complexos
- Tratamento de erros

**Negativos:**
- Servidores indisponíveis
- Ferramentas inexistentes
- Entradas malformadas
- Falhas de permissão

### Segurança
- Validação de entradas
- Isolamento de processos
- Gerenciamento seguro de conexões
- Tratamento de erros

## 🧰 5. Possíveis Melhorias

### Robustez
1. Timeout para operações de rede
2. Retry com backoff exponencial
3. Cache de respostas
4. Melhor tratamento de erros

### Performance
1. Processamento em lote
2. Cache de ferramentas frequentes
3. Otimização de prompts

### Funcionalidades
1. Suporte a histórico de conversa
2. Autocompletar comandos
3. Documentação integrada
4. Interface web

## 🧑‍🎓 6. Conclusão

### Aprendizados
- Integração de modelos de linguagem com ferramentas
- Programação assíncrona em Python
- Design de interfaces de linha de comando
- Gerenciamento de recursos

### Boas Práticas
1. Documentação clara de APIs
2. Tratamento de erros abrangente
3. Separação de preocupações
4. Testes abrangentes

### Desafio
Como você implementaria um sistema de permissões granulares para controle de acesso às ferramentas, considerando:
- Diferentes níveis de usuário
- Registro de auditoria
- Cache de permissões
- Performance em sistemas distribuídos

## 🚀 Como Executar

1. Instale as dependências:
```bash
uv pip install -r requirements.txt
```

2. Configure os servidores em `servers_config.json`:
```json
{
  "mcpServers": {
    "servidor1": {
      "command": "python",
      "args": ["caminho/para/servidor.py"],
      "env": {}
    }
  }
}
```

3. Execute a aplicação:
```bash
python main.py
```

## 📝 Comandos Disponíveis
- Digite comandos em linguagem natural
- O sistema irá detectar e executar as ferramentas apropriadas
- Digite 'quit' ou 'exit' para sair

## 📝 Licença
MIT