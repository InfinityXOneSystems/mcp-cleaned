import * as vscode from 'vscode';
import { VisionCortexPanel } from './panels/visionCortexPanel';
import { AutoBuilderPanel } from './panels/autoBuilderPanel';
import { DebateArenaPanel } from './panels/debateArenaPanel';

export function activate(ctx: vscode.ExtensionContext) {
  const cmds: [string, () => void][] = [
    ['infinityx.open.visionCortex', () => VisionCortexPanel.show(ctx.extensionUri)],
    ['infinityx.open.autoBuilder',  () => AutoBuilderPanel.show(ctx.extensionUri)],
    ['infinityx.open.debateArena',  () => DebateArenaPanel.show(ctx.extensionUri)],
  ];
  for (const [id, fn] of cmds) {
    ctx.subscriptions.push(vscode.commands.registerCommand(id, fn));
  }
}
