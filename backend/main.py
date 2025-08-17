from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json
import uvicorn

app = FastAPI()

PASSWORD = "1234"   # change this to your own password
distance = 0
active_connections = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            # ✅ Password check request
            if msg.get("action") == "check":
                if msg.get("password") == PASSWORD:
                    await websocket.send_text(json.dumps({"status": "ok"}))
                else:
                    await websocket.send_text(json.dumps({"error": "Invalid password"}))
                continue

            # ✅ Increase / Decrease request
            if msg.get("password") != PASSWORD:
                await websocket.send_text(json.dumps({"error": "Invalid password"}))
                continue

            global distance
            if msg.get("action") == "increase":
                if distance<90:
                    distance += 1
            elif msg.get("action") == "decrease":
                if distance>0:
                    distance -= 1

            # Broadcast new distance to all clients
            for conn in active_connections:
                await conn.send_text(json.dumps({"distance": distance}))

    except WebSocketDisconnect:
        active_connections.remove(websocket)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
