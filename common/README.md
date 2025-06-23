# MCP Example

```markdown
# 🧠 Projeto MCP Avançado com FastMCP + Chain of Thought (CoT) + Skeleton of Thought (SoT)

Este repositório implementa uma arquitetura avançada do **Model Context Protocol (MCP)** utilizando o framework **FastMCP**, combinando raciocínio CoT/SoT, agentes especializados, roteamento, ferramentas, crítica e políticas de controle. Inclui também um **controller customizado** que orquestra os passos de planejamento, execução e revisão.

---

## 📂 Estrutura de Pastas

``` shell
mcp_project/
├── server.py                 # Entry-point com FastMCP
├── agents.yaml              # Declaração dos agentes
├── controller/              # Orquestrador com lógica CoT/SoT
│   └── chain_controller.py
├── memory/                  # Estado persistente por agente
├── router/                  # Seletores dinâmicos
├── critic/                  # Pós-validação com lógica
├── policy/                  # Controle contextual e de segurança
├── prompts/                 # Prompts para plan/execute/review
│   ├── plan.txt
│   ├── execute.txt
│   └── review.txt
├── tools/                   # Integração com Ollama, RAG etc.
├── adapters/                # Pós-processamento da saída
├── templates/               # Templates de resposta (ex: JSON)
├── requirements.txt         # Dependências Python
```

---

## 🧠 agents.yaml

Define agentes MCP com orquestração modular:

```yaml
- id: mcp-orchestrator
  name: CoT-SoT Controller
  controller: controller.chain_controller:run_chain
  prompt: prompts/plan.txt
  tool: tools.ollama_tool:ollama_tool
  adapter: adapters.json_output:json_adapter
  template: templates/reply_template.txt
  memory: memory/chain-agent.json
  router: router.selector:select_agent
  critic: critic.validate_reasoning:validate
  policy: policy.prompt_policy:apply_policy
```

---

## 🧠 Lógica do Controller (Chain of Thought + Skeleton of Thought)

### `controller/chain_controller.py`

1. **Planejamento**: cria tópicos via SoT (`plan.txt`)
2. **Execução**: expande com raciocínio passo a passo via CoT (`execute.txt`)
3. **Revisão**: aplica validação crítica (`review.txt`)

---

## 📄 Prompts

### `prompts/plan.txt`

```txt
Liste os principais tópicos a serem abordados:
- Tópico 1:
- Tópico 2:
- Tópico 3:
```

### `prompts/execute.txt`

```txt
Para cada tópico do plano, elabore com raciocínio passo a passo:
1. {plan[0]} → ...
2. {plan[1]} → ...
```

### `prompts/review.txt`

Prompt de revisão crítica para análise qualitativa da resposta gerada.

---

## 🛠 tools/ — Ferramentas externas

Exemplo: `ollama_tool.py` com modelo `gemma:3b`:

```python
def ollama_tool(input_text: str, context: dict) -> str:
    return client.generate(prompt=input_text)
```

Adicione ferramentas como:
- `duckduckgo_search`
- `bash_tool`
- `knowledge_search` (RAG)

---

## 🧠 memory/ — Contexto persistente

Exemplo:

```json
{
  "history": [
    {"user": "Oi", "agent": "Olá! Como posso ajudar?"}
  ]
}
```

---

## 🛰 router/ — Seleção de agentes

Exemplo simples:

```python
if "passo a passo" in input_text: return "cot-agent"
```

---

## 🧪 critic/ — Validação da resposta

Exemplo:

```python
if "passo" not in output:
    issues.append("Faltou raciocínio lógico")
```

---

## 🔐 policy/ — Controle de conteúdo/contexto

Exemplo:

```python
if "confidencial" in context.get("tags"): return "Redigido por segurança."
```

---

## 🧾 adapters/ — Output customizado

Transforma a resposta para JSON:

```python
return {"response": response}
```

---

## 🧱 templates/ — Modelos de resposta

Exemplo:

```txt
Resposta: {{ response }}
```

---

## 🧪 Evolução Recomendada

1. ✅ **CoT**: Prompts passo a passo
2. ✅ **SoT**: Estruturação em tópicos
3. ⚙️ **Controller MCP**: Encadeia múltiplas etapas
4. 🔁 **Chain Agents**: Agentes serializados com controle explícito
5. 🔍 **RAG**: Acesso a conhecimento externo
6. 📊 **Observabilidade**: OpenTelemetry + Prometheus
7. 🔐 **Autorização**: RBAC/context-aware policy
8. 📚 **Avaliação Automática**: `evaluator.py` + datasets

---

## 🚀 Execução Local

```bash
uv pip install -r requirements.txt
uvicorn server:app --reload
```

Ou:

```bash
mcp server --agents agents.yaml
```

---

## 📦 Requisitos

- Python 3.12+
- [`fastmcp`](https://pypi.org/project/fastmcp/)
- [`mcp-ollama`](https://github.com/emgeee/mcp-ollama)
- `uvicorn`

---

## 🔗 Recursos

- [FastMCP Server](https://mcp.so/server/fastmcp/jlowin)
- [ModelContextProtocol Docs](https://modelcontextprotocol.io)
- [Ollama Python SDK](https://github.com/ollama/ollama-python)

---
```