import * as fs from 'fs';
import * as path from 'path';

/** HTML-escape a string for safe embedding in webview HTML. */
export function esc(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

/** Escape a string for safe use inside a single-quoted JS string within an HTML attribute. */
export function escAttr(text: string): string {
  return text
    .replace(/\\/g, '\\\\')
    .replace(/'/g, "\\'")
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/&/g, '&amp;');
}

// --- Safe HTML tagged template ---

/** Wrapper that marks a string as already-safe HTML (skips auto-escaping in html``). */
export class SafeHtml { constructor(public readonly value: string) {} }

/** Wrapper that marks a string for JS-in-attribute escaping in html``. */
export class SafeAttr { constructor(public readonly value: string) {} }

/** Mark a pre-built HTML fragment as safe — won't be double-escaped by html``. */
export function raw(value: string): SafeHtml { return new SafeHtml(value); }

/** Mark a value for JS-string-in-attribute escaping (for onclick handlers etc.) in html``. */
export function attr(value: string): SafeAttr { return new SafeAttr(value); }

/**
 * Tagged template that auto-escapes interpolations for safe HTML.
 *
 *   html`<span>${userName}</span>`           // auto HTML-escaped
 *   html`<div>${raw(childHtml)}</div>`       // pre-built HTML, no escaping
 *   html`<a onclick="fn('${attr(v)}')">`     // JS-in-attribute escaped
 */
export function html(strings: TemplateStringsArray, ...values: unknown[]): string {
  return strings.reduce((result, str, i) => {
    if (i >= values.length) { return result + str; }
    const val = values[i];
    if (val instanceof SafeHtml) { return result + str + val.value; }
    if (val instanceof SafeAttr) { return result + str + escAttr(val.value); }
    return result + str + esc(String(val));
  }, '');
}

/** Convert a slug like "my-thing_name" to "My Thing Name". */
export function titleCase(slug: string): string {
  return slug
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, c => c.toUpperCase());
}

/**
 * Minimal YAML front-matter parser.
 * Extracts the `---` delimited block at the top of a markdown file
 * and returns key-value pairs. Handles quoted strings and JSON arrays.
 */
export function parseFrontMatter(content: string): Record<string, any> {
  const match = content.match(/^---\s*\n([\s\S]*?)\n---/);
  if (!match) { return {}; }

  const result: Record<string, any> = {};
  for (const line of match[1].split('\n')) {
    const kv = line.match(/^(\w[\w-]*):\s*(.+)$/);
    if (!kv) { continue; }
    const key = kv[1].trim();
    let value: any = kv[2].trim();

    // Strip surrounding quotes
    if ((value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }

    // Parse JSON arrays like ["a", "b"]
    if (value.startsWith('[') && value.endsWith(']')) {
      try { value = JSON.parse(value); } catch { /* keep as string */ }
    }

    result[key] = value;
  }
  return result;
}

/** Read a text file, returning empty string on failure. */
export function readTextFile(filePath: string): string {
  try {
    return fs.readFileSync(filePath, 'utf-8');
  } catch {
    return '';
  }
}

/**
 * Resolve a relative path within a root directory and verify it doesn't escape.
 * Returns the resolved absolute path, or undefined if the path traverses outside root.
 */
export function safePath(root: string, relative: string): string | undefined {
  const resolved = path.resolve(root, relative);
  return resolved.startsWith(root + path.sep) || resolved === root ? resolved : undefined;
}

/** List files in a directory matching an extension. Returns full paths, sorted. */
export function listFiles(dir: string, ext: string): string[] {
  if (!fs.existsSync(dir)) { return []; }
  try {
    return fs.readdirSync(dir)
      .filter(f => f.endsWith(ext))
      .map(f => path.join(dir, f))
      .sort();
  } catch {
    return [];
  }
}
