#!/bin/sh
# NBD Video for macOS (Apple Silicon): starts the plugin with an official standalone Python build. Plain text, nothing compiled: read it.
# First run: download Python (python-build-standalone, the build uv uses), check its SHA-256, unpack it next to the plugin's data.
# Every run: start bootstrap.py (also plain text, the same file as on Windows), which speaks MCP to Claude Code or Codex and
# fetches the engine for a valid key.
# Nothing may be printed on stdout: it is the channel to the AI client. Messages go to stderr.
set -u
POINTER="$HOME/Library/Application Support/ClickVideo/plugin-data.txt"  # written by bootstrap.py: for click-engine run in a terminal
if [ -z "${CLAUDE_PLUGIN_DATA:-}${PLUGIN_DATA:-}" ] && [ -f "$POINTER" ]; then CLAUDE_PLUGIN_DATA="$(cat "$POINTER")"; export CLAUDE_PLUGIN_DATA; fi
D="${CLAUDE_PLUGIN_DATA:-${PLUGIN_DATA:-$HOME/Library/Application Support/ClickVideo}}"
case "$D" in '${'*) D="$HOME/Library/Application Support/ClickVideo" ;; esac
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="$D/runtime/bin/python3"

# The customer moved the heavy data to another disk (tool chon_thu_muc_du_lieu): Python was copied there and linked as runtime.next
# while it was running. Swap it in now; bootstrap.py deletes runtime.old.
if [ -x "$D/runtime.next/bin/python3" ]; then
  if [ -e "$D/runtime" ] || [ -L "$D/runtime" ]; then mv "$D/runtime" "$D/runtime.old" 2>/dev/null; fi
  [ -e "$D/runtime" ] || mv "$D/runtime.next" "$D/runtime" 2>/dev/null
fi

if [ ! -x "$PY" ]; then
  URL="https://github.com/astral-sh/python-build-standalone/releases/download/20261026/cpython-3.12.16%2B20261026-aarch64-apple-darwin-install_only.tar.gz"
  SHA="fbf4afef53c2a6b72bb741bc06d5671a9dfaf87bd84e5aa73ac9b3d0d589f14e"
  if [ "$(/usr/bin/uname -m)" != "arm64" ]; then
    echo "CLICK: ban cho Mac can chip Apple M (M1 tro len)" >&2; exit 1
  fi
  mkdir -p "$D/cache" || { echo "CLICK: khong tao duoc thu muc du lieu" >&2; exit 1; }
  cd "$D/cache" || exit 1
  /usr/bin/curl -sSfL --retry 3 -o python-mac.tar.gz "$URL" >/dev/null 2>&1 || { echo "CLICK: khong tai duoc Python" >&2; exit 1; }
  GOT="$(/usr/bin/shasum -a 256 python-mac.tar.gz | /usr/bin/cut -d' ' -f1)"
  if [ "$GOT" != "$SHA" ]; then
    rm -f python-mac.tar.gz; echo "CLICK: ma kiem tra cua Python khong khop, da xoa tep tai ve" >&2; exit 1
  fi
  # unpacked aside, then moved in one step: a second window starting at the same time never sees half a Python
  rm -rf "$D/runtime.part" && mkdir -p "$D/runtime.part"
  /usr/bin/tar -xzf python-mac.tar.gz -C "$D/runtime.part" --strip-components 1 >/dev/null 2>&1 || { echo "CLICK: khong giai nen duoc Python" >&2; exit 1; }
  rm -f python-mac.tar.gz
  [ -x "$PY" ] || mv "$D/runtime.part" "$D/runtime"
  rm -rf "$D/runtime.part"
  cd "$HERE" || exit 1
fi

exec "$PY" -I -X utf8 "$HERE/bootstrap.py" "$@"
