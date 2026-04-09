import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { BaseWebviewPanel, BASE_CSS, html, raw, attr, safePath, KiroChat } from 'openvsx-kiro';

interface SpecPlan {
  schema: string;
  createdAt: string;
  specs: SpecPlanEntry[];
}

interface SpecPlanEntry {
  name: string;
  slug: string;
  description: string;
  featureGroups: string[];
  requirementIds: string[];
  priority: string;
  status: string;
  specPath: string;
}

interface SpecFileStatus {
  requirements: boolean;
  design: boolean;
  tasks: boolean;
}

export class SpecsDashboardPanel extends BaseWebviewPanel {
  private watchers: vscode.Disposable[] = [];

  constructor(
    private workspaceRoot: string,
    private chat: KiroChat,
    private outputRoot: string
  ) {
    super({ viewType: 'specsDashboard', title: 'Specs Dashboard' });
  }

  protected onDidCreatePanel(): void {
    const planWatcher = vscode.workspace.createFileSystemWatcher(
      path.join(this.outputRoot, 'spec-plan.json')
    );
    planWatcher.onDidChange(() => this.update());
    planWatcher.onDidCreate(() => this.update());
    this.disposables.push(planWatcher);

    const specsPattern = new vscode.RelativePattern(this.workspaceRoot, '.kiro/specs/**/*');
    const specsWatcher = vscode.workspace.createFileSystemWatcher(specsPattern);
    specsWatcher.onDidChange(() => this.update());
    specsWatcher.onDidCreate(() => this.update());
    specsWatcher.onDidDelete(() => this.update());
    this.disposables.push(specsWatcher);
  }

  protected onMessage(msg: any): void {
    switch (msg.command) {
      case 'generateSpecs':
        this.chat.send('/al-dt-generate-specs');
        break;
      case 'createSpec':
        this.chat.send(`/al-dt-workflow-create-spec ${msg.slug}`);
        break;
      case 'previewFile': {
        const fullPath = safePath(this.workspaceRoot, msg.filePath);
        if (fullPath && fs.existsSync(fullPath)) {
          vscode.commands.executeCommand('markdown.showPreview', vscode.Uri.file(fullPath));
        }
        break;
      }
      case 'editFile': {
        const fullPath = safePath(this.workspaceRoot, msg.filePath);
        if (fullPath && fs.existsSync(fullPath)) {
          vscode.commands.executeCommand('vscode.open', vscode.Uri.file(fullPath));
        }
        break;
      }
    }
  }

  protected getBodyHtml(): string {
    const plan = this.readPlan();
    if (!plan) {
      return `<div class="empty">
        <h2>No Spec Plan Found</h2>
        <p>Run <code>/al-dt-generate-specs</code> to create a spec breakdown from your requirements.</p>
        <button class="action-btn" onclick="generateSpecs()">▶ Generate Specs</button>
      </div>`;
    }

    const totalSpecs = plan.specs?.length ?? 0;
    const createdSpecs = (plan.specs ?? []).filter(s => {
      const files = this.getFileStatus(s.specPath);
      return files.requirements && files.design && files.tasks;
    }).length;

    const specsHtml = (plan.specs ?? []).map(spec => {
      const files = this.getFileStatus(spec.specPath);
      const fileIndicators = [
        { name: 'requirements', exists: files.requirements, path: spec.specPath + 'requirements.md' },
        { name: 'design', exists: files.design, path: spec.specPath + 'design.md' },
        { name: 'tasks', exists: files.tasks, path: spec.specPath + 'tasks.md' },
      ];

      const filesHtml = fileIndicators.map(f =>
        f.exists
          ? html`<span class="file-group">` +
            html`<a class="file-pill created" href="#" onclick="previewFile('${attr(f.path)}')">${f.name}</a>` +
            html`<a class="file-edit-btn enabled" href="#" onclick="editFile('${attr(f.path)}')" title="Edit">✎</a>` +
            `</span>`
          : html`<span class="file-group">` +
            html`<span class="file-pill pending">${f.name}</span>` +
            `<span class="file-edit-btn disabled" title="Not created yet">✎</span>` +
            `</span>`
      ).join('');

      const allFilesExist = files.requirements && files.design && files.tasks;
      const anyFileExists = files.requirements || files.design || files.tasks;

      let statusHtml: string;
      if (allFilesExist) {
        statusHtml = `<span class="status-badge completed">Complete</span>`;
      } else if (anyFileExists) {
        statusHtml = `<span class="status-badge in-progress">In Progress</span>`;
      } else {
        statusHtml = html`<button class="create-btn" onclick="createSpec('${attr(spec.slug)}')">▶ Create Spec</button>`;
      }

      return html`
        <div class="spec-card">
          <div class="spec-header">
            <span class="spec-name">${spec.name}</span>
            <span class="priority priority-${raw(spec.priority.toLowerCase())}">${spec.priority}</span>
            ${raw(statusHtml)}
          </div>
          <p class="spec-desc">${spec.description}</p>
          <div class="spec-meta">
            <div class="file-pills">${raw(filesHtml)}</div>
            <span class="req-ids">${spec.requirementIds.join(', ')}</span>
          </div>
        </div>
      `;
    }).join('');

    return html`
      <div class="header">
        <h1>Specs</h1>
        <div class="header-meta">
          <span class="progress-text">${createdSpecs} of ${totalSpecs} specs complete</span>
          <button class="action-btn small" onclick="generateSpecs()">↻ Regenerate Plan</button>
        </div>
      </div>
      <div class="specs-list">${raw(specsHtml)}</div>
    `;
  }

  private readPlan(): SpecPlan | null {
    const planPath = path.join(this.outputRoot, 'spec-plan.json');
    if (!fs.existsSync(planPath)) { return null; }
    try {
      return JSON.parse(fs.readFileSync(planPath, 'utf-8'));
    } catch { return null; }
  }

  private getFileStatus(specPath: string): SpecFileStatus {
    const base = path.join(this.workspaceRoot, specPath);
    return {
      requirements: fs.existsSync(path.join(base, 'requirements.md')),
      design: fs.existsSync(path.join(base, 'design.md')),
      tasks: fs.existsSync(path.join(base, 'tasks.md')),
    };
  }

  protected getScriptJs(): string {
    return `
      function generateSpecs() { vscode.postMessage({ command: 'generateSpecs' }); }
      function createSpec(slug) { vscode.postMessage({ command: 'createSpec', slug }); }
      function previewFile(filePath) { vscode.postMessage({ command: 'previewFile', filePath }); }
      function editFile(filePath) { vscode.postMessage({ command: 'editFile', filePath }); }
    `;
  }

  protected getCss(): string {
    return BASE_CSS + SPECS_CSS;
  }
}

const SPECS_CSS = `
  .header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }
  .header-meta { display: flex; align-items: center; gap: 12px; }
  .progress-text { font-size: 0.9em; opacity: 0.6; }

  .specs-list { display: flex; flex-direction: column; gap: 12px; }

  .spec-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 6px; padding: 16px; }
  .spec-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
  .spec-name { font-weight: 600; font-size: 1.05em; flex: 1; }

  .priority { font-size: 0.75em; font-weight: 700; padding: 2px 8px; border-radius: 3px; }
  .priority-p0 { background: #d32f2f; color: #fff; }
  .priority-p1 { background: var(--yellow); color: var(--bg); }
  .priority-p2 { background: var(--dim); color: var(--bg); }

  .create-btn {
    background: transparent; border: 1px solid var(--accent); color: var(--accent); padding: 4px 12px;
    border-radius: 4px; cursor: pointer; font-size: 0.85em; font-family: var(--vscode-font-family);
    white-space: nowrap;
  }
  .create-btn:hover { background: var(--accent); color: var(--bg); }

  .status-badge { font-size: 0.8em; padding: 3px 10px; border-radius: 3px; font-weight: 600; }
  .status-badge.completed { background: var(--green); color: var(--bg); }
  .status-badge.in-progress { background: var(--yellow); color: var(--bg); }

  .spec-desc { font-size: 0.9em; opacity: 0.8; margin-bottom: 10px; line-height: 1.4; }

  .spec-meta { display: flex; align-items: center; justify-content: space-between; }
  .file-pills { display: flex; gap: 8px; }
  .file-pill {
    font-size: 0.8em; padding: 2px 8px; border-radius: 3px 0 0 3px; font-family: var(--vscode-font-family);
  }
  .file-pill.created { background: var(--green); color: var(--bg); cursor: pointer; text-decoration: none; }
  .file-pill.created:hover { opacity: 0.85; }
  .file-pill.pending { background: none; color: var(--dim); border: 1px solid var(--border); border-right: none; }

  .file-group { display: inline-flex; align-items: stretch; }
  .file-edit-btn {
    font-size: 0.8em; width: 24px; display: inline-flex; align-items: center; justify-content: center;
    border-radius: 0 3px 3px 0; text-decoration: none; font-family: var(--vscode-font-family);
  }
  .file-edit-btn.enabled {
    background: var(--green); color: var(--bg); cursor: pointer;
    border-left: 1px solid rgba(0,0,0,0.15); opacity: 0.8;
  }
  .file-edit-btn.enabled:hover { opacity: 1; }
  .file-edit-btn.disabled {
    background: none; color: var(--dim); border: 1px solid var(--border); border-left: none;
    cursor: default; opacity: 0.4;
  }

  .req-ids { font-size: 0.8em; opacity: 0.5; font-family: var(--vscode-font-family); }
`;
