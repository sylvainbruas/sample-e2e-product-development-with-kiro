import * as vscode from 'vscode';

export interface KiroChatOptions {
  /** Prefix for warning/error messages, e.g. "Design Thinking" */
  displayName: string;
  /** Delay in ms between newSession and sendMainUserInput. Defaults to 500. */
  sessionDelay?: number;
}

/**
 * Standardized interface for sending messages to Kiro chat.
 *
 * Usage:
 *   const chat = new KiroChat({ displayName: 'My Extension' });
 *   await chat.send('do something');
 *   await chat.sendRaw('yolo');  // no new session, just sends
 */
export class KiroChat {
  private readonly displayName: string;
  private readonly sessionDelay: number;

  constructor(opts: KiroChatOptions) {
    this.displayName = opts.displayName;
    this.sessionDelay = opts.sessionDelay ?? 500;
  }

  /**
   * Open a new Kiro chat session and send a prompt.
   * Wraps the message with the power prefix if provided.
   */
  async send(message: string, powerName?: string): Promise<void> {
    if (!message || typeof message !== 'string') {
      vscode.window.showWarningMessage(`${this.displayName}: No message to send.`);
      return;
    }
    const prompt = powerName
      ? `Use the ${powerName} power to run ${message}`
      : message;
    try {
      await vscode.commands.executeCommand('kiroAgent.newSession');
      await delay(this.sessionDelay);
      await vscode.commands.executeCommand('kiroAgent.sendMainUserInput', prompt);
    } catch (e: any) {
      vscode.window.showErrorMessage(`${this.displayName}: Failed to send to chat — ${e.message}`);
    }
  }

  /**
   * Send a message to the current Kiro chat session without opening a new one.
   */
  async sendRaw(message: string): Promise<void> {
    try {
      await vscode.commands.executeCommand('kiroAgent.sendMainUserInput', message);
    } catch (e: any) {
      vscode.window.showErrorMessage(`${this.displayName}: Failed to send — ${e.message}`);
    }
  }
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
