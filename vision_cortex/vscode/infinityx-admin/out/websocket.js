"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.startWebSocketFeed = startWebSocketFeed;
function startWebSocketFeed(p, topic) {
    const ws = new WebSocket('ws://localhost:8000/ws/' + topic);
    ws.onmessage = m => p.webview.postMessage(JSON.parse(m.data));
    ws.onerror = () => setInterval(() => p.webview.postMessage({
        agent: 'predictor', confidence: (Math.random() * 0.3 + 0.7).toFixed(2),
        timestamp: new Date().toISOString()
    }), 4000);
}
//# sourceMappingURL=websocket.js.map