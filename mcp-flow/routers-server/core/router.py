from fastmcp import Client
import yaml
from typing import Dict, Any, Optional, List
import asyncio
from datetime import datetime, timedelta


class Cache:
    def __init__(self, ttl: int, max_size: int):
        self.ttl = ttl
        self.max_size = max_size
        self.cache = {}
        self.timestamps = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self.cache:
            if datetime.now() - self.timestamps[key] < timedelta(seconds=self.ttl):
                return self.cache[key]
            else:
                del self.cache[key]
                del self.timestamps[key]
        return None

    def set(self, key: str, value: Any) -> None:
        if len(self.cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            del self.cache[oldest_key]
            del self.timestamps[oldest_key]

        self.cache[key] = value
        self.timestamps[key] = datetime.now()


class Router:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.clients = self._initialize_clients()
        if self.config["router"]["cache"]["enabled"]:
            self.cache = Cache(
                ttl=self.config["router"]["cache"]["ttl"],
                max_size=self.config["router"]["cache"]["max_size"],
            )
        else:
            self.cache = None

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        except Exception as e:
            raise Exception(f"Failed to load config: {str(e)}")

    def _initialize_clients(self) -> Dict[str, Client]:
        clients = {}
        for server_name, server_config in self.config["router"]["servers"].items():
            if server_config["enabled"]:
                clients[server_name] = Client(server_config["path"])
        return clients

    async def _retry_operation(
        self, operation, max_attempts: int = None, delay: int = None
    ):
        if max_attempts is None:
            max_attempts = self.config["router"]["retry"]["max_attempts"]
        if delay is None:
            delay = self.config["router"]["retry"]["delay"]

        for attempt in range(max_attempts):
            try:
                return await operation()
            except Exception:
                if attempt == max_attempts - 1:
                    raise
                await asyncio.sleep(delay)

    async def _query_neo4j(self, cypher_query: str, params: Dict = None) -> Dict:
        async with self.clients["neo4j"] as neo4j:
            return await self._retry_operation(
                lambda: neo4j.call_tool(
                    "query", {"cypher_query": cypher_query, "params": params or {}}
                )
            )

    async def _generate_embeddings(self, text: str) -> List[float]:
        async with self.clients["ollama"] as ollama:
            response = await self._retry_operation(
                lambda: ollama.call_tool(
                    "generate",
                    {
                        "prompt": text,
                        "model_name": self.config["router"]["integration"]["ollama"][
                            "default_model"
                        ],
                    },
                )
            )
            # Convert text to vector using FAISS
            async with self.clients["faiss"] as faiss:
                vector_response = await self._retry_operation(
                    lambda: faiss.call_tool(
                        "text_to_vector", {"text": response["text"]}
                    )
                )
                return vector_response["vector"]

    async def handle_problem(self, problem_description: str) -> Dict:
        try:
            # Check cache first
            if self.cache:
                cached_result = self.cache.get(problem_description)
                if cached_result:
                    return {"source": "cache", "data": cached_result}

            # 1. Check Neo4j for existing solution
            neo4j_result = await self._query_neo4j(
                f"""
                MATCH (p:{self.config["router"]["integration"]["neo4j"]["problem_label"]}
                      {{description: $desc}})-[r:{self.config["router"]["integration"]["neo4j"]["relationship_type"]}]->
                      (s:{self.config["router"]["integration"]["neo4j"]["solution_label"]})
                RETURN p, s
                """,
                {"desc": problem_description},
            )

            if neo4j_result.get("result"):
                result = {"source": "neo4j", "data": neo4j_result["result"]}
                if self.cache:
                    self.cache.set(problem_description, result)
                return result

            # 2. Generate embeddings and search similar problems
            problem_vector = await self._generate_embeddings(problem_description)

            async with self.clients["faiss"] as faiss:
                similar_problems = await self._retry_operation(
                    lambda: faiss.call_tool(
                        "search",
                        {
                            "query_vector": problem_vector,
                            "k": 5,
                            "threshold": self.config["router"]["integration"]["faiss"][
                                "similarity_threshold"
                            ],
                        },
                    )
                )

                if similar_problems.get("results"):
                    # Get solutions for similar problems from Neo4j
                    similar_ids = [r["id"] for r in similar_problems["results"]]
                    similar_solutions = await self._query_neo4j(
                        f"""
                        MATCH (p:{self.config["router"]["integration"]["neo4j"]["problem_label"]})
                        WHERE p.id IN $ids
                        MATCH (p)-[r:{self.config["router"]["integration"]["neo4j"]["relationship_type"]}]->
                              (s:{self.config["router"]["integration"]["neo4j"]["solution_label"]})
                        RETURN p, s
                        """,
                        {"ids": similar_ids},
                    )
                    if similar_solutions.get("result"):
                        result = {
                            "source": "similar_problems",
                            "data": similar_solutions["result"],
                        }
                        if self.cache:
                            self.cache.set(problem_description, result)
                        return result

            # 3. Search external sources
            async with self.clients["duckduckgo"] as search:
                search_resp = await self._retry_operation(
                    lambda: search.call_tool(
                        "search",
                        {
                            "query": problem_description,
                            "max_results": self.config["router"]["integration"][
                                "duckduckgo"
                            ]["max_results"],
                        },
                    )
                )
                results = search_resp.get("results", [])

            # 4. Generate solution using Ollama
            text_to_summarize = "\n".join(
                [r.get("body", r.get("snippet", "")) for r in results]
            )
            prompt = f"Analyze and provide a solution for: {problem_description}\n\nContext:\n{text_to_summarize}"

            async with self.clients["ollama"] as ollama:
                ollama_resp = await self._retry_operation(
                    lambda: ollama.call_tool(
                        "generate",
                        {
                            "prompt": prompt,
                            "model_name": self.config["router"]["integration"][
                                "ollama"
                            ]["default_model"],
                            "max_tokens": self.config["router"]["integration"][
                                "ollama"
                            ]["max_tokens"],
                            "temperature": self.config["router"]["integration"][
                                "ollama"
                            ]["temperature"],
                        },
                    )
                )
                solution = ollama_resp.get("text", "")

            # 5. Store new problem and solution
            await self._query_neo4j(
                f"""
                CREATE (p:{self.config["router"]["integration"]["neo4j"]["problem_label"]}
                       {{description: $desc, vector: $vector}})
                CREATE (s:{self.config["router"]["integration"]["neo4j"]["solution_label"]}
                       {{text: $solution}})
                CREATE (p)-[r:{self.config["router"]["integration"]["neo4j"]["relationship_type"]}]->(s)
                RETURN p, s
                """,
                {
                    "desc": problem_description,
                    "vector": problem_vector,
                    "solution": solution,
                },
            )

            # Store vector in FAISS
            async with self.clients["faiss"] as faiss:
                await self._retry_operation(
                    lambda: faiss.call_tool(
                        "add_vectors",
                        {"vectors": [problem_vector], "ids": [problem_description]},
                    )
                )

            result = {"source": "new_solution", "solution": solution}
            if self.cache:
                self.cache.set(problem_description, result)
            return result

        except Exception as e:
            return {"error": f"Failed to handle problem: {str(e)}"}

    async def close(self) -> None:
        for client in self.clients.values():
            await client.close()
