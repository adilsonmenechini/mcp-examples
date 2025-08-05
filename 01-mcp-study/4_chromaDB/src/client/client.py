from src.chatbot.interaction import format_prompt, extract_tool_calls
from src.llm.gemini import GeminiClient
from src.vectorstore.chroma_store import ChromaVectorStore

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import asyncio
from contextlib import AsyncExitStack
from typing import Dict, Optional
import json
from datetime import datetime

# Importa funções de log
from src.utils.logger import (
    log_info, log_warning, log_error, log_debug,
    log_success, log_tool_call, log_tool_result,
    log_context_found, log_model_response
)

class MCPClient:
    def __init__(self):
        self.exit_stack = AsyncExitStack()
        self.sessions: Dict[str, ClientSession] = {}
        self.tool_map = {}
        self.llm = GeminiClient()
        self.vector_store = ChromaVectorStore()  # vetorização local
        log_info("MCPClient inicializado")

    async def connect_all_servers(self, server_params_map: Dict[str, StdioServerParameters]):
        """
        Inicializa e conecta a todos os servidores MCP.
        Registra ferramentas disponíveis em `self.tool_map`.
        """
        log_info(f"Conectando a {len(server_params_map)} servidores MCP...")
        
        for name, params in server_params_map.items():
            try:
                log_debug(f"Conectando ao servidor: {name}")
                stdio_transport = await self.exit_stack.enter_async_context(stdio_client(params))
                read, write = stdio_transport
                session = await self.exit_stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                self.sessions[name] = session

                tool_response = await session.list_tools()
                for tool in tool_response.tools:
                    self.tool_map[tool.name] = (session, {
                        "description": tool.description,
                        "input_schema": tool.inputSchema,
                        "source": name
                    })
                
                log_success(f"Conectado ao servidor: {name}")
                for tool in tool_response.tools:
                    log_info(f"  - {tool.name}: {tool.description}")
                    
            except Exception as e:
                log_error(f"Falha ao conectar ao servidor {name}: {e}", exc_info=True)
                raise

    async def chat_loop(self):
        """
        Laço interativo principal.
        Comando especial: !add <id> <conteúdo>
        """
        log_info("\n🤖 Digite sua pergunta. Digite 'quit' para sair.")
        log_info("ℹ️  Use '!add <id> <conteúdo>' para adicionar documentos à base vetorial.")

        while True:
            try:
                user_input = input("\nUser: ").strip()
                if user_input.lower() in {"quit", "exit"}:
                    log_info("Encerrando o chat...")
                    break

                if user_input.startswith("!add "):
                    log_info("🔍 Comando 'add' detectado...")
                    parts = user_input.split(" ", 2)
                    if len(parts) == 3:
                        doc_id, content = parts[1], parts[2]
                        log_info(f"📝 Tentando adicionar documento - ID: {doc_id}, Conteúdo: {content[:50]}...")
                        success = self.vector_store.add_document(doc_id, content)
                        
                        if success:
                            log_success(f"Documento '{doc_id}' adicionado ao Chroma.")
                            
                            # Verificação adicional
                            log_debug("Verificando se o documento foi salvo...")
                            results = self.vector_store.query(content, k=1)
                            if results and any(content in result for result in results):
                                log_success("Documento encontrado na busca!")
                            else:
                                log_warning("Documento não encontrado na busca. Pode haver um problema com o salvamento.")
                    else:
                        log_error("Uso correto: !add <id> <conteúdo>")
                    continue

                await self.handle_input(user_input)
                
            except KeyboardInterrupt:
                log_info("\nInterrompido pelo usuário.")
                break
                
            except Exception as e:
                log_error(f"Erro inesperado no loop de chat: {e}", exc_info=True)

    async def handle_input(self, query: str):
        """
        Processa a entrada do usuário, gera uma resposta usando o modelo de linguagem
        e executa as ferramentas necessárias.
        """
        try:
            log_info(f"Processando pergunta: {query}")
            
            # 1. Busca contexto relevante
            context_text = self._get_relevant_context(query)
            
            # 2. Prepara o prompt com as ferramentas disponíveis
            tools_description = self.describe_tools()
            log_debug(f"Ferramentas disponíveis: {', '.join(self.tool_map.keys()) or 'Nenhuma'}")
            
            # 3. Gera o prompt com o contexto
            prompt = format_prompt(
                tools_description, 
                f"Pergunta: {query}\n\nContexto:\n{context_text}"
            )
            
            # 4. Gera a resposta do modelo
            log_debug("Solicitando geração de resposta do modelo...")
            raw_response = await self.llm.generate(prompt)
            log_debug(f"Resposta bruta do modelo recebida: {raw_response[:200]}...")
            
            # 5. Processa a resposta e executa ferramentas se necessário
            final_response = await self._process_model_response(query, raw_response)
            
            # 6. Se não houve chamada de ferramenta, retorna a resposta direta
            if final_response is None:
                final_response = raw_response
                
            return final_response
            
        except Exception as e:
            error_msg = f"Erro ao processar a entrada: {e}"
            log_error(error_msg, exc_info=True)
            return error_msg
    
    def _get_relevant_context(self, query: str) -> str:
        """
        Busca contexto relevante no ChromaDB para a consulta.
        """
        try:
            log_debug(f"Buscando contexto para: {query}")
            
            # Busca por termos individuais para melhor recall
            search_terms = [term for term in query.split() if len(term) > 3][:5]
            context_chunks = []
            
            # Busca por termos individuais primeiro
            for term in search_terms:
                chunks = self.vector_store.query(term, k=1, min_similarity=0.4)
                if chunks:
                    log_debug(f"Termo '{term}' retornou {len(chunks)} chunks de contexto")
                    context_chunks.extend(chunks)
            
            # Adiciona uma busca com a query completa
            full_query_chunks = self.vector_store.query(query, k=2, min_similarity=0.3)
            if full_query_chunks:
                log_debug(f"Busca completa retornou {len(full_query_chunks)} chunks de contexto")
                context_chunks.extend(full_query_chunks)
            
            # Remove duplicatas mantendo a ordem
            seen = set()
            unique_chunks = []
            for chunk in context_chunks:
                if chunk not in seen:
                    seen.add(chunk)
                    unique_chunks.append(chunk)
            
            context_text = "\n---\n".join(unique_chunks)
            log_debug(f"Contexto final com {len(unique_chunks)} chunks únicos")
            
            return context_text
            
        except Exception as e:
            log_error(f"Erro ao buscar contexto: {e}", exc_info=True)
            return ""

    async def _process_model_response(self, query: str, raw_response: str) -> Optional[str]:
        """
        Processa a resposta do modelo, extrai chamadas de ferramentas e executa se necessário.
        Retorna a resposta final ou None se não houver chamadas de ferramentas.
        """
        # Tenta extrair chamadas de ferramenta
        tool_calls = extract_tool_calls(raw_response)
        
        # Se não encontrou chamadas no formato esperado, tenta interpretar como JSON direto
        if not tool_calls:
            log_debug("Nenhuma chamada de ferramenta detectada. Tentando interpretar como JSON direto...")
            try:
                tool_call = json.loads(raw_response)
                if isinstance(tool_call, dict) and 'name' in tool_call and 'input' in tool_call:
                    tool_calls = [tool_call]
                    log_debug(f"JSON direto detectado: {tool_call['name']}")
                else:
                    return None
            except json.JSONDecodeError:
                log_warning("A resposta não contém chamadas de ferramentas válidas.")
                return None
        
        # Processa cada chamada de ferramenta
        final_response = None
        
        for i, call in enumerate(tool_calls, 1):
            tool_name = call.get("name", "").strip()
            tool_input = call.get("input", {})
            
            log_debug(f"Processando ferramenta {i}/{len(tool_calls)}: {tool_name}")
            log_debug(f"   Entrada: {tool_input}")
            
            if not tool_name:
                log_error("Nome da ferramenta não especificado.")
                continue
                
            if tool_name not in self.tool_map:
                log_error(f"Ferramenta '{tool_name}' não está registrada.")
                log_info(f"   Ferramentas disponíveis: {', '.join(self.tool_map.keys())}")
                continue
            
            session, tool_meta = self.tool_map[tool_name]
            
            try:
                # Executa a ferramenta
                log_debug(f"   Chamando ferramenta '{tool_name}'...")
                result = await session.call_tool(tool_name, tool_input)
                
                # Processa o resultado
                if hasattr(result, "content") and hasattr(result.content, "text"):
                    tool_output = result.content.text
                elif hasattr(result, "output"):
                    tool_output = result.output
                else:
                    tool_output = str(result)
                
                log_debug(f"   Resultado: {tool_output[:500]}...")
                
                # Salva o resultado no ChromaDB
                self._save_tool_result(tool_name, tool_input, tool_output, query)
                
                # Gera uma resposta final com base no resultado
                final_prompt = f"""
Você usou a ferramenta '{tool_name}' para responder à pergunta: {query}

A ferramenta retornou: {tool_output}

Com base nisso, forneça uma resposta natural e útil ao usuário.
Seja conciso e direto ao ponto.
"""
                print("Gerando resposta final...")
                final_response = await self.llm.generate([
                    {"role": "user", "parts": [{"text": final_prompt}]}
                ])
                
                print("🤖 Resposta final:", final_response)
                
            except Exception as e:
                error_msg = f"Erro ao chamar a ferramenta '{tool_name}': {e}"
                log_error(error_msg, exc_info=True)
                final_response = f"Desculpe, ocorreu um erro: {error_msg}"
        
        return final_response
    
    def _save_tool_result(self, tool_name: str, tool_input: dict, tool_output: str, original_query: str):
        """
        Salva o resultado de uma ferramenta no ChromaDB.
        """
        try:
            # Gera um ID único baseado na ferramenta e entrada
            doc_id = f"{tool_name}_{str(tool_input)[:30]}_{hash(str(tool_output)) % 10000:04d}"
            
            # Prepara o conteúdo do documento
            doc_content = f"""
Ferramenta: {tool_name}
Consulta original: {original_query}
Entrada: {json.dumps(tool_input, ensure_ascii=False)}
Saída: {tool_output}
"""
            # Adiciona metadados para facilitar a busca
            metadata = {
                "tool": tool_name,
                "query": original_query,
                "input_summary": str(tool_input)[:100],
                "timestamp": str(datetime.now().isoformat())
            }
            
            # Salva no ChromaDB
            success = self.vector_store.add_document(
                doc_id=doc_id,
                content=doc_content,
                metadata=metadata
            )
            
            if success:
                log_debug(f"Resultado salvo no ChromaDB como: {doc_id}")
            else:
                log_warning(f"Falha ao salvar resultado no ChromaDB")
                
        except Exception as e:
            log_error(f"Erro ao salvar resultado no ChromaDB: {e}", exc_info=True)
    
    def describe_tools(self) -> str:
        """
        Gera uma string com a lista das ferramentas disponíveis e suas descrições.
        """
        description = ""
        for name, (_, meta) in self.tool_map.items():
            description += f"- {name} ({meta['source']}): {meta['description']}\n"
        return description

    async def cleanup(self):
        await self.exit_stack.aclose()