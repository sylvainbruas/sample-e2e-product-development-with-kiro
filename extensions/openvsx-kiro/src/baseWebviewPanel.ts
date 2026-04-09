import * as vscode from 'vscode';
import { esc } from './utils';

export { esc };

export interface WebviewPanelOptions {
  /** Internal panel type id, e.g. 'designThinkingDashboard' */
  viewType: string;
  /** Human-readable panel title */
  title: string;
  /** Enable scripts in the webview. Defaults to true. */
  enableScripts?: boolean;
  /** Retain webview content when hidden. Defaults to true. */
  retainContextWhenHidden?: boolean;
}

/**
 * Abstract base for webview dashboard panels.
 *
 * Subclasses implement:
 *   - `getBodyHtml()` — returns the inner HTML for the panel body
 *   - `onMessage(msg)` — handles messages from the webview script
 *   - `getScriptJs()` — returns the JS to inject (acquireVsCodeApi + handlers)
 *   - optionally override `getCss()` to extend the base styles
 */
export abstract class BaseWebviewPanel {
  protected panel: vscode.WebviewPanel | undefined;
  protected disposables: vscode.Disposable[] = [];

  constructor(protected readonly opts: WebviewPanelOptions) {}

  show(extensionUri: vscode.Uri): void {
    if (this.panel) {
      this.panel.reveal();
      this.update();
      return;
    }

    this.panel = vscode.window.createWebviewPanel(
      this.opts.viewType,
      this.opts.title,
      vscode.ViewColumn.One,
      {
        enableScripts: this.opts.enableScripts ?? true,
        retainContextWhenHidden: this.opts.retainContextWhenHidden ?? true,
      }
    );

    this.panel.onDidDispose(() => {
      this.panel = undefined;
      this.disposables.forEach(d => d.dispose());
      this.disposables = [];
    });

    this.panel.webview.onDidReceiveMessage(
      msg => this.onMessage(msg),
      undefined,
      this.disposables
    );

    this.onDidCreatePanel();
    this.update();
  }

  /** Called once after the panel is first created. Hook up data listeners here. */
  protected onDidCreatePanel(): void {}

  protected update(): void {
    if (!this.panel) { return; }
    this.panel.webview.html = this.wrapHtml(this.getBodyHtml());
  }

  /** Return the inner body HTML. */
  protected abstract getBodyHtml(): string;

  /** Handle a message posted from the webview script. */
  protected abstract onMessage(msg: any): void;

  /**
   * Return the `<script>` content (without tags).
   * The base provides `acquireVsCodeApi()` — override to add handlers.
   */
  protected abstract getScriptJs(): string;

  /** Return CSS to use. Override to extend or replace. */
  protected getCss(): string {
    return BASE_CSS;
  }

  protected wrapHtml(body: string): string {
    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
${this.getCss()}
</style>
</head>
<body>
${body}
<script>
  const vscode = acquireVsCodeApi();
  ${this.getScriptJs()}
</script>
</body>
</html>`;
  }

  dispose(): void {
    this.panel?.dispose();
    this.disposables.forEach(d => d.dispose());
  }
}

/**
 * Shared base CSS variables and reset that match VS Code's theming.
 * Extensions can append their own rules via `getCss()`.
 */
export const BASE_CSS = `
  :root {
    --bg: var(--vscode-editor-background);
    --fg: var(--vscode-editor-foreground);
    --border: var(--vscode-panel-border, #333);
    --accent: var(--vscode-textLink-foreground, #4fc1ff);
    --card-bg: var(--vscode-editorWidget-background, #1e1e1e);
    --green: var(--vscode-testing-iconPassed, #4caf50);
    --yellow: var(--vscode-charts-yellow, #ff9800);
    --red: var(--vscode-testing-iconFailed, #f44336);
    --dim: var(--vscode-disabledForeground, #666);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: var(--vscode-font-family);
    color: var(--fg);
    background: var(--bg);
    padding: 24px;
    font-size: 14px;
  }
  h1 { font-size: 1.6em; margin-bottom: 4px; }
  h2 { font-size: 1.3em; margin: 24px 0 12px; }
  .meta { opacity: 0.6; font-size: 0.9em; margin-bottom: 18px; }

  .empty { text-align: center; padding: 60px 20px; opacity: 0.7; }
  .empty code { background: var(--card-bg); padding: 2px 6px; border-radius: 3px; }

  .action-btn {
    background: var(--accent); color: var(--bg); border: none; padding: 8px 20px;
    border-radius: 4px; cursor: pointer; font-size: 1em; font-family: var(--vscode-font-family);
    font-weight: 600; margin-top: 16px;
  }
  .action-btn.small { padding: 4px 12px; font-size: 0.85em; margin-top: 0; }
  .action-btn:hover { opacity: 0.9; }

  .run-btn {
    background: transparent; border: 1px solid var(--border); color: var(--accent); padding: 4px 12px;
    border-radius: 4px; cursor: pointer; font-size: 0.85em; font-family: var(--vscode-font-family);
    white-space: nowrap; display: flex; align-items: center; gap: 4px;
  }
  .run-btn:hover { background: var(--accent); color: var(--bg); }

  .progress-bar-container {
    width: 100%; height: 8px; background: var(--border);
    border-radius: 4px; overflow: hidden; margin-bottom: 6px;
  }
  .progress-bar {
    height: 100%; background: var(--accent);
    border-radius: 4px; transition: width 0.3s;
  }

  .step { font-size: 1em; padding: 5px 0; display: flex; align-items: center; gap: 8px; }
  .step-icon { width: 18px; text-align: center; flex-shrink: 0; font-size: 1em; }
  .step-label { flex-shrink: 0; }
  .step.completed .step-icon { color: var(--green); }
  .step.in-progress .step-icon { color: var(--yellow); }
  .step.not-started .step-icon { color: var(--dim); }
  .step.not-started .step-label { color: var(--dim); }

  .file-link {
    margin-left: auto; font-size: 0.9em; color: var(--accent); text-decoration: none;
    font-family: var(--vscode-font-family); cursor: pointer; opacity: 0.8;
  }
  .file-link:hover { text-decoration: underline; opacity: 1; }
  .file-pending {
    margin-left: auto; font-size: 0.85em; color: var(--dim);
    font-family: var(--vscode-font-family); font-style: italic;
  }
`;
