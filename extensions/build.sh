#!/usr/bin/env bash
set -euo pipefail

EXT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="$EXT_DIR/out"

# ── Parse args ──
TARGET=""
if [ $# -gt 0 ]; then
  TARGET="$1"
fi

echo "🧹 Cleaning output directory..."
rm -rf "$OUT_DIR"
mkdir -p "$OUT_DIR"

# ── Build shared lib first ──
LIB_DIR="$EXT_DIR/openvsx-kiro"
echo ""
echo "📚 Building shared lib (openvsx-kiro)..."
echo "  Installing dependencies..."
rm -rf "$LIB_DIR/node_modules"
(cd "$LIB_DIR" && npm install --silent)
echo "  Compiling..."
(cd "$LIB_DIR" && npx tsc -p ./)

# ── Build extensions ──
echo ""
echo "📦 Building extensions..."
for ext_dir in "$EXT_DIR"/*/; do
  ext_name="$(basename "$ext_dir")"

  # Skip the shared lib, output dir, and non-extension folders
  [ "$ext_name" = "openvsx-kiro" ] && continue
  [ "$ext_name" = "out" ] && continue
  [ ! -f "$ext_dir/package.json" ] && continue

  # If a target was specified, only build that one
  if [ -n "$TARGET" ] && [ "$ext_name" != "$TARGET" ]; then
    continue
  fi

  echo "  → $ext_name"

  # Install deps (clean to avoid stale .bin symlinks)
  echo "    Installing dependencies..."
  rm -rf "$ext_dir/node_modules"
  (cd "$ext_dir" && npm install --silent)

  # Compile TypeScript
  echo "    Compiling..."
  (cd "$ext_dir" && npx tsc -p ./)

  # For extensions that depend on openvsx-kiro: replace the symlink with
  # a real copy so vsce can bundle it, then restore after packaging.
  NEEDS_RESTORE=false
  if [ -L "$ext_dir/node_modules/openvsx-kiro" ]; then
    NEEDS_RESTORE=true
    echo "    Resolving openvsx-kiro symlink..."
    LINK_TARGET="$(readlink "$ext_dir/node_modules/openvsx-kiro")"
    rm "$ext_dir/node_modules/openvsx-kiro"
    mkdir -p "$ext_dir/node_modules/openvsx-kiro"
    cp -R "$LIB_DIR/out" "$ext_dir/node_modules/openvsx-kiro/out"
    cp "$LIB_DIR/package.json" "$ext_dir/node_modules/openvsx-kiro/package.json"
  fi

  # Package with vsce
  # We already compiled, so neutralize prepublish to avoid re-compiling
  # (which would re-resolve the symlink and break the copy).
  if command -v vsce &>/dev/null; then
    echo "    Packaging..."
    cp "$ext_dir/package.json" "$ext_dir/package.json.bak"
    cp "$ext_dir/package-lock.json" "$ext_dir/package-lock.json.bak" 2>/dev/null || true
    node -e "
      const pkg = require('$ext_dir/package.json');
      if (pkg.scripts) pkg.scripts['vscode:prepublish'] = 'echo already compiled';
      if (pkg.dependencies && pkg.dependencies['openvsx-kiro']) pkg.dependencies['openvsx-kiro'] = '0.1.0';
      require('fs').writeFileSync('$ext_dir/package.json', JSON.stringify(pkg, null, 2) + '\n');
    "
    rm -f "$ext_dir/package-lock.json"
    (cd "$ext_dir" && vsce package --allow-missing-repository -o "$OUT_DIR/${ext_name}.vsix")
    mv "$ext_dir/package.json.bak" "$ext_dir/package.json"
    mv "$ext_dir/package-lock.json.bak" "$ext_dir/package-lock.json" 2>/dev/null || true
  else
    echo "    ⚠ vsce not found — install with: npm install -g @vscode/vsce"
    echo "    Skipping packaging."
  fi

  # Restore symlink
  if [ "$NEEDS_RESTORE" = true ]; then
    rm -rf "$ext_dir/node_modules/openvsx-kiro"
    ln -s "$LINK_TARGET" "$ext_dir/node_modules/openvsx-kiro"
  fi
done

echo ""
echo "✅ Build complete."
ls -la "$OUT_DIR/"*.vsix 2>/dev/null || echo "  (no .vsix files — vsce not installed)"
