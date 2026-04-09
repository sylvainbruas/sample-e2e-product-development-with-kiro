import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';
import { BaseWebviewPanel, BASE_CSS, html, raw, attr, safePath, KiroChat, JsonFileWatcher } from 'openvsx-kiro';
import { Manifest } from './types';
import { RolesTreeProvider, RoleMeta } from './rolesTreeProvider';

interface ProfileData {
  interviewInsights: string[];
  empathy: { says: string[]; thinks: string[]; does: string[]; feels: string[] };
  validatedInsights: string[];
  userFlows: { id: string; title: string; actor: string }[];
  requirements: { id: string; title: string; story: string }[];
}

export class RolesDashboardPanel extends BaseWebviewPanel {
  constructor(
    private watcher: JsonFileWatcher<Manifest>,
    private workspaceRoot: string,
    private chat: KiroChat,
    private rolesTree: RolesTreeProvider,
    private staticRolesDir: string,
    private outputRoot: string
  ) {
    super({ viewType: 'rolesDashboard', title: 'Roles & Interviews' });
  }

  protected onDidCreatePanel(): void {
    this.disposables.push(this.watcher.onDidChange(() => this.update()));
    const pat = new vscode.RelativePattern(this.workspaceRoot,
      path.relative(this.workspaceRoot, this.outputRoot) + '/roles/**');
    const w = vscode.workspace.createFileSystemWatcher(pat);
    w.onDidChange(() => this.update());
    w.onDidCreate(() => this.update());
    w.onDidDelete(() => this.update());
    this.disposables.push(w);
  }

  protected onMessage(msg: any): void {
    switch (msg.command) {
      case 'impersonate':
        this.chat.send(`/al-impersonate ${msg.rolePath}`);
        break;
      case 'interview':
        this.chat.send(`/al-dt-skill-interview ${msg.slug}`);
        break;
      case 'openFile': {
        const fullPath = safePath(this.workspaceRoot, msg.filePath);
        if (fullPath && fs.existsSync(fullPath)) {
          vscode.commands.executeCommand('markdown.showPreview', vscode.Uri.file(fullPath));
        }
        break;
      }
    }
  }

  protected getBodyHtml(): string {
    const statics = this.rolesTree.scanRoles(this.staticRolesDir, false);
    const dynamics = this.rolesTree.scanRoles(path.join(this.outputRoot, 'roles'), true);

    if (!statics.length && !dynamics.length) {
      return `<div class="empty"><h2>No Roles Found</h2>
        <p>Run <code>/al-dt-workflow-empathize</code> to create personas.</p></div>`;
    }

    let body = '';

    if (statics.length > 0) {
      body += `<h2>Team Roles</h2><div class="roles-grid">`;
      body += statics.map(r => this.renderStaticRole(r)).join('');
      body += `</div>`;
    }

    if (dynamics.length > 0) {
      body += `<h2>Synthetic Users</h2><div class="roles-list">`;
      body += dynamics.map(r => {
        const profile = this.parseProfile(r.slug);
        return this.renderDynamicRole(r, profile);
      }).join('');
      body += `</div>`;
    }

    return body;
  }

  private renderStaticRole(r: RoleMeta): string {
    return html`
      <div class="role-card static">
        <div class="role-header">
          <span class="role-icon">🛡</span>
          <span class="role-name">${r.name}</span>
          <button class="chat-btn" onclick="impersonate('${attr(r.relPath)}')" title="Chat as ${r.name}">💬</button>
        </div>
        <p class="role-desc">${r.role}</p>
        <a class="file-link" href="#" onclick="openFile('${attr(r.relPath)}')">${path.basename(r.relPath)}</a>
      </div>`;
  }

  private renderDynamicRole(r: RoleMeta, profile: ProfileData | null): string {
    const interviewHtml = r.interviews.length > 0
      ? r.interviews.map(f => {
          const rel = path.relative(this.workspaceRoot, f);
          return html`<a class="file-link" href="#" onclick="openFile('${attr(rel)}')">📄 ${path.basename(f)}</a>`;
        }).join('')
      : `<span class="dim">No interview yet</span>`;

    let profileHtml = '';
    if (profile) {
      // Empathy map
      if (profile.empathy.says.length || profile.empathy.thinks.length || profile.empathy.does.length || profile.empathy.feels.length) {
        profileHtml += `<div class="empathy-grid">`;
        profileHtml += this.renderQuadrant('Says', profile.empathy.says, '💬');
        profileHtml += this.renderQuadrant('Thinks', profile.empathy.thinks, '💭');
        profileHtml += this.renderQuadrant('Does', profile.empathy.does, '🎯');
        profileHtml += this.renderQuadrant('Feels', profile.empathy.feels, '❤️');
        profileHtml += `</div>`;
      }

      // Interview insights
      if (profile.interviewInsights.length) {
        profileHtml += `<div class="section"><h4>Interview Insights</h4>`;
        profileHtml += profile.interviewInsights.map(i => html`<p class="insight-item">• ${i}</p>`).join('');
        profileHtml += `</div>`;
      }

      // Requirements
      if (profile.requirements.length) {
        profileHtml += `<div class="section"><h4>Requirements</h4><div class="req-list">`;
        profileHtml += profile.requirements.map(r =>
          html`<div class="req-item"><span class="req-id">${r.id}</span> <span class="req-title">${r.title}</span></div>`
        ).join('');
        profileHtml += `</div></div>`;
      }

      // User flows
      if (profile.userFlows.length) {
        profileHtml += `<div class="section"><h4>User Flows</h4><div class="flow-list">`;
        profileHtml += profile.userFlows.map(f =>
          html`<div class="flow-item"><span class="flow-id">${f.id}</span> ${f.title}</div>`
        ).join('');
        profileHtml += `</div></div>`;
      }
    }

    const hasDetails = profileHtml.length > 0;

    return html`
      <div class="role-card dynamic">
        <div class="role-header">
          <span class="role-icon">👤</span>
          <div class="role-info">
            <span class="role-name">${r.name}</span>
            <span class="role-desc">${r.role}</span>
          </div>
          <button class="chat-btn" onclick="impersonate('${attr(r.relPath)}')" title="Chat as ${r.name}">💬 Chat</button>
          <button class="interview-btn" onclick="interview('${attr(r.slug)}')" title="Interview ${r.name}">🎙 Interview</button>
        </div>
        <div class="role-files">
          <a class="file-link" href="#" onclick="openFile('${attr(r.relPath)}')">📋 Role</a>
          ${raw(interviewHtml)}
        </div>
        ${raw(hasDetails ? `<details class="role-details"><summary>Details</summary>${profileHtml}</details>` : '')}
      </div>`;
  }

  private renderQuadrant(title: string, items: string[], icon: string): string {
    if (!items.length) { return ''; }
    const itemsHtml = items.map(i => html`<p class="q-item">${i}</p>`).join('');
    return html`<div class="quadrant">
      <h5>${raw(icon)} ${title}</h5>
      ${raw(itemsHtml)}
    </div>`;
  }

  /**
   * Parse enrichment sections from a dynamic role file. Structure:
   *   ## Interview Insights — numbered bold items
   *   ## Empathy Map — **Says/Thinks/Does/Feels** with bullet lists
   *   ## Validated Insights — dash-prefixed items
   *   ## User Flows — ### Flow X.X — Title with Actor line
   *   ## Requirements — **FR-X.X** As persona, I want...
   */
  private parseProfile(slug: string): ProfileData | null {
    const filePath = path.join(this.outputRoot, 'roles', `${slug}.md`);
    if (!fs.existsSync(filePath)) { return null; }
    const content = fs.readFileSync(filePath, 'utf-8');

    const data: ProfileData = {
      interviewInsights: [],
      empathy: { says: [], thinks: [], does: [], feels: [] },
      validatedInsights: [],
      userFlows: [],
      requirements: [],
    };

    // Split into ## sections
    const sections = content.split(/^## /m).slice(1);

    for (const section of sections) {
      const firstLine = section.split('\n')[0].trim();
      const body = section.slice(section.indexOf('\n') + 1);

      if (firstLine.startsWith('Interview Insights')) {
        // Numbered: "1. **Bold text** — rest"
        const matches = body.matchAll(/^\d+\.\s+\*\*(.+?)\*\*/gm);
        for (const m of matches) { data.interviewInsights.push(m[1]); }
      } else if (firstLine.startsWith('Empathy Map')) {
        let currentQ: keyof typeof data.empathy | null = null;
        for (const line of body.split('\n')) {
          if (line.startsWith('**Says**')) { currentQ = 'says'; continue; }
          if (line.startsWith('**Thinks**')) { currentQ = 'thinks'; continue; }
          if (line.startsWith('**Does**')) { currentQ = 'does'; continue; }
          if (line.startsWith('**Feels**')) { currentQ = 'feels'; continue; }
          if (currentQ && line.startsWith('- ')) {
            data.empathy[currentQ].push(line.slice(2).trim().replace(/^[""\u201C]|[""\u201D]$/g, ''));
          }
        }
      } else if (firstLine.startsWith('Validated Insights')) {
        for (const line of body.split('\n')) {
          if (line.startsWith('- ')) {
            data.validatedInsights.push(line.slice(2).trim());
          }
        }
      } else if (firstLine.startsWith('User Flows')) {
        const flowMatches = body.matchAll(/^### (Flow [\d.]+)[\s:—–-]+(.+)/gm);
        for (const m of flowMatches) {
          // Find the Personas line after this heading
          const afterHeading = body.slice(body.indexOf(m[0]) + m[0].length);
          const personaMatch = afterHeading.match(/\*\*Personas?:\*\*\s*(.+)/);
          data.userFlows.push({ id: m[1], title: m[2].trim(), actor: personaMatch ? personaMatch[1].trim() : '' });
        }
      } else if (firstLine.startsWith('Requirements')) {
        // Formats:
        //   ### FR-X.X: Title  or  ### FR-X.X — Title
        //   **FR-X.X** As persona, I want {goal}, so that {reason}.
        //   **FR-X.X: Title**
        const reqMatches = body.matchAll(/(?:^###+ (FR-[\w.]+)[\s:—–-]+(.+)|^\*\*(FR-[\w.]+?)(?:[\s:—–-]+(.+?))?\*\*\s*(.*))/gm);
        for (const m of reqMatches) {
          const id = m[1] || m[3];
          const title = m[1] ? (m[2] || '').trim()
            : (m[4] || m[5] || '').trim();
          data.requirements.push({ id, title, story: '' });
        }
      }
    }

    return data;
  }

  protected getScriptJs(): string {
    return `
      function impersonate(rolePath) { vscode.postMessage({ command: 'impersonate', rolePath }); }
      function interview(slug) { vscode.postMessage({ command: 'interview', slug }); }
      function openFile(filePath) { vscode.postMessage({ command: 'openFile', filePath }); }
    `;
  }

  protected getCss(): string {
    return BASE_CSS + ROLES_CSS;
  }
}

const ROLES_CSS = `
  .roles-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; margin-bottom: 24px; }
  .roles-list { display: flex; flex-direction: column; gap: 16px; }

  .role-card { background: var(--card-bg); border: 1px solid var(--border); border-radius: 6px; padding: 16px; }
  .role-card.static { border-left: 3px solid var(--green); }
  .role-card.dynamic { border-left: 3px solid var(--accent); }

  .role-header { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
  .role-icon { font-size: 1.3em; flex-shrink: 0; }
  .role-info { flex: 1; display: flex; flex-direction: column; }
  .role-name { font-weight: 600; font-size: 1.05em; }
  .role-desc { font-size: 0.85em; opacity: 0.7; margin-top: 2px; }

  .chat-btn, .interview-btn {
    background: transparent; border: 1px solid var(--border); color: var(--accent); padding: 4px 10px;
    border-radius: 4px; cursor: pointer; font-size: 0.8em; font-family: var(--vscode-font-family);
    white-space: nowrap; flex-shrink: 0;
  }
  .chat-btn:hover { background: var(--accent); color: var(--bg); }
  .interview-btn { color: var(--yellow); border-color: var(--yellow); }
  .interview-btn:hover { background: var(--yellow); color: var(--bg); }

  .role-files { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px; }
  .dim { color: var(--dim); font-size: 0.85em; }

  .empathy-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin: 12px 0; }
  .quadrant { background: var(--bg); border: 1px solid var(--border); border-radius: 4px; padding: 10px; }
  .quadrant h5 { font-size: 0.85em; margin-bottom: 6px; opacity: 0.8; }
  .q-item { font-size: 0.8em; padding: 2px 0; line-height: 1.4; opacity: 0.9; }

  .section { margin-top: 10px; }
  .section h4 { font-size: 0.9em; margin-bottom: 6px; opacity: 0.8; }
  .insight-item { font-size: 0.8em; line-height: 1.4; padding: 2px 0; }

  .req-list, .flow-list { display: flex; flex-direction: column; gap: 4px; }
  .req-item, .flow-item { font-size: 0.8em; padding: 4px 8px; background: var(--bg); border: 1px solid var(--border); border-radius: 3px; }
  .req-id, .flow-id { font-weight: 600; color: var(--accent); margin-right: 4px; }
  .req-title { opacity: 0.9; }

  .role-details { margin-top: 8px; }
  .role-details summary {
    cursor: pointer; font-size: 0.85em; font-weight: 600; opacity: 0.7;
    padding: 4px 0; user-select: none; list-style: none;
  }
  .role-details summary::before { content: '▸ '; }
  .role-details[open] summary::before { content: '▾ '; }
  .role-details summary::-webkit-details-marker { display: none; }
  .role-details summary:hover { opacity: 1; }
`;
