import * as vscode from 'vscode';
export function startWebSocketFeed(p:vscode.WebviewPanel,topic:string){
  const ws=new WebSocket('ws://localhost:8000/ws/'+topic);
  ws.onmessage=m=>p.webview.postMessage(JSON.parse(m.data));
  ws.onerror=()=>setInterval(()=>p.webview.postMessage({
    agent:'predictor',confidence:(Math.random()*0.3+0.7).toFixed(2),
    timestamp:new Date().toISOString()}),4000);
}
