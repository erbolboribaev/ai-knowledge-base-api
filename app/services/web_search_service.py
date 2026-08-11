import logging
from tavily import TavilyClient
from app.core.config import settings

logging.basicConfig(level=logging.INFO)

_client: TavilyClient | None = None


def get_tavily_client() -> TavilyClient:
    global _client
    if _client is None:
        _client = TavilyClient(api_key=settings.tavily_api_key)
    return _client


def search_web(query: str, max_results: int = 3) -> list[dict]:
    """
    Tavily API orqali internetdan qidiradi - AI/RAG ilovalar uchun
    maxsus yaratilgan, barqaror va ishonchli qidiruv xizmati.
    """
    try:
        client = get_tavily_client()
        response = client.search(query=query, max_results=max_results)
        results = response.get("results", [])
        logging.info(f"Web search '{query}' returned {len(results)} results")
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
            }
            for r in results
        ]
    except Exception as e:
        logging.error(f"Web search error: {type(e).__name__}: {e}")
        return []
