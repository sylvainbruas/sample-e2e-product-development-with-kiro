import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { BaseWebviewPanel, BASE_CSS, html, raw, attr, safePath, KiroChat, JsonFileWatcher } from 'openvsx-kiro';
import { Manifest, PHASE_ORDER, PHASE_DISPLAY, STEP_MAP, PhaseName, StepData, OUTPUT_DIR } from './types';

interface SpecPlanEntry {
  name: string;
  slug: string;
  featureGroups: string[];
  specPath: string;
}

export class DashboardPanel extends BaseWebviewPanel {
  constructor(
    private watcher: JsonFileWatcher<Manifest>,
    private workspaceRoot: string,
    private chat: KiroChat
  ) {
    super({ viewType: 'ideationDashboard', title: 'Ideation Dashboard' });
  }

  protected onDidCreatePanel(): void {
    this.disposables.push(this.watcher.onDidChange(() => this.update()));
  }

  protected onMessage(msg: any): void {
    switch (msg.command) {
      case 'runPhase':
        this.chat.send(`/${msg.skill}`);
        break;
      case 'sendAuto':
        this.chat.sendRaw('auto');
        break;
      case 'sendAutoflow':
        this.chat.sendRaw('autoflow');
        break;
      case 'sendAutomagic':
        this.chat.sendRaw('automagic');
        break;
      case 'openFile': {
        const fullPath = safePath(this.workspaceRoot, msg.filePath);
        if (fullPath && fs.existsSync(fullPath)) {
          vscode.commands.executeCommand('markdown.showPreview', vscode.Uri.file(fullPath));
        }
        break;
      }
      case 'openRolesDashboard':
        vscode.commands.executeCommand('ideation.openRolesDashboard');
        break;
      case 'openSpecsDashboard':
        vscode.commands.executeCommand('ideation.openSpecsDashboard');
        break;
    }
  }

  protected getBodyHtml(): string {
    const manifest = this.watcher.current;
    if (!manifest) {
      return `<div class="empty"><h2>No Design Thinking Process Found</h2>
        <button class="action-btn" onclick="runPhase('al-dt-workflow-empathize')">▶ Start Empathize</button></div>`;
    }

    const projectName = this.getProjectName() || manifest.project.name || 'Untitled Project';
    const lastUpdated = new Date(manifest.project.lastUpdated).toLocaleString();
    let totalSteps = 0;
    let completedSteps = 0;
    for (const name of PHASE_ORDER) {
      const phase = manifest.phases[name];
      const stepMap = STEP_MAP[name];
      for (const [key] of Object.entries(stepMap)) {
        totalSteps++;
        if (phase?.steps[key]?.status === 'completed') { completedSteps++; }
      }
    }
    const progressPct = totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0;

    const phasesHtml = PHASE_ORDER.map((name, idx) => {
      if (!manifest.phases[name]) { return ''; }
      const isNext = manifest.phases[name].status === 'not_started' &&
        (idx === 0 || manifest.phases[PHASE_ORDER[idx - 1]]?.status === 'completed');
      return this.renderPhase(name, manifest, isNext);
    }).join('');

    const specsOnDisk = this.getSpecsFromPlan();
    const specsHtml = specsOnDisk.length > 0
      ? `<div class="section"><h2>Specs</h2>${specsOnDisk.map(s =>
          html`<div class="spec-card"><span class="spec-name">${s.name}</span><span class="spec-features">${s.featureGroups.join(', ')}</span></div>`
        ).join('')}</div>`
      : '';

    return html`
      <div class="project-header">
        <h1>${projectName}</h1>
        <p class="meta">Last updated: ${lastUpdated}</p>
      </div>
      <div class="progress-bar-container"><div class="progress-bar" style="width:${progressPct}%"></div></div>
      <div class="progress-row">
        <span class="progress-label">${completedSteps} of ${totalSteps} steps complete (${progressPct}%)</span>
        <button class="automagic-btn" onclick="sendAutomagic()" title="Run full lifecycle autonomously">✨ Automagic</button>
      </div>
      <div class="phases">${raw(phasesHtml)}</div>
      ${raw(specsHtml)}
    `;
  }

  private renderPhase(name: PhaseName, manifest: Manifest, isNext: boolean): string {
    const phase = manifest.phases[name];
    if (!phase) { return ''; }
    const display = PHASE_DISPLAY[name];
    const stepMap = STEP_MAP[name];

    const statusIcon = phase.status === 'completed' ? '✅' : phase.status === 'in_progress' ? '🔄' : isNext ? '⏳' : '○';
    const cardClass = phase.status !== 'not_started' ? phase.status : isNext ? 'next_up' : 'not_started';

    const autoBtn = phase.status === 'in_progress'
      ? `<button class="auto-btn" onclick="sendAuto()" title="Complete current step">⚡ Auto</button>`
      : '';
    const autoflowBtn = phase.status === 'in_progress'
      ? `<button class="autoflow-btn" onclick="sendAutoflow()" title="Complete workflow autonomously">⚡ Autoflow</button>`
      : '';

    const stepsHtml = Object.entries(stepMap).map(([key, info]) => {
      const step = (phase.steps[key] as StepData | undefined) ?? { status: 'not_started' };
      return this.renderStep(info.label, step, info.file, info.specs, info.files);
    }).join('');

    return html`
      <div class="phase-card ${raw(cardClass)}">
        <div class="phase-header">
          <span class="phase-number">${display.number}</span>
          <span class="phase-label">${display.label}</span>
          <span class="phase-status">${raw(statusIcon)}</span>
          ${raw(autoBtn)}
          ${raw(autoflowBtn)}
          <button class="run-btn" onclick="runPhase('${attr(display.skill)}')" title="Invoke /${display.skill}">
            <span class="codicon">▶</span> /${display.skill}
          </button>
        </div>
        <div class="phase-body">${raw(stepsHtml)}</div>
      </div>
    `;
  }

  private renderStep(label: string, step: StepData, filePath?: string, specs?: boolean, extraFiles?: string[]): string {
    const effectiveStatus = step.status;

    const icon = effectiveStatus === 'completed' ? '✓'
      : effectiveStatus === 'user_confirmed' ? '👤'
      : effectiveStatus === 'in_progress' ? '◉' : '○';
    const cls = effectiveStatus === 'completed' ? 'completed'
      : effectiveStatus === 'user_confirmed' ? 'confirmed'
      : effectiveStatus === 'in_progress' ? 'in-progress' : 'not-started';

    let fileLink = '';
    if (specs) {
      fileLink = `<a class="file-link" href="#" onclick="openSpecsDashboard()">📋 Specs Dashboard</a>`;
    } else if (filePath) {
      fileLink = this.renderFileLink(filePath);
    }

    let extraLinks = '';
    if (extraFiles) {
      extraLinks = extraFiles.map(f => this.renderFileLink(f)).join('');
    }

    return html`<div class="step ${raw(cls)}"><span class="step-icon">${raw(icon)}</span><span class="step-label">${label}</span>${raw(fileLink)}${raw(extraLinks)}</div>`;
  }

  private renderFileLink(filePath: string): string {
    const fullPath = path.join(this.workspaceRoot, filePath);
    const isDir = fs.existsSync(fullPath) && fs.statSync(fullPath).isDirectory();
    const fileName = filePath.split('/').pop() || filePath;

    if (isDir && filePath.endsWith('roles')) {
      return `<a class="file-link" href="#" onclick="openRolesDashboard()">👥 Roles Dashboard</a>`;
    } else if (fs.existsSync(fullPath)) {
      return html`<a class="file-link" href="#" onclick="openFile('${attr(filePath)}')">${fileName}</a>`;
    } else {
      return html`<span class="file-pending">${fileName}</span>`;
    }
  }

  private getProjectName(): string {
    try {
      const configPath = path.join(this.workspaceRoot, '.al', 'config.json');
      if (fs.existsSync(configPath)) {
        const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
        return config.projectName || '';
      }
    } catch { /* ignore */ }
    return '';
  }

  private getSpecsFromPlan(): SpecPlanEntry[] {
    const planPath = path.join(this.workspaceRoot, OUTPUT_DIR, 'spec-plan.json');
    if (!fs.existsSync(planPath)) { return []; }
    try {
      const plan = JSON.parse(fs.readFileSync(planPath, 'utf-8'));
      if (!plan.specs) { return []; }
      return (plan.specs as SpecPlanEntry[]).filter(s =>
        fs.existsSync(path.join(this.workspaceRoot, s.specPath))
      );
    } catch { return []; }
  }

  protected getScriptJs(): string {
    return `
      function runPhase(skill) { vscode.postMessage({ command: 'runPhase', skill }); }
      function sendAuto() { vscode.postMessage({ command: 'sendAuto' }); }
      function sendAutoflow() { vscode.postMessage({ command: 'sendAutoflow' }); }
      function sendAutomagic() { vscode.postMessage({ command: 'sendAutomagic' }); }
      function openFile(filePath) { vscode.postMessage({ command: 'openFile', filePath }); }
      function openRolesDashboard() { vscode.postMessage({ command: 'openRolesDashboard' }); }
      function openSpecsDashboard() { vscode.postMessage({ command: 'openSpecsDashboard' }); }
    `;
  }

  protected getCss(): string {
    return BASE_CSS + DASHBOARD_CSS;
  }
}

const DASHBOARD_CSS = `
  .progress-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
  .progress-row .progress-label { font-size: 0.9em; opacity: 0.6; }
  .phases { display: flex; flex-direction: column; gap: 12px; }

  .phase-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 6px; overflow: hidden; }
  .phase-card.completed { border-left: 3px solid var(--green); }
  .phase-card.in_progress { border-left: 3px solid var(--yellow); }
  .phase-card.not_started { border-left: 3px solid var(--border); opacity: 0.4; }
  .phase-card.next_up { border-left: 3px solid var(--accent); opacity: 1; }

  .phase-header { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-bottom: 1px solid var(--border); }
  .phase-number {
    background: var(--accent); color: var(--bg); width: 24px; height: 24px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center; font-size: 0.8em; font-weight: bold; flex-shrink: 0;
  }
  .phase-label { font-weight: 600; flex: 1; }
  .phase-status { font-size: 1em; }
  .phase-body { padding: 12px 16px; }

  .auto-btn, .autoflow-btn {
    background: transparent; padding: 4px 12px;
    border-radius: 4px; cursor: pointer; font-size: 0.85em; font-family: var(--vscode-font-family);
    white-space: nowrap; display: flex; align-items: center; gap: 4px; font-weight: 600;
  }
  .auto-btn { border: 1px solid var(--yellow); color: var(--yellow); }
  .auto-btn:hover { background: var(--yellow); color: var(--bg); }
  .autoflow-btn { border: 1px solid var(--yellow); color: var(--yellow); }
  .autoflow-btn:hover { background: var(--yellow); color: var(--bg); }
  .automagic-btn {
    background: transparent; border: 1px solid var(--accent); color: var(--accent);
    padding: 4px 14px; border-radius: 4px; cursor: pointer; font-size: 0.85em;
    font-family: var(--vscode-font-family); font-weight: 600; white-space: nowrap;
  }
  .automagic-btn:hover { background: var(--accent); color: var(--bg); }

  .step.confirmed .step-icon { color: var(--accent); }

  .section { margin-top: 24px; }
  .spec-card {
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 4px;
    padding: 8px 12px; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center;
  }
  .spec-name { font-weight: 600; }
  .spec-features { font-size: 0.8em; opacity: 0.6; }
`;
