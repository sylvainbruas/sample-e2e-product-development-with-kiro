import * as vscode from 'vscode';

export interface KiroChatOptions {
  /** Prefix for warning/error messages, e.g. "Design Thinking" */
  displayName: string;
  /** Delay in ms between newSession and sending the prompt. Defaults to 500. */
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
      await sendPrompt(prompt, this.sessionDelay);
    } catch (e: any) {
      vscode.window.showErrorMessage(`${this.displayName}: Failed to send to chat — ${e.message}`);
    }
  }

  /**
   * Send a message to the current Kiro chat session without opening a new one.
   */
  async sendRaw(message: string): Promise<void> {
    try {
      await sendPrompt(message, this.sessionDelay);
    } catch (e: any) {
      vscode.window.showErrorMessage(`${this.displayName}: Failed to send — ${e.message}`);
    }
  }
}

/**
 * Send a prompt to Kiro chat, opening a new session with the prompt preloaded.
 *
 * Kiro exposes `kiroAgent.loadSessionWithPrompt(session, prompt)`, which opens
 * a chat session and submits the given prompt. The first argument is the target
 * session (undefined = new session); the second is the prompt string.
 *
 * Older builds used `kiroAgent.sendMainUserInput`, which no longer exists. We
 * fall back to it only if the current command is unavailable.
 */
async function sendPrompt(prompt: string, sessionDelay: number): Promise<void> {
  const commands = await vscode.commands.getCommands(true);
  if (commands.includes('kiroAgent.loadSessionWithPrompt')) {
    await vscode.commands.executeCommand('kiroAgent.loadSessionWithPrompt', undefined, prompt);
    return;
  }
  // Legacy fallback for older Kiro versions.
  await vscode.commands.executeCommand('kiroAgent.newSession');
  await delay(sessionDelay);
  await vscode.commands.executeCommand('kiroAgent.sendMainUserInput', prompt);
}

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}
