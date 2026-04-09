import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { KiroChat, JsonFileWatcher } from 'openvsx-kiro';
import { PhasesTreeProvider } from './phasesTreeProvider';
import { SpecsTreeProvider } from './specsTreeProvider';
import { RolesTreeProvider } from './rolesTreeProvider';
import { DashboardPanel } from './dashboardPanel';
import { SpecsDashboardPanel } from './specsDashboardPanel';
import { RolesDashboardPanel } from './rolesDashboardPanel';
import { PHASE_DISPLAY, PhaseName, Manifest, OUTPUT_DIR } from './types';

export function activate(context: vscode.ExtensionContext): void {
  const workspaceRoot = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
  if (!workspaceRoot) { return; }

  const chat = new KiroChat({ displayName: 'Kiro Ideation' });
  const outputRoot = path.join(workspaceRoot, OUTPUT_DIR);

  const manifestPath = path.join(outputRoot, 'manifest.json');
  const watcher = new JsonFileWatcher<Manifest>({
    filePath: manifestPath,
    workspaceRoot,
    additionalPatterns: [`${OUTPUT_DIR}/**/*`],
  });

  // Static roles: check .al (installed) first, then .al-runtime, fall back to agent-lattice dev path
  const staticRolesDir = fs.existsSync(path.join(workspaceRoot, '.al', 'modules', 'design-thinking', 'roles'))
    ? path.join(workspaceRoot, '.al', 'modules', 'design-thinking', 'roles')
    : fs.existsSync(path.join(workspaceRoot, '.al-runtime', 'modules', 'design-thinking', 'roles'))
      ? path.join(workspaceRoot, '.al-runtime', 'modules', 'design-thinking', 'roles')
      : path.join(workspaceRoot, 'agent-lattice', 'modules', 'design-thinking', 'roles');

  const phasesTree = new PhasesTreeProvider(watcher, workspaceRoot);
  const specsTree = new SpecsTreeProvider(watcher, workspaceRoot, outputRoot);
  const rolesTree = new RolesTreeProvider(watcher, workspaceRoot, staticRolesDir, outputRoot);
  const dashboard = new DashboardPanel(watcher, workspaceRoot, chat);
  const specsDashboard = new SpecsDashboardPanel(workspaceRoot, chat, outputRoot);
  const rolesDashboard = new RolesDashboardPanel(watcher, workspaceRoot, chat, rolesTree, staticRolesDir, outputRoot);

  context.subscriptions.push(
    vscode.window.registerTreeDataProvider('ideationPhases', phasesTree),
    vscode.window.registerTreeDataProvider('ideationSpecs', specsTree),
    vscode.window.registerTreeDataProvider('ideationRoles', rolesTree),

    vscode.commands.registerCommand('ideation.openDashboard', () => dashboard.show(context.extensionUri)),
    vscode.commands.registerCommand('ideation.openSpecsDashboard', () => specsDashboard.show(context.extensionUri)),
    vscode.commands.registerCommand('ideation.openRolesDashboard', () => rolesDashboard.show(context.extensionUri)),

    vscode.commands.registerCommand('ideation.runPhase', async (item: { phaseName?: PhaseName; skill?: string }) => {
      const skill = item.skill || (item.phaseName && PHASE_DISPLAY[item.phaseName]?.skill);
      if (skill) { await chat.send(`/${skill}`); }
    }),

    vscode.commands.registerCommand('ideation.openArtifact', (item: { filePath?: string }) => {
      if (item.filePath) { vscode.window.showTextDocument(vscode.Uri.file(item.filePath)); }
    }),

    vscode.commands.registerCommand('ideation.previewSpec', (item: { resourceUri?: vscode.Uri; specPath?: string }) => {
      const specDir = item.resourceUri?.fsPath ?? (item.specPath ? path.join(workspaceRoot, item.specPath) : undefined);
      if (specDir) {
        const reqPath = path.join(specDir, 'requirements.md');
        if (fs.existsSync(reqPath)) { vscode.commands.executeCommand('markdown.showPreview', vscode.Uri.file(reqPath)); }
      }
    }),

    vscode.commands.registerCommand('ideation.openSpecRaw', (item: { resourceUri?: vscode.Uri; specPath?: string }) => {
      const specDir = item.resourceUri?.fsPath ?? (item.specPath ? path.join(workspaceRoot, item.specPath) : undefined);
      if (specDir) {
        const reqPath = path.join(specDir, 'requirements.md');
        if (fs.existsSync(reqPath)) { vscode.window.showTextDocument(vscode.Uri.file(reqPath)); }
      }
    }),

    vscode.commands.registerCommand('ideation.refresh', () => {
      watcher.read();
      phasesTree.refresh();
      rolesTree.refresh();
    }),

    vscode.commands.registerCommand('ideation.sendToChat', async (message: string) => { await chat.send(message); }),
    vscode.commands.registerCommand('ideation.sendAuto', async () => { await chat.sendRaw('auto'); }),

    vscode.commands.registerCommand('ideation.generateSpecs', async () => {
      const manifest = watcher.current;
      if (!manifest || manifest.phases.prototype.status !== 'completed') {
        vscode.window.showWarningMessage('Kiro Ideation: Prototype phase must be completed before generating specs.');
        return;
      }
      await chat.send('/al-dt-generate-specs');
    }),

    vscode.commands.registerCommand('ideation.chatWithRole', async (item: { role?: { relPath: string } }) => {
      if (item?.role) { await chat.send(`/al-impersonate ${item.role.relPath}`); }
    }),

    { dispose: () => {
      watcher.dispose(); dashboard.dispose(); specsDashboard.dispose();
      rolesDashboard.dispose(); rolesTree.dispose();
    }}
  );

  watcher.init();
}

export function deactivate(): void {}
