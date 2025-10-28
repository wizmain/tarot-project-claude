#!/usr/bin/env bash
# -------------------------------------------------------------
# ai.sh — One wrapper to drive Codex CLI, Gemini CLI, Claude Code, AMP CLI
# Goal: keep "vibe coding" intent & progress sticky by auto-injecting
#       project context (INTENT/TASKS/ADR/Prompts) into every call.
# -------------------------------------------------------------
# Quick start (examples):
#   ./scripts/ai.sh -p codex  -m plan  -q "src/auth/* 리팩터링 계획 먼저"
#   ./scripts/ai.sh -p gemini -m apply -q "위 PLAN 승인됨. 단계별로 구현 시작" -f src/auth/login.ts
#   ./scripts/ai.sh -p claude -q "DIFF 보고서 생성" --model "claude-3.7-sonnet"
#   ./scripts/ai.sh -p amp    -q "테스트 실패 원인 분석" --temp 0.1
#
# NOTE: Provider commands are pluggable via environment variables:
#   CODEX_CMD (default: codex)   | GEMINI_CMD (default: gemini)
#   CLAUDE_CMD (default: claude) | AMP_CMD    (default: amp)
# If your local CLI flags differ, tweak the *_invoke() functions below.
# -------------------------------------------------------------

set -euo pipefail

# ---------- repo & paths ----------
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
LOG_DIR="$ROOT/logs/llm"
mkdir -p "$LOG_DIR"
TMP_DIR="${TMPDIR:-/tmp}"

# default context sources (change to fit your repo)
CTX_FILES=(
  "$ROOT/INTENT.md"
  "$ROOT/TASKS.md"
  "$ROOT/PROMPT_SYSTEM.md"
)
ADR_DIR="$ROOT/DECISIONS"
PROMPTS_DIR="$ROOT/prompts"
STARTER_PROMPT="$PROMPTS_DIR/engineer.starter.md"   # optional

# ---------- defaults ----------
PROVIDER="codex"         # codex | gemini | claude | amp
MODE="chat"              # chat | plan | apply
MODEL=""                 # provider default unless set
TEMP="0.2"
TOP_P="1.0"
EXTRA_CTX=()             # extra file paths
INCLUDE_FILES=()         # source files to embed (read-only snippets)
NO_ADR="0"               # 1 = skip ADR ingestion
MAX_ADR=3                # number of latest ADRs to include
DRY_RUN="0"
QUERY=""

# ---------- helpers ----------
usage() {
  cat <<'USAGE'
Usage: ai.sh -p <provider> [-m <mode>] -q "prompt" [options]

Providers:  codex | gemini | claude | amp
Modes:      chat | plan | apply

Options:
  -p, --provider <name>        Provider (default: codex)
  -m, --mode <mode>            chat | plan | apply (default: chat)
  -q, --query <text>           Your instruction/prompt
  -f, --files <paths>          Comma-separated file(s) to embed as read-only context
  -c, --context <paths>        Comma-separated extra context files
      --model <name>           Model id (provider-specific)
      --temp <float>           Temperature (default: 0.2)
      --top-p <float>          Top-p (default: 1.0)
      --no-adr                 Skip ADR ingestion
      --max-adr <n>            Number of recent ADRs to include (default: 3)
      --dry-run                Print composed context & command, do not run
  -h, --help                   Show this help

Env overrides:
  CODEX_CMD (default: codex)
  GEMINI_CMD (default: gemini)
  CLAUDE_CMD (default: claude)
  AMP_CMD   (default: amp)
USAGE
}

join_by() { local IFS="$1"; shift; echo "$*"; }

abs_or_die() {
  local p="$1"
  if [[ -e "$p" ]]; then realpath "$p"; else echo "[WARN] missing: $p" >&2; return 1; fi
}

push_if_exists() {
  local arrname="$1"; shift
  local p
  for p in "$@"; do
    if [[ -e "$p" ]]; then
      eval "$arrname+=(\"$p\")"
    fi
  done
}

# ---------- parse args ----------
while (( "$#" )); do
  case "$1" in
    -p|--provider) PROVIDER="$2"; shift 2;;
    -m|--mode) MODE="$2"; shift 2;;
    -q|--query) QUERY="$2"; shift 2;;
    -f|--files)
      IFS=',' read -r -a tmp <<< "$2"; INCLUDE_FILES+=("${tmp[@]}"); shift 2;;
    -c|--context)
      IFS=',' read -r -a tmp <<< "$2"; EXTRA_CTX+=("${tmp[@]}"); shift 2;;
    --model) MODEL="$2"; shift 2;;
    --temp)  TEMP="$2"; shift 2;;
    --top-p) TOP_P="$2"; shift 2;;
    --no-adr) NO_ADR="1"; shift;;
    --max-adr) MAX_ADR="$2"; shift 2;;
    --dry-run) DRY_RUN="1"; shift;;
    -h|--help) usage; exit 0;;
    --) shift; break;;
    *) echo "Unknown arg: $1" >&2; usage; exit 1;;
  esac
done

if [[ -z "$QUERY" ]]; then echo "[ERR] --query is required" >&2; usage; exit 1; fi

# ---------- build context blob ----------
CONTEXT_FILE="$(mktemp "$TMP_DIR/ai_ctx_XXXXXX.txt")"
{
  echo "===== CONTEXT START ($PROVIDER / $MODE) ====="

  echo "--- PROJECT: INTENT/TASKS/SYSTEM ---"
  for f in "${CTX_FILES[@]}"; do
    if [[ -f "$f" ]]; then
      echo -e "\n### $(realpath --relative-to="$ROOT" "$f")\n"; cat "$f"; fi
  done

  if [[ "$NO_ADR" != "1" && -d "$ADR_DIR" ]]; then
    echo -e "\n--- DECISIONS (latest $MAX_ADR) ---"
    # shellcheck disable=SC2012
    ls -1t "$ADR_DIR"/*.md 2>/dev/null | head -n "$MAX_ADR" | while read -r adr; do
      echo -e "\n### $(basename "$adr")\n"; sed -n '1,200p' "$adr"
    done
  fi

  if [[ -f "$STARTER_PROMPT" && "$MODE" == "plan" ]]; then
    echo -e "\n--- PLAN STARTER PROMPT ---\n"; cat "$STARTER_PROMPT"
  fi

  if (( ${#EXTRA_CTX[@]} > 0 )); then
    echo -e "\n--- EXTRA CONTEXT ---"
    for p in "${EXTRA_CTX[@]}"; do
      [[ -f "$p" ]] && { echo -e "\n### $p\n"; cat "$p"; }
    done
  fi

  if (( ${#INCLUDE_FILES[@]} > 0 )); then
    echo -e "\n--- READ-ONLY FILE SNIPPETS ---"
    for p in "${INCLUDE_FILES[@]}"; do
      [[ -f "$p" ]] && { echo -e "\n### $(realpath --relative-to="$ROOT" "$p")\n"; sed -n '1,400p' "$p"; }
    done
  fi

  echo -e "\n===== CONTEXT END ====="
} > "$CONTEXT_FILE"

# ---------- build final prompt ----------
PROMPT_FILE="$(mktemp "$TMP_DIR/ai_prompt_XXXXXX.txt")"
{
  echo "[MODE]=$MODE"
  case "$MODE" in
    plan)
      echo "You must propose a PLAN first (3~7 steps, each with expected output & test). Wait for approval before mass code changes."
      ;;
    apply)
      echo "PLAN approved. Execute step-by-step, commit-sized diffs, then output DIFF SUMMARY and TEST IMPACT."
      ;;
    *) ;;
  esac
  echo -e "\n[QUERY]"; echo "$QUERY"
} > "$PROMPT_FILE"

# ---------- providers ----------
: "${CODEX_CMD:=codex}"
: "${GEMINI_CMD:=gemini}"
: "${CLAUDE_CMD:=claude}"
: "${AMP_CMD:=amp}"

codex_invoke() {
  local cmd=("$CODEX_CMD" chat
    --temperature "$TEMP" --top-p "$TOP_P"
    --context-file "$CONTEXT_FILE" --input-file "$PROMPT_FILE")
  [[ -n "$MODEL" ]] && cmd+=(--model "$MODEL")
  echo "+ ${cmd[*]}" >&2
  "${cmd[@]}"
}

gemini_invoke() {
  # Example: a community gemini CLI; adapt flags to your tool
  local cmd=("$GEMINI_CMD" code
    --temperature "$TEMP" --top-p "$TOP_P"
    --ctx-file "$CONTEXT_FILE" --prompt-file "$PROMPT_FILE")
  [[ -n "$MODEL" ]] && cmd+=(--model "$MODEL")
  echo "+ ${cmd[*]}" >&2
  "${cmd[@]}"
}

claude_invoke() {
  local cmd=("$CLAUDE_CMD" chat
    --temperature "$TEMP"
    --system-file "$CONTEXT_FILE" --message-file "$PROMPT_FILE")
  [[ -n "$MODEL" ]] && cmd+=(--model "$MODEL")
  echo "+ ${cmd[*]}" >&2
  "${cmd[@]}"
}

amp_invoke() {
  # Placeholder for your AMP CLI (agent runner)
  local cmd=("$AMP_CMD" run
    --temp "$TEMP" --context "$CONTEXT_FILE" --prompt "$PROMPT_FILE")
  [[ -n "$MODEL" ]] && cmd+=(--model "$MODEL")
  echo "+ ${cmd[*]}" >&2
  "${cmd[@]}"
}

# ---------- dispatch ----------
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG_FILE="$LOG_DIR/${STAMP}_${PROVIDER}_${MODE}.md"

{
  echo "# $PROVIDER $MODE @ $STAMP"
  echo
  echo "## Prompt"
  sed 's/^/    /' "$PROMPT_FILE"
  echo
  echo "## Context Sources"
  for f in "${CTX_FILES[@]}"; do [[ -f "$f" ]] && echo "- $(realpath --relative-to="$ROOT" "$f")"; done
  (( ${#EXTRA_CTX[@]} > 0 )) && for f in "${EXTRA_CTX[@]}"; do echo "- $f"; done
  (( ${#INCLUDE_FILES[@]} > 0 )) && for f in "${INCLUDE_FILES[@]}"; do echo "- $(realpath --relative-to="$ROOT" "$f")"; done
  [[ "$NO_ADR" != "1" && -d "$ADR_DIR" ]] && echo "- ADR (latest $MAX_ADR) from $(realpath --relative-to="$ROOT" "$ADR_DIR")"
  echo
  echo "## Output"
} > "$LOG_FILE"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "[DRY-RUN] Context @ $CONTEXT_FILE" >&2
  echo "[DRY-RUN] Prompt  @ $PROMPT_FILE" >&2
  echo "[DRY-RUN] Log     @ $LOG_FILE" >&2
  exit 0
fi

case "$PROVIDER" in
  codex)  codex_invoke    | tee -a "$LOG_FILE" ;;
  gemini) gemini_invoke   | tee -a "$LOG_FILE" ;;
  claude) claude_invoke   | tee -a "$LOG_FILE" ;;
  amp)    amp_invoke      | tee -a "$LOG_FILE" ;;
  *) echo "[ERR] unknown provider: $PROVIDER" >&2; exit 2;;

esac

# ---------- cleanup hint ----------
echo "\n[log] saved: $LOG_FILE" >&2
# Keep $CONTEXT_FILE & $PROMPT_FILE for debugging; they are in /tmp.
