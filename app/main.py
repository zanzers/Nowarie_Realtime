from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI(
    title="Nowarie Realtime",
    description="A reusable real-time backend for messaging and future multiplayer applications.",
    version="0.1.0",
)

@app.get("/health")
async def health_check():
    return {
        "status":"Healthy",
        "service": "nowarie-realtime",
        "version":"0.1.0"
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    print("Websocket endpoint reached")

    await websocket.accept()
    print("Websocket connection accepted.")

    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"Server received: {message}")

    except WebSocketDisconnect:
        print("Client disconnected.")