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
exports.VisionCortexPanel = void 0;
const vscode = __importStar(require("vscode"));
const websocket_1 = require("../websocket");
class VisionCortexPanel {
    static show(uri) {
        const p = vscode.window.createWebviewPanel("visionCortex", "🧠 Vision Cortex", vscode.ViewColumn.One, { enableScripts: true });
        p.webview.html = this.html();
        (0, websocket_1.startWebSocketFeed)(p, "visionCortex");
    }
    static html() {
        return `
<html>
  <body style="background:#001014;color:#fff;font-family:system-ui;padding:20px;">
    <h2>Vision Cortex</h2>
    <pre id="out">Awaiting feed...</pre>
    <script>
      const vscode = acquireVsCodeApi();
      window.addEventListener("message", e=>{
        document.getElementById("out").innerText = JSON.stringify(e.data,null,2);
      });
    </script>
  </body>
</html>`;
    }
}
exports.VisionCortexPanel = VisionCortexPanel;
//# sourceMappingURL=visionCortexPanel.js.map