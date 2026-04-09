# Extensions

VS Code / Kiro IDE extensions that provide visual tooling for Agent Lattice workflows.

| Package | Type | Description |
|---------|------|-------------|
| [`openvsx-kiro`](openvsx-kiro/) | Shared library | Reusable building blocks for Kiro extensions — chat integration, webview panels, tree providers, file watching |
| [`kiro-ideation-plugin`](kiro-ideation-plugin/) | VS Code extension | Sidebar dashboard and tree views for navigating the design thinking process |

---

## Table of Contents

- [Quick Start](#quick-start)
- [Kiro Ideation Plugin](#kiro-ideation-plugin)
  - [Activation](#activation)
  - [Sidebar Views](#sidebar-views)
  - [Dashboard](#dashboard)
  - [Commands](#commands)
  - [How It Reads Data](#how-it-reads-data)
- [openvsx-kiro (Shared Library)](#openvsx-kiro-shared-library)
  - [KiroChat](#kirochat)
  - [JsonFileWatcher](#jsonfilewatcher)
  - [BaseWebviewPanel](#basewebviewpanel)
  - [BaseTreeProvider](#basetreeprovider)
  - [Utilities](#utilities)
- [Building](#building)
- [Development](#development)

---

## Quick Start

### Prerequisites

- Node.js v20+
- TypeScript v5.3+ (installed per-package via `npm install`)
- [@vscode/vsce](https://github.com/microsoft/vscode-vsce) for packaging: `npm install -g @vscode/vsce`
- [Kiro](https://kiro.dev) IDE (or VS Code ^1.85.0)

### Build and install

```bash
# Build everything (shared lib + all extensions)
./build.sh

# Or build a specific extension
./build.sh kiro-ideation-plugin
```

Output goes to `out/`:

```
out/
└── kiro-ideation-plugin.vsix
```

Install the `.vsix`:

```bash
# Via command line
code --install-extension out/kiro-ideation-plugin.vsix

# Or via VS Code / Kiro
# Cmd+Shift+P → "Extensions: Install from VSIX..." → select the file
```

---

## Kiro Ideation Plugin

A companion extension for the Agent Lattice [design-thinking module](../agent-lattice/modules/design-thinking/). It provides a visual layer on top of the workflow artifacts, so you can track progress, launch phases, chat with roles, and manage specs — all from the sidebar.

### Activation

The extension activates automatically when it detects:

```
.al/output/design-thinking/manifest.json
```

This file is created when the design thinking module is installed and the first workflow is initiated.

### Sidebar Views

The extension adds a **Kiro Ideation** activity bar container with three tree views:

#### Phases

Shows all six phases in order with status icons:

| Icon | Meaning |
|------|---------|
| `pass-filled` (green) | Completed |
| `arrow-circle-right` (yellow) | In progress |
| `circle-large-outline` (dim) | Not started |

Each phase expands to show its individual steps. Steps link to their output artifacts when available. A play button on each phase sends the corresponding skill command to Kiro Chat.

#### Roles

Lists both static roles (shipped with the module) and dynamic roles (personas created during Empathize). Each role has a **Chat with Role** button that sends `/al-impersonate {path}` to Kiro Chat, opening a conversational session with that role.

Static roles are resolved from these locations (first match wins):
1. `.al/modules/design-thinking/roles/` (installed)
2. `.al-runtime/modules/design-thinking/roles/` (legacy)
3. `agent-lattice/modules/design-thinking/roles/` (dev layout)

Dynamic roles are read from `.al/output/design-thinking/roles/`.

#### Specs

Shows entries from `spec-plan.json` (created during the Generate Specs phase). Each spec shows its status (created vs. pending, detected by checking if `.kiro/specs/{slug}/` exists on disk) and provides buttons to preview or open the requirements file.

### Dashboard

A rich webview panel (`Cmd+Shift+P` → "Open Ideation Dashboard") showing:

- **Project header** — name (from `.al/config.json`), last updated timestamp
- **Progress bar** — completed steps / total steps across all phases
- **Phase cards** — each phase shows its status, step list with file links, and action buttons:
  - **Auto** — sends `auto` to the current chat session (complete current step)
  - **Autoflow** — sends `autoflow` (complete current workflow)
  - **Automagic** — top-level button to run the full lifecycle autonomously
- **Specs section** — created specs with links to their directories

Dedicated dashboards are also available for Roles and Specs individually.

### Commands

| Command | What it does |
|---------|-------------|
| `ideation.openDashboard` | Open the main ideation dashboard |
| `ideation.openSpecsDashboard` | Open the specs dashboard |
| `ideation.openRolesDashboard` | Open the roles dashboard |
| `ideation.runPhase` | Send `/{skill}` to Kiro Chat for a phase |
| `ideation.generateSpecs` | Send `/al-dt-generate-specs` (requires Prototype completed) |
| `ideation.chatWithRole` | Send `/al-impersonate {rolePath}` to Kiro Chat |
| `ideation.previewSpec` | Open a spec's `requirements.md` in markdown preview |
| `ideation.openSpecRaw` | Open a spec's `requirements.md` in the editor |
| `ideation.sendAuto` | Send `auto` to the current chat session |
| `ideation.refresh` | Force re-read manifest and refresh all views |

### How It Reads Data

The extension does **not** run Agent Lattice scripts or parse workflow files. It reads only output artifacts:

1. **`manifest.json`** — workflow state (phase/step statuses, timestamps, file lists). Watched via `JsonFileWatcher` with a 2-second poll fallback.
2. **`spec-plan.json`** — spec breakdown and statuses.
3. **`roles/*.md`** — dynamic role files in the output directory.
4. **`config.json`** — project name for display.

The `JsonFileWatcher` combines VS Code `FileSystemWatcher` events with polling, and also watches the entire `design-thinking/**` directory for any file changes (artifact creation triggers a re-read).

---

## openvsx-kiro (Shared Library)

A pure TypeScript library providing reusable building blocks for Kiro extensions. Not a VS Code extension itself — it's bundled as a local dependency (`"openvsx-kiro": "file:../openvsx-kiro"` in consumer `package.json`).

### KiroChat

Standardized interface for sending messages to Kiro Chat.

```typescript
import { KiroChat } from 'openvsx-kiro';

const chat = new KiroChat({ displayName: 'My Extension' });

// Open a new session and send a prompt
await chat.send('/al-dt-workflow-empathize');

// Send to the current session without opening a new one
await chat.sendRaw('auto');

// Wrap with a power prefix
await chat.send('@configure', 'kiro-configurator');
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `displayName` | `string` | — | Prefix for warning/error messages |
| `sessionDelay` | `number` | `500` | Delay (ms) between `newSession` and `sendMainUserInput` |

Under the hood, `send()` calls `kiroAgent.newSession` → waits `sessionDelay` → calls `kiroAgent.sendMainUserInput`. `sendRaw()` skips the session creation.

### JsonFileWatcher

Watches a JSON file on disk and emits parsed values on change. Dual strategy: VS Code `FileSystemWatcher` for instant notification + a configurable poll fallback for reliability.

```typescript
import { JsonFileWatcher } from 'openvsx-kiro';

const watcher = new JsonFileWatcher<MyType>({
  filePath: '/absolute/path/to/data.json',
  workspaceRoot: '/absolute/path/to/workspace',
  additionalPatterns: ['output/**/*'],  // also watch these globs
  pollInterval: 2000,                    // ms, set 0 to disable
});

watcher.onDidChange(data => {
  // data is parsed JSON (or null if file was deleted/invalid)
});

await watcher.init();

// Access current cached value
const current = watcher.current;
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `filePath` | `string` | — | Absolute path to the JSON file |
| `workspaceRoot` | `string` | — | Workspace root for RelativePattern watchers |
| `additionalPatterns` | `string[]` | `[]` | Extra glob patterns to watch (relative to workspace root) |
| `pollInterval` | `number` | `2000` | Poll interval in ms (0 to disable) |

### BaseWebviewPanel

Abstract base class for VS Code webview dashboard panels. Handles panel lifecycle, message routing, and wraps content in a themed HTML shell.

```typescript
import { BaseWebviewPanel, BASE_CSS } from 'openvsx-kiro';

class MyDashboard extends BaseWebviewPanel {
  constructor() {
    super({ viewType: 'myDashboard', title: 'My Dashboard' });
  }

  protected getBodyHtml(): string {
    return '<h1>Hello</h1>';
  }

  protected onMessage(msg: any): void {
    // Handle messages from webview JS
  }

  protected getScriptJs(): string {
    return `document.querySelector('h1').addEventListener('click', () => {
      vscode.postMessage({ type: 'clicked' });
    });`;
  }
}
```

Subclasses implement:
- `getBodyHtml()` — inner HTML for the panel body
- `onMessage(msg)` — handle messages from the webview script
- `getScriptJs()` — JS to inject (has access to `vscode` via `acquireVsCodeApi()`)
- `getCss()` *(optional)* — override to extend `BASE_CSS`

`BASE_CSS` provides VS Code theme-aware CSS variables (`--bg`, `--fg`, `--accent`, `--card-bg`, `--green`, `--yellow`, `--red`, `--dim`) and base component styles for cards, buttons, progress bars, steps, and file links.

### BaseTreeProvider

Abstract tree data provider with built-in refresh support.

```typescript
import { BaseTreeProvider, MessageItem } from 'openvsx-kiro';

class MyTree extends BaseTreeProvider<vscode.TreeItem> {
  protected getRootChildren(): vscode.TreeItem[] {
    return [new MessageItem('Nothing here yet', 'info')];
  }

  protected getChildrenOf(element: vscode.TreeItem): vscode.TreeItem[] {
    return [];
  }
}
```

Also exports `MessageItem` — a simple non-interactive tree item for placeholder messages.

### Utilities

| Function | Signature | Description |
|----------|-----------|-------------|
| `esc` | `(text: string) => string` | HTML-escape a string for safe embedding in webviews |
| `titleCase` | `(slug: string) => string` | Convert `"my-thing_name"` to `"My Thing Name"` |
| `parseFrontMatter` | `(content: string) => Record<string, any>` | Parse YAML front-matter from markdown files |
| `readTextFile` | `(filePath: string) => string` | Read a text file, returning `""` on failure |
| `listFiles` | `(dir: string, ext: string) => string[]` | List files in a directory matching an extension |

---

## Building

The build script handles the full pipeline:

```bash
./build.sh                        # Build all extensions
./build.sh kiro-ideation-plugin   # Build a specific extension
```

What it does:

1. Builds `openvsx-kiro` shared library first (`npx tsc`)
2. For each extension: installs deps → compiles TypeScript → packages with `vsce`
3. Handles a symlink issue: extensions reference `openvsx-kiro` as a local `file:` dependency. npm creates a symlink, but `vsce` can't follow symlinks during packaging. The build script temporarily replaces the symlink with a real copy, packages, then restores the symlink.

Output: `out/{extension-name}.vsix`

---

## Development

### Watch mode

For live development, run the TypeScript compiler in watch mode:

```bash
# Shared lib
cd openvsx-kiro && npm run watch

# Extension
cd kiro-ideation-plugin && npm run watch
```

Then press `F5` in VS Code to launch the Extension Development Host.

### Adding a new extension

1. Create a new directory with a `package.json` (engines `vscode ^1.85.0`)
2. Add `"openvsx-kiro": "file:../openvsx-kiro"` to dependencies
3. Implement activation in `src/extension.ts`
4. The build script picks up any directory with a `package.json` automatically (excluding `openvsx-kiro` itself and `out/`)
