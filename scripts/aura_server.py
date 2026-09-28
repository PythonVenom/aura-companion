"""TCP сервер для Blender (ADR-037).

Запуск в Blender:
    blender --python scripts/aura_server.py

Слушает 127.0.0.1:9876, исполняет whitelisted команды.
"""
import json
import socket
import threading
from typing import Any

HOST = "127.0.0.1"
PORT = 9876


def handle_scene_info(params: dict) -> dict:
    import bpy
    return {
        "scene": bpy.context.scene.name,
        "objects": len(bpy.data.objects),
        "materials": len(bpy.data.materials),
    }


def handle_list_objects(params: dict) -> dict:
    import bpy
    return {"objects": [obj.name for obj in bpy.data.objects]}


def handle_list_materials(params: dict) -> dict:
    import bpy
    return {"materials": [m.name for m in bpy.data.materials]}


def handle_export_fbx(params: dict) -> dict:
    import bpy
    path = params.get("path", "/tmp/aura_export.fbx")
    bpy.ops.export_scene.fbx(filepath=path)
    return {"exported": path}


def handle_render(params: dict) -> dict:
    import bpy
    path = params.get("path", "/tmp/aura_render.png")
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return {"rendered": path}


HANDLERS = {
    "scene_info": handle_scene_info,
    "list_objects": handle_list_objects,
    "list_materials": handle_list_materials,
    "export_fbx": handle_export_fbx,
    "render": handle_render,
}


def dispatch(payload: dict) -> dict:
    cmd = payload.get("cmd", "")
    if cmd not in HANDLERS:
        return {"ok": False, "error": f"unknown cmd: {cmd}"}
    try:
        result = HANDLERS[cmd](payload.get("params", {}))
        return {"ok": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def client_thread(conn: socket.socket) -> None:
    with conn:
        while True:
            try:
                data = conn.recv(65536)
                if not data:
                    break
                payload = json.loads(data.decode("utf-8"))
                response = dispatch(payload)
                conn.sendall(json.dumps(response).encode("utf-8"))
            except Exception:
                break


def serve_forever() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(1)
        print(f"[Aura] Blender server listening on {HOST}:{PORT}")
        while True:
            conn, _ = srv.accept()
            threading.Thread(target=client_thread, args=(conn,), daemon=True).start()


if __name__ == "__main__":
    try:
        serve_forever()
    except KeyboardInterrupt:
        print("[Aura] Остановлен")
