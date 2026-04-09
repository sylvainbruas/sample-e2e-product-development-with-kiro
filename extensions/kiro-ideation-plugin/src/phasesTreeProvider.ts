import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { BaseTreeProvider, MessageItem, JsonFileWatcher } from 'openvsx-kiro';
import {
  Manifest, PhaseName, PhaseData, StepData,
  PHASE_ORDER, PHASE_DISPLAY, STEP_MAP
} from './types';

type TreeItem = PhaseItem | StepItem | MessageItem;

export class PhasesTreeProvider extends BaseTreeProvider<TreeItem> {
  constructor(
    private watcher: JsonFileWatcher<Manifest>,
    private workspaceRoot: string
  ) {
    super();
    watcher.onDidChange(() => this._onDidChangeTreeData.fire());
  }

  protected getRootChildren(): TreeItem[] {
    const manifest = this.watcher.current;
    if (!manifest) {
      return [new MessageItem('No manifest.json found. Run /al-dt-workflow-empathize to start.')];
    }
    return PHASE_ORDER.map((name, idx) => {
      const phase = manifest.phases[name];
      if (!phase) { return null; }
      const display = PHASE_DISPLAY[name];
      const isNext = phase.status === 'not_started' &&
        (idx === 0 || (manifest.phases[PHASE_ORDER[idx - 1]]?.status === 'completed'));
      return new PhaseItem(name, display.label, display.number, phase, display.skill, isNext);
    }).filter((item): item is PhaseItem => item !== null);
  }

  protected getChildrenOf(element: TreeItem): TreeItem[] {
    if (element instanceof PhaseItem) {
      const manifest = this.watcher.current;
      if (!manifest) { return []; }
      const phase = manifest.phases[element.phaseName];
      const stepMap = STEP_MAP[element.phaseName];
      return Object.entries(stepMap).map(([key, info]) => {
        const stepData = (phase?.steps[key] as StepData | undefined) ?? { status: 'not_started' };
        return new StepItem(info.label, stepData, info.file, info.specs ?? false, this.workspaceRoot);
      });
    }
    return [];
  }
}

class PhaseItem extends vscode.TreeItem {
  constructor(
    public readonly phaseName: PhaseName,
    label: string,
    phaseNumber: number,
    phase: PhaseData,
    public readonly skill: string,
    isNext: boolean
  ) {
    super(`${phaseNumber}. ${label}`, vscode.TreeItemCollapsibleState.Collapsed);
    this.contextValue = 'phase';
    this.tooltip = `${label} — ${phase.status}\nClick ▶ to invoke /${skill}`;

    if (phase.status === 'completed') {
      this.iconPath = new vscode.ThemeIcon('pass-filled', new vscode.ThemeColor('testing.iconPassed'));
    } else if (phase.status === 'in_progress') {
      this.iconPath = new vscode.ThemeIcon('circle-filled', new vscode.ThemeColor('charts.yellow'));
    } else if (isNext) {
      this.iconPath = new vscode.ThemeIcon('arrow-circle-right', new vscode.ThemeColor('textLink.foreground'));
    } else {
      this.iconPath = new vscode.ThemeIcon('circle-large-outline', new vscode.ThemeColor('disabledForeground'));
    }
  }
}

class StepItem extends vscode.TreeItem {
  constructor(
    label: string,
    step: StepData,
    filePath: string | undefined,
    isSpecsDashboard: boolean,
    workspaceRoot: string
  ) {
    super(label, vscode.TreeItemCollapsibleState.None);
    this.contextValue = 'step';

    const effectiveStatus = step.status;

    if (effectiveStatus === 'completed') {
      this.iconPath = new vscode.ThemeIcon('check', new vscode.ThemeColor('testing.iconPassed'));
    } else if (effectiveStatus === 'user_confirmed') {
      this.iconPath = new vscode.ThemeIcon('account', new vscode.ThemeColor('charts.blue'));
    } else if (effectiveStatus === 'in_progress') {
      this.iconPath = new vscode.ThemeIcon('circle-filled', new vscode.ThemeColor('charts.yellow'));
    } else {
      this.iconPath = new vscode.ThemeIcon('circle-outline', new vscode.ThemeColor('disabledForeground'));
    }

    if (isSpecsDashboard) {
      this.description = 'Specs Dashboard';
      this.command = { command: 'ideation.openSpecsDashboard', title: 'Open Specs Dashboard', arguments: [] };
      this.tooltip = `${label} — ${step.status}\nClick to open Specs Dashboard`;
    } else if (filePath) {
      const fullPath = path.join(workspaceRoot, filePath);
      const isDir = fs.existsSync(fullPath) && fs.statSync(fullPath).isDirectory();
      const fileName = path.basename(filePath);

      if (isDir && filePath.endsWith('roles')) {
        this.description = 'Roles Dashboard';
        this.command = { command: 'ideation.openRolesDashboard', title: 'Open Roles Dashboard', arguments: [] };
        this.tooltip = `${label} — ${step.status}\nClick to open Roles Dashboard`;
      } else if (fs.existsSync(fullPath)) {
        this.description = fileName;
        this.command = { command: 'markdown.showPreview', title: 'Open Artifact', arguments: [vscode.Uri.file(fullPath)] };
        this.tooltip = `${label} — ${step.status}\nClick to open ${fileName}`;
      } else {
        this.description = `${fileName} (pending)`;
        this.tooltip = `${label} — ${step.status}\n${fileName} not yet created`;
      }
    } else {
      this.tooltip = `${label} — ${step.status}`;
    }

    if (step.confirmedAt) {
      this.tooltip += `\nConfirmed: ${new Date(step.confirmedAt as string).toLocaleString()}`;
    }
  }
}
