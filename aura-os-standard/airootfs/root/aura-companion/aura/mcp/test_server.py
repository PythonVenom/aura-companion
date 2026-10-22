import sys
import json

def send_response(response):
    print(json.dumps(response), flush=True)

def main():
    for line in sys.stdin:
        try:
            req = json.loads(line)
            method = req.get("method")
            req_id = req.get("id")

            if method == "initialize":
                send_response({
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {"name": "test-server", "version": "1.0"}}
                })
            elif method == "tools/list":
                send_response({
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {"tools": [{"name": "echo", "description": "Повторяет текст", "inputSchema": {"type": "object", "properties": {"text": {"type": "string"}}}}]}
                })
            elif method == "tools/call":
                params = req.get("params", {})
                if params.get("name") == "echo":
                    text = params.get("arguments", {}).get("text", "")
                    send_response({"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": f"Эхо: {text}"}]}})
                else:
                    send_response({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Tool not found"}})
            else:
                send_response({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}})
        except Exception as e:
            pass

if __name__ == "__main__":
    main()
