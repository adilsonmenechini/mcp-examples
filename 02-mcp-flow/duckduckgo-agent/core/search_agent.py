from duckduckgo_search import DDGS


class DuckDuckGoAgent:
    def search(self, query: str, max_results=5):
        ddgs = DDGS()
        results = ddgs.text(query, max_results=max_results)
        return results
