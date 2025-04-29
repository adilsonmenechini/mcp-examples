from duckduckgo_search import ddg


class DuckDuckGoAgent:
    def search(self, query: str, max_results=5):
        results = ddg(query, max_results=max_results)
        return results or []
