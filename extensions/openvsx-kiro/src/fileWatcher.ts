import * as vscode from 'vscode';
import * as fs from 'fs';
import * as path from 'path';

export interface JsonFileWatcherOptions<T> {
  /** Absolute path to the JSON file to watch. */
  filePath: string;
  /** Workspace root for creating RelativePattern watchers. */
  workspaceRoot: string;
  /**
   * Glob patterns (relative to workspaceRoot) to watch in addition
   * to the primary file. Useful for watching a whole directory.
   */
  additionalPatterns?: string[];
  /** Poll interval in ms. Defaults to 2000. Set to 0 to disable polling. */
  pollInterval?: number;
}

/**
 * Watches a JSON file on disk and emits parsed values on change.
 * Combines VS Code file system watchers with a poll fallback
 * for reliability across OS and editor versions.
 *
 * Usage:
 *   const watcher = new JsonFileWatcher<MyType>({
 *     filePath: '/abs/path/to/manifest.json',
 *     workspaceRoot: '/abs/path/to/workspace',
 *     additionalPatterns: ['design-thinking/**\/*'],
 *   });
 *   watcher.onDidChange(data => { ... });
 *   await watcher.init();
 */
export class JsonFileWatcher<T> {
  private _onDidChange = new vscode.EventEmitter<T | null>();
  readonly onDidChange = this._onDidChange.event;

  private watchers: vscode.Disposable[] = [];
  private cached: T | null = null;
  private pollTimer: NodeJS.Timeout | undefined;
  private lastContent: string = '';

  private readonly filePath: string;
  private readonly workspaceRoot: string;
  private readonly additionalPatterns: string[];
  private readonly pollInterval: number;

  constructor(opts: JsonFileWatcherOptions<T>) {
    this.filePath = opts.filePath;
    this.workspaceRoot = opts.workspaceRoot;
    this.additionalPatterns = opts.additionalPatterns ?? [];
    this.pollInterval = opts.pollInterval ?? 2000;
  }

  get current(): T | null {
    return this.cached;
  }

  get fileUri(): vscode.Uri {
    return vscode.Uri.file(this.filePath);
  }

  async init(): Promise<void> {
    await this.read();

    // Watch the primary file
    const relPath = path.relative(this.workspaceRoot, this.filePath);
    const primaryPattern = new vscode.RelativePattern(this.workspaceRoot, relPath);
    const primaryWatcher = vscode.workspace.createFileSystemWatcher(primaryPattern);
    primaryWatcher.onDidChange(() => this.read());
    primaryWatcher.onDidCreate(() => this.read());
    primaryWatcher.onDidDelete(() => this.clear());
    this.watchers.push(primaryWatcher);

    // Watch additional patterns
    for (const pattern of this.additionalPatterns) {
      const extra = new vscode.RelativePattern(this.workspaceRoot, pattern);
      const w = vscode.workspace.createFileSystemWatcher(extra);
      w.onDidChange(() => this.read());
      w.onDidCreate(() => this.read());
      w.onDidDelete(() => this.read());
      this.watchers.push(w);
    }

    // Poll fallback
    if (this.pollInterval > 0) {
      this.pollTimer = setInterval(() => this.poll(), this.pollInterval);
    }
  }

  async read(): Promise<T | null> {
    try {
      const doc = await vscode.workspace.fs.readFile(this.fileUri);
      const content = Buffer.from(doc).toString('utf-8');
      this.lastContent = content;
      this.cached = JSON.parse(content) as T;
      this._onDidChange.fire(this.cached);
      return this.cached;
    } catch {
      this.clear();
      return null;
    }
  }

  private poll(): void {
    try {
      const content = fs.readFileSync(this.filePath, 'utf-8');
      if (content !== this.lastContent) {
        this.lastContent = content;
        try {
          this.cached = JSON.parse(content) as T;
          this._onDidChange.fire(this.cached);
        } catch { /* invalid JSON, skip */ }
      }
    } catch {
      if (this.cached !== null) {
        this.clear();
      }
    }
  }

  private clear(): void {
    this.cached = null;
    this.lastContent = '';
    this._onDidChange.fire(null);
  }

  dispose(): void {
    this.watchers.forEach(w => w.dispose());
    if (this.pollTimer) { clearInterval(this.pollTimer); }
    this._onDidChange.dispose();
  }
}
