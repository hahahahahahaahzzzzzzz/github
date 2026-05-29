import uvicorn

if __name__ == "__main__":
    print("[INIT] Initializing RepoLeak Watcher X Backend Services...")
    print("[REST] Server running on: http://localhost:8000")
    print("[WS] WebSocket Endpoint running on: ws://localhost:8000/ws")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
