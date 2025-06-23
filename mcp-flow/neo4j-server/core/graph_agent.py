from neo4j import GraphDatabase, Session
from neo4j.exceptions import ServiceUnavailable
import yaml
from typing import List, Dict
import time


class GraphAgent:
    def __init__(self, config_path: str = "config.yaml", max_retries: int = 3):
        with open(config_path, "r") as f:
            cfg = yaml.safe_load(f)
        neo4j_cfg = cfg["neo4j"]
        self.max_retries = max_retries
        self.driver = GraphDatabase.driver(
            neo4j_cfg["uri"],
            auth=(neo4j_cfg["user"], neo4j_cfg["password"]),
            max_connection_lifetime=3600,
        )

    def _execute_with_retry(self, operation):
        retries = 0
        while retries < self.max_retries:
            try:
                return operation()
            except ServiceUnavailable:
                retries += 1
                if retries == self.max_retries:
                    raise
                time.sleep(1)

    def query(self, cypher_query: str, params: Dict = None) -> List[Dict]:
        def run_query():
            with self.driver.session() as session:
                result = session.run(cypher_query, params or {})
                return [record.data() for record in result]

        return self._execute_with_retry(run_query)

    def write_transaction(self, cypher_query: str, params: Dict = None) -> None:
        def run_transaction(tx: Session):
            tx.run(cypher_query, params or {})

        with self.driver.session() as session:
            session.write_transaction(run_transaction)

    def close(self) -> None:
        self.driver.close()
