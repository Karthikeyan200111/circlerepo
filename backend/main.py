from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json, uvicorn, uuid

app = FastAPI()

# sessions store distance per session
sessions = {}  # {session_id: {"distance": int, "connections": [WebSocket]}}

@app.get("/")
async def read_root():
    return {"message": "🚀 Welcome! Use /ws?session_id=xxx to connect."}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            # ✅ Create a new session
            if msg.get("action") == "create":
                session_id = str(uuid.uuid4())[:8]  # short ID
                sessions[session_id] = {"distance": 60, "connections": [websocket]}  # start at 60
                await websocket.send_text(json.dumps({"session_id": session_id, "distance": 60}))
                continue

            # ✅ Join existing session
            if msg.get("action") == "join":
                session_id = msg.get("session_id")
                if session_id not in sessions:
                    await websocket.send_text(json.dumps({"error": "Invalid session ID"}))
                    continue
                sessions[session_id]["connections"].append(websocket)
                await websocket.send_text(json.dumps({"status": "ok"}))
                await websocket.send_text(json.dumps({"status": "joined", "distance": sessions[session_id]["distance"]}))
                continue

            # ✅ Must provide session_id for control actions
            session_id = msg.get("session_id")
            if session_id not in sessions:
                await websocket.send_text(json.dumps({"error": "Invalid session ID"}))
                continue

            # ✅ Increase/Decrease with bounds 60–90
            if msg.get("action") == "increase":
                if sessions[session_id]["distance"] < 120:
                    sessions[session_id]["distance"] += 1
            elif msg.get("action") == "decrease":
                if sessions[session_id]["distance"] > -15:
                    sessions[session_id]["distance"] -= 1

            # ✅ Broadcast updated distance only in this session
            for conn in sessions[session_id]["connections"]:
                await conn.send_text(json.dumps({"distance": sessions[session_id]["distance"]}))

    except WebSocketDisconnect:
        # remove disconnected client from all sessions
        for sid in list(sessions.keys()):
            if websocket in sessions[sid]["connections"]:
                sessions[sid]["connections"].remove(websocket)
                if not sessions[sid]["connections"]:
                    del sessions[sid]  # cleanup empty session
