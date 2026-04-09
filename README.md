# Sample for End-to-End Product Development with Kiro

This sample demonstrates how to run a complete product development lifecycle — from user research through implementation-ready specs — using AI-assisted workflows inside the Kiro IDE. It combines a document-driven workflow framework (**Agent Lattice**) with companion **IDE extensions** that visualize progress in real time.

## What's Inside

| Directory | What it is |
|-----------|-----------|
| [`agent-lattice/`](agent-lattice/) | The core framework — a runtime that orchestrates roles, workflows, gates, and scripts, plus pluggable modules for design thinking and Kiro spec generation |
| [`extensions/`](extensions/) | VS Code / Kiro IDE extensions — a shared library (`openvsx-kiro`) and a design-thinking visualizer (`kiro-ideation-plugin`) |

Each component has its own README with a deep dive into architecture, modules, and usage:

- [Agent Lattice README](agent-lattice/README.md) — runtime internals, module system, design thinking process, Kiro bridge
- [Extensions README](extensions/README.md) — shared library API, ideation plugin features, build and install

## Quick Start

### Prerequisites

- Python 3.10+
- [Kiro](https://kiro.dev) IDE (or VS Code ^1.85.0 for extensions only)
- Node.js v20+ and npm (for building extensions)

### 1. Install Agent Lattice into your project

```bash
# Install runtime + all modules
python3 agent-lattice/installer.py install --target /path/to/project --all

# Or pick specific modules
python3 agent-lattice/installer.py install --target /path/to/project --modules design-thinking,kiro
```

This copies the runtime and selected modules into `.al/` and registers Kiro skills under `.kiro/skills/`.

### 2. Open the project in Kiro

The installed skills appear in the skill picker. Start with the entry workflow:

```
/al-dt-workflow-empathize
```

Follow the guided phases: **Empathize** → **Define** → **Ideate** → **Prototype** → **Test** → **Generate Specs** → **Create Spec**.

### 3. (Optional) Install the visualizer extension

Build and install the Kiro Ideation extension for a sidebar dashboard that tracks phases, roles, and specs:

```bash
cd extensions && ./build.sh kiro-ideation-plugin
```

Then install the `.vsix` from `extensions/out/`:

```bash
code --install-extension extensions/out/kiro-ideation-plugin.vsix
```

The extension activates automatically when it detects `.al/output/design-thinking/manifest.json` in your workspace.

## How It Works (10,000-Foot View)

```
┌─────────────────────────────────────────────────────────┐
│  Kiro IDE                                               │
│                                                         │
│  ┌──────────────┐    ┌──────────────────────────────┐   │
│  │  Kiro Chat   │◄──►│  Agent Lattice Runtime       │   │
│  │              │    │  ┌─────────┐  ┌───────────┐  │   │
│  │  /al-dt-*    │    │  │ Steering│  │  Scripts  │  │   │
│  │  /al-impersonate  │  │  docs   │  │ (manifest,│  │   │
│  │              │    │  │         │  │  write,   │  │   │
│  └──────────────┘    │  │         │  │  roles)   │  │   │
│                      │  └─────────┘  └───────────┘  │   │
│                      └──────────┬───────────────────┘   │
│                                 │                       │
│                      ┌──────────▼───────────────────┐   │
│                      │  Modules                     │   │
│                      │  ┌────────────┐ ┌──────────┐ │   │
│                      │  │  Design    │ │  Kiro    │ │   │
│                      │  │  Thinking  │─│  Bridge  │ │   │
│                      │  └────────────┘ └──────────┘ │   │
│                      └──────────┬───────────────────┘   │
│                                 │                       │
│  ┌──────────────┐    ┌──────────▼───────────────────┐   │
│  │  Kiro        │    │  .al/output/                 │   │
│  │  Ideation    │◄───│  manifest.json, artifacts,   │   │
│  │  Extension   │    │  spec-plan.json, roles/      │   │
│  └──────────────┘    └──────────────────────────────┘   │
│                                 │                       │
│                      ┌──────────▼───────────────────┐   │
│                      │  .kiro/specs/                │   │
│                      │  Implementation-ready specs  │   │
│                      └──────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

1. The user invokes a skill in Kiro Chat (e.g., `/al-dt-workflow-empathize`)
2. The runtime loads the appropriate steering docs and workflow definition
3. The LLM follows the workflow step by step — adopting roles, producing artifacts, stopping at gates for user input
4. Scripts handle all file mutations (manifest state, artifact writing, role management)
5. The Kiro module bridges ideation output to Kiro's native spec system
6. The IDE extension watches output files and reflects progress in the sidebar

## Installer Reference

```bash
# List available modules
python3 agent-lattice/installer.py list

# Install into a project
python3 agent-lattice/installer.py install --target DIR [--modules MOD1,MOD2] [--all]

# Uninstall (preserve output artifacts)
python3 agent-lattice/installer.py uninstall --target DIR --keep-output

# Uninstall everything
python3 agent-lattice/installer.py uninstall --target DIR
```

### Installed Layout

After installation, your project looks like this:

```
your-project/
├── .kiro/
│   ├── steering/al-runtime.md       # Always-loaded runtime router
│   └── skills/                      # Kiro skill entries
│       ├── al-dt-workflow-empathize/SKILL.md
│       ├── al-dt-workflow-define/SKILL.md
│       ├── al-impersonate/SKILL.md
│       └── ...
└── .al/
    ├── runtime/                     # Steering docs, scripts, schemas
    ├── modules/                     # Installed modules
    │   ├── design-thinking/
    │   └── kiro/
    ├── output/design-thinking/      # Artifacts, manifest, dynamic roles
    └── config.json                  # Runtime + module configuration
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.

