import sys
import json
from duckduckgo_search import DDGS

def handle_request(req):
    method = req.get("method")
    req_id = req.get("id")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "web_search", "version": "1.0"}}}
    
    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [
            {"name": "search_news", "description": "Search for latest news articles.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}
        ]}}
    
    elif method == "tools/call":
        params = req.get("params", {})
        if params.get("name") == "search_news":
            query = params.get("arguments", {}).get("query", "").strip()
            try:
                results = DDGS().news(query, region="ru-ru", max_results=5)
                if not results:
                    return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": "Новостей не найдено."}]}}
                
                text_out = ""
                for r in results:
                    text_out += f"Заголовок: {r.get('title')}\nСсылка: {r.get('url')}\nДата: {r.get('date')}\n\n"
                
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": text_out}]}}
            except Exception as e:
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Search error: {type(e).__name__} - {e}"}], "isError": True}}
    
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            req = json.loads(line)
            resp = handle_request(req)
            print(json.dumps(resp, ensure_ascii=False), flush=True)
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}), flush=True)

if __name__ == "__main__":
    main()
