import * as vscode from 'vscode';

/**
 * Abstract tree data provider with built-in refresh support.
 *
 * Subclasses implement `getRootChildren()` and `getChildrenOf(element)`.
 */
export abstract class BaseTreeProvider<T extends vscode.TreeItem>
  implements vscode.TreeDataProvider<T>
{
  protected _onDidChangeTreeData = new vscode.EventEmitter<T | undefined | void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  getTreeItem(element: T): vscode.TreeItem {
    return element;
  }

  getChildren(element?: T): T[] {
    if (!element) {
      return this.getRootChildren();
    }
    return this.getChildrenOf(element);
  }

  /** Return top-level tree items. */
  protected abstract getRootChildren(): T[];

  /** Return children of a given tree item. Default: no children. */
  protected getChildrenOf(_element: T): T[] {
    return [];
  }
}

/**
 * A simple non-interactive tree item for displaying messages
 * like "No data found" or "Run X to start".
 */
export class MessageItem extends vscode.TreeItem {
  constructor(message: string, icon: string = 'info') {
    super(message, vscode.TreeItemCollapsibleState.None);
    this.contextValue = 'message';
    this.iconPath = new vscode.ThemeIcon(icon);
  }
}
