from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
import asyncio
app=FastAPI()
@app.post('/mcp/execute')
async def exec(data:dict): return JSONResponse({"status":"ok","agent":data.get("agent"),"payload":data})
@app.websocket('/ws/{topic}')
async def ws(websocket:WebSocket,topic:str):
    await websocket.accept()
    while True:
        await asyncio.sleep(4)
        await websocket.send_json({"topic":topic,"confidence":0.8,"timestamp":"heartbeat"})
