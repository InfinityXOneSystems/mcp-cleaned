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
exports.activate = activate;
const vscode = __importStar(require("vscode"));
const visionCortexPanel_1 = require("./panels/visionCortexPanel");
const autoBuilderPanel_1 = require("./panels/autoBuilderPanel");
const debateArenaPanel_1 = require("./panels/debateArenaPanel");
function activate(ctx) {
    const cmds = [
        ['infinityx.open.visionCortex', () => visionCortexPanel_1.VisionCortexPanel.show(ctx.extensionUri)],
        ['infinityx.open.autoBuilder', () => autoBuilderPanel_1.AutoBuilderPanel.show(ctx.extensionUri)],
        ['infinityx.open.debateArena', () => debateArenaPanel_1.DebateArenaPanel.show(ctx.extensionUri)]
    ];
    cmds.forEach(([id, fn]) => ctx.subscriptions.push(vscode.commands.registerCommand(id, fn)));
}
//# sourceMappingURL=extension.js.map