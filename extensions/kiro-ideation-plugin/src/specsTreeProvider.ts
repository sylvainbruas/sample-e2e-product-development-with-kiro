import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { BaseTreeProvider, MessageItem, JsonFileWatcher } from 'openvsx-kiro';
import { Manifest } from './types';

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

interface SpecPlan { specs: SpecPlanEntry[]; }

type TreeItem = SpecItem | MessageItem;

export class SpecsTreeProvider extends BaseTreeProvider<TreeItem> {
  private watchers: vscode.Disposable[] = [];

  constructor(
    manifestWatcher: JsonFileWatcher<Manifest>,
    private workspaceRoot: string,
    private outputRoot: string
  ) {
    super();
    manifestWatcher.onDidChange(() => this._onDidChangeTreeData.fire());

    const relOutput = path.relative(workspaceRoot, outputRoot);
    const planWatcher = vscode.workspace.createFileSystemWatcher(
      new vscode.RelativePattern(workspaceRoot, `${relOutput}/spec-plan.json`));
    planWatcher.onDidChange(() => this._onDidChangeTreeData.fire());
    planWatcher.onDidCreate(() => this._onDidChangeTreeData.fire());
    planWatcher.onDidDelete(() => this._onDidChangeTreeData.fire());
    this.watchers.push(planWatcher);

    const specsWatcher = vscode.workspace.createFileSystemWatcher(
      new vscode.RelativePattern(workspaceRoot, '.kiro/specs/**/*'));
    specsWatcher.onDidChange(() => this._onDidChangeTreeData.fire());
    specsWatcher.onDidCreate(() => this._onDidChangeTreeData.fire());
    specsWatcher.onDidDelete(() => this._onDidChangeTreeData.fire());
    this.watchers.push(specsWatcher);
  }

  protected getRootChildren(): TreeItem[] {
    const plan = this.readPlan();
    if (!plan?.specs?.length) { return [new MessageItem('No specs created yet')]; }
    const existing = plan.specs.filter(s => fs.existsSync(path.join(this.workspaceRoot, s.specPath)));
    if (!existing.length) { return [new MessageItem('No specs created yet')]; }
    return existing.map(s => new SpecItem(s.name, s.specPath, s.featureGroups, s.description, this.workspaceRoot));
  }

  private readPlan(): SpecPlan | null {
    const planPath = path.join(this.outputRoot, 'spec-plan.json');
    if (!fs.existsSync(planPath)) { return null; }
    try { return JSON.parse(fs.readFileSync(planPath, 'utf-8')); } catch { return null; }
  }

  dispose(): void {
    this.watchers.forEach(w => w.dispose());
    this._onDidChangeTreeData.dispose();
  }
}

class SpecItem extends vscode.TreeItem {
  public specPath?: string;
  constructor(name: string, specPath: string, featureGroups: string[], description: string, workspaceRoot: string) {
    super(name, vscode.TreeItemCollapsibleState.None);
    if (specPath && workspaceRoot) {
      this.resourceUri = vscode.Uri.file(path.join(workspaceRoot, specPath));
      this.iconPath = new vscode.ThemeIcon('file-code');
      this.description = featureGroups.join(', ');
      this.tooltip = description || `Path: ${specPath}\nFeatures: ${featureGroups.join(', ')}`;
      this.contextValue = 'spec';
      this.specPath = specPath;
    } else {
      this.iconPath = new vscode.ThemeIcon('info');
      this.description = 'Run /al-dt-generate-specs after prototype phase';
    }
  }
}
