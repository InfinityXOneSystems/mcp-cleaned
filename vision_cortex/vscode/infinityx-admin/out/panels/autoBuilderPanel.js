"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.AutoBuilderPanel = void 0;
const vscode = __importStar(require("vscode"));
const mcpClient_1 = require("../api/mcpClient");
class AutoBuilderPanel {
    static show(uri) {
        const p = vscode.window.createWebviewPanel("autoBuilder", "⚙️ Auto Builder", vscode.ViewColumn.One, { enableScripts: true });
        p.webview.html = `
<html>
  <body style="background:#0a0a0a;color:#0f0;font-family:system-ui;padding:20px;">
    <h2>Auto Builder</h2>
    <button id="run">Run DRY_RUN</button>
    <pre id="out"></pre>
    <script>
      const vscode = acquireVsCodeApi();
      document.getElementById("run").onclick = ()=>vscode.postMessage({cmd:"run"});
      window.addEventListener("message", e=>{
        document.getElementById("out").innerText = JSON.stringify(e.data,null,2);
      });
    </script>
  </body>
</html>`;
        p.webview.onDidReceiveMessage(async (m) => {
            if (m.cmd === "run") {
                const res = await (0, mcpClient_1.mcpInvoke)("builder.integrator", "build_cycle", { mode: "DRY_RUN" });
                p.webview.postMessage(res);
            }
        });
    }
}
exports.AutoBuilderPanel = AutoBuilderPanel;
//# sourceMappingURL=autoBuilderPanel.js.map