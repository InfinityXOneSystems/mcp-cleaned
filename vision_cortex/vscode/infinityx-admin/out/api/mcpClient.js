"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.mcpInvoke = mcpInvoke;
const node_fetch_1 = __importDefault(require("node-fetch"));
async function mcpInvoke(agent, action, payload) {
    const r = await (0, node_fetch_1.default)('http://localhost:8000/mcp/execute', { method: 'POST',
        headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ agent, action, payload }) });
    return await r.json();
}
//# sourceMappingURL=mcpClient.js.map