import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { BaseTreeProvider, MessageItem, JsonFileWatcher } from 'openvsx-kiro';
import { Manifest } from './types';

type TreeItem = RoleCategoryItem | RoleItem | InterviewItem | MessageItem;

export interface RoleMeta {
  name: string;
  slug: string;
  role: string;
  filePath: string;
  relPath: string;
  isDynamic: boolean;
  interviews: string[];
}

export class RolesTreeProvider extends BaseTreeProvider<TreeItem> {
  private watchers: vscode.Disposable[] = [];

  constructor(
    private watcher: JsonFileWatcher<Manifest>,
    private workspaceRoot: string,
    private staticRolesDir: string,
    private outputRoot: string
  ) {
    super();
    watcher.onDidChange(() => this._onDidChangeTreeData.fire());

    const rolesPattern = new vscode.RelativePattern(workspaceRoot, path.relative(workspaceRoot, path.join(outputRoot, 'roles', '**')));
    const rolesWatcher = vscode.workspace.createFileSystemWatcher(rolesPattern);
    rolesWatcher.onDidChange(() => this._onDidChangeTreeData.fire());
    rolesWatcher.onDidCreate(() => this._onDidChangeTreeData.fire());
    rolesWatcher.onDidDelete(() => this._onDidChangeTreeData.fire());
    this.watchers.push(rolesWatcher);

    const interviewPattern = new vscode.RelativePattern(workspaceRoot, path.relative(workspaceRoot, path.join(outputRoot, '01-empathize', 'interview-*.md')));
    const interviewWatcher = vscode.workspace.createFileSystemWatcher(interviewPattern);
    interviewWatcher.onDidChange(() => this._onDidChangeTreeData.fire());
    interviewWatcher.onDidCreate(() => this._onDidChangeTreeData.fire());
    interviewWatcher.onDidDelete(() => this._onDidChangeTreeData.fire());
    this.watchers.push(interviewWatcher);
  }

  protected getRootChildren(): TreeItem[] {
    const statics = this.scanRoles(this.staticRolesDir, false);
    const dynamics = this.scanRoles(path.join(this.outputRoot, 'roles'), true);

    const items: TreeItem[] = [];
    if (statics.length > 0) { items.push(new RoleCategoryItem('Team Roles', statics.length, 'organization')); }
    if (dynamics.length > 0) { items.push(new RoleCategoryItem('Synthetic Users', dynamics.length, 'account')); }
    if (items.length === 0) { return [new MessageItem('No roles found. Run /al-dt-workflow-empathize to create personas.')]; }
    return items;
  }

  protected getChildrenOf(element: TreeItem): TreeItem[] {
    if (element instanceof RoleCategoryItem) {
      const isDynamic = element.label === 'Synthetic Users';
      const dir = isDynamic ? path.join(this.outputRoot, 'roles') : this.staticRolesDir;
      return this.scanRoles(dir, isDynamic).map(r => new RoleItem(r));
    }
    if (element instanceof RoleItem && element.role.isDynamic) {
      return element.role.interviews.map(f => new InterviewItem(f));
    }
    return [];
  }

  scanRoles(dir: string, isDynamic: boolean): RoleMeta[] {
    if (!fs.existsSync(dir)) { return []; }
    const interviewDir = path.join(this.outputRoot, '01-empathize');

    return fs.readdirSync(dir)
      .filter(f => f.endsWith('.md'))
      .sort()
      .map(f => {
        const filePath = path.join(dir, f);
        const content = fs.readFileSync(filePath, 'utf-8');
        const meta = parseRoleMeta(content);
        const slug = path.basename(f, '.md');
        const name = meta.name || slug.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

        const interviews: string[] = [];
        if (isDynamic && fs.existsSync(interviewDir)) {
          const interviewFile = path.join(interviewDir, `interview-${slug}.md`);
          if (fs.existsSync(interviewFile)) { interviews.push(interviewFile); }
        }

        return { name, slug, role: meta.role || '', filePath, relPath: path.relative(this.workspaceRoot, filePath), isDynamic, interviews };
      });
  }

  dispose(): void {
    this.watchers.forEach(w => w.dispose());
    this._onDidChangeTreeData.dispose();
  }
}

function parseRoleMeta(content: string): Record<string, string> {
  const result: Record<string, string> = {};
  const lines = content.split('\n');
  let pastH1 = false;
  for (const line of lines) {
    if (line.startsWith('# ') && !line.startsWith('## ')) {
      pastH1 = true;
      result.name = line.slice(2).trim();
      continue;
    }
    if (!pastH1) { continue; }
    if (line.startsWith('## ')) { break; }
    const m = line.match(/^- \*\*(.+?):\*\*\s*(.*)/);
    if (m) { result[m[1].toLowerCase().trim()] = m[2].trim(); }
  }
  return result;
}

class RoleCategoryItem extends vscode.TreeItem {
  constructor(label: string, count: number, icon: string) {
    super(label, vscode.TreeItemCollapsibleState.Expanded);
    this.description = `${count}`;
    this.iconPath = new vscode.ThemeIcon(icon);
    this.contextValue = 'roleCategory';
  }
}

class RoleItem extends vscode.TreeItem {
  constructor(public readonly role: RoleMeta) {
    super(role.name, role.isDynamic && role.interviews.length > 0
      ? vscode.TreeItemCollapsibleState.Collapsed : vscode.TreeItemCollapsibleState.None);
    this.description = role.role;
    this.tooltip = `${role.name}\n${role.role}\nClick to preview`;
    this.contextValue = role.isDynamic ? 'dynamicRole' : 'staticRole';
    this.iconPath = role.isDynamic
      ? new vscode.ThemeIcon('account', new vscode.ThemeColor('charts.blue'))
      : new vscode.ThemeIcon('shield', new vscode.ThemeColor('testing.iconPassed'));
    this.command = { command: 'markdown.showPreview', title: 'Preview Role', arguments: [vscode.Uri.file(role.filePath)] };
  }
}

class InterviewItem extends vscode.TreeItem {
  constructor(filePath: string) {
    super(path.basename(filePath), vscode.TreeItemCollapsibleState.None);
    this.iconPath = new vscode.ThemeIcon('comment-discussion', new vscode.ThemeColor('charts.yellow'));
    this.contextValue = 'interview';
    this.tooltip = 'Click to preview interview';
    this.command = { command: 'markdown.showPreview', title: 'Preview Interview', arguments: [vscode.Uri.file(filePath)] };
  }
}
