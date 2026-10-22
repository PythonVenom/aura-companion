import sys
import json
import sqlite3

DB_PATH = sys.argv[1] if len(sys.argv) > 1 else ":memory:"

def handle_request(req):
    method = req.get("method")
    req_id = req.get("id")

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "sqlite", "version": "1.0"}}}
    
    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": [
            {"name": "query", "description": "Execute a read-only SQL query against the database. NEVER include the database name or file name in the SQL.", "inputSchema": {"type": "object", "properties": {"sql": {"type": "string"}}, "required": ["sql"]}},
            {"name": "get_schema", "description": "Get the schema (tables and columns) of the database", "inputSchema": {"type": "object", "properties": {}}}
        ]}}
    
    elif method == "tools/call":
        params = req.get("params", {})
        if params.get("name") == "get_schema":
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [r[0] for r in cursor.fetchall()]
                schema_info = {}
                for t in tables:
                    cursor.execute(f"PRAGMA table_info({t})")
                    schema_info[t] = [c[1] for c in cursor.fetchall()]
                conn.close()
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(schema_info, ensure_ascii=False)}]}}
            except Exception as e:
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": str(e)}], "isError": True}}
                
        if params.get("name") == "query":
            sql = params.get("arguments", {}).get("sql")
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute(sql)
                rows = cursor.fetchall()
                cols = [d[0] for d in cursor.description] if cursor.description else []
                result = [dict(zip(cols, row)) for row in rows]
                conn.close()
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}}
            except Exception as e:
                return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": str(e)}], "isError": True}}
    
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            req = json.loads(line)
            resp = handle_request(req)
            print(json.dumps(resp), flush=True)
        except Exception as e:
            print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": str(e)}}), flush=True)

if __name__ == "__main__":
    main()
