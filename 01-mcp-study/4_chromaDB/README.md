# MCP Client with ChromaDB Integration

## 🧩 1. Contexto e Propósito

### Problema Resolvido
Este projeto implementa um cliente MCP (Model Control Protocol) com integração ao ChromaDB para armazenamento vetorial local, permitindo busca semântica em documentos e execução de ferramentas remotas através de uma interface de chat interativa.

### Propósito do Código
O código serve como uma ponte entre modelos de linguagem e ferramentas externas, fornecendo:
- Gerenciamento de conexões com múltiplos servidores MCP
- Armazenamento e recuperação vetorial de documentos
- Interface de linha de comando interativa
- Integração com o modelo Gemini para processamento de linguagem natural

### Casos de Uso
- Automação de tarefas através de ferramentas remotas
- Chatbots com acesso a múltiplas funcionalidades
- Aplicações de busca semântica em documentos
- Prototipagem rápida de assistentes de IA

## 🔍 2. Análise do Código

### Estrutura Principal
```python
class MCPClient:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.sessions: Dict[str, ClientSession] = {}
        self.tool_map = {}
        self.llm = GeminiClient()
        self.vector_store = ChromaVectorStore()
```

**Perguntas Reflexivas:**
- Por que usar `AsyncExitStack`?
  - Gerencia corretamente o ciclo de vida de recursos assíncronos
- Como o `tool_map` é estruturado?
  - Mapeia nomes de ferramentas para suas sessões e metadados

### Gerenciamento de Conexões
```python
async def connect_all_servers(self, server_params_map: Dict[str, StdioServerParameters]):
    for name, params in server_params_map.items():
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(params))
        read, write = stdio_transport
        session = await self.exit_stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        self.sessions[name] = session
```
**Análise:**
- Conexão assíncrona com múltiplos servidores
- Gerenciamento de recursos com context managers
- Tratamento de erros robusto

## 🧠 3. Análise Conceitual

### Princípios de Design
- **Separação de Responsabilidades**: Clientes, servidores e armazenamento são bem definidos
- **Extensibilidade**: Fácil adição de novos servidores e ferramentas
- **Assincronia**: Uso eficiente de recursos com operações assíncronas

### Complexidade
- Conexão com servidores: O(n) onde n é o número de servidores
- Busca vetorial: O(log n) para buscas eficientes
- Processamento de comandos: O(1) para comandos diretos

### Efeitos Colaterais
- Dependência de servidores MCP externos
- Armazenamento local de vetores
- Consumo de recursos para embeddings

## 🧪 4. Testabilidade e Segurança

### Casos de Teste
**Positivos:**
- Conexão com servidores
- Execução de ferramentas
- Busca semântica
- Adição/remoção de documentos

**Negativos:**
- Servidores indisponíveis
- Entradas malformadas
- Falhas de permissão
- Espaço em disco insuficiente

### Segurança
- Gerenciamento seguro de conexões
- Isolamento de processos
- Validação de entradas
- Tratamento de erros

## 🧰 5. Possíveis Melhorias

### Robustez
1. Timeout para operações de rede
2. Retry com backoff exponencial
3. Monitoramento de saúde dos servidores

### Performance
1. Cache de embeddings
2. Batch processing para documentos
3. Otimização de índices vetoriais

### Funcionalidades
1. Suporte a mais backends de vetorização
2. Interface web
3. Autenticação e autorização
4. Métricas e logging detalhados

## 🧑‍🎓 6. Conclusão

### Aprendizados
- Arquitetura de sistemas distribuídos
- Processamento assíncrono em Python
- Armazenamento e busca vetorial
- Integração de modelos de linguagem

### Boas Práticas
1. Gerenciamento adequado de recursos
2. Tratamento de erros abrangente
3. Documentação clara de APIs
4. Testes abrangentes

### Desafio
Como você implementaria um sistema de cache distribuído para os embeddings, considerando:
- Consistência entre múltiplas instâncias
- Invalidação eficiente
- Balanceamento de carga

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
- `!add <id> <conteúdo>`: Adiciona um documento ao ChromaDB
- `search <consulta>`: Busca documentos relevantes
- `list-tools`: Lista ferramentas disponíveis
- `quit`: Encerra a aplicação

## 📝 Licença
MIT