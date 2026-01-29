#!/bin/bash
# Auto-install project plugins if not present

PLUGIN_ID="achieve@lean-playground"
INSTALLED_FILE="$HOME/.claude/plugins/installed_plugins.json"

# Check if plugin is already installed
if [[ -f "$INSTALLED_FILE" ]] && grep -q "$PLUGIN_ID" "$INSTALLED_FILE"; then
  exit 0  # Already installed
fi

# Install the plugin
cd /workspaces/lean-playground
claude plugin marketplace add ./ 2>/dev/null || true
claude plugin install achieve@lean-playground --scope project 2>/dev/null || true
