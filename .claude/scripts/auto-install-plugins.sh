#!/bin/bash
# Auto-install project plugins if not present

PLUGIN_ID="achieve@claude-achieve-plugin"
INSTALLED_FILE="$HOME/.claude/plugins/installed_plugins.json"

# Check if plugin is already installed
if [[ -f "$INSTALLED_FILE" ]] && grep -q "$PLUGIN_ID" "$INSTALLED_FILE"; then
  exit 0  # Already installed
fi

# Install the plugin from GitHub marketplace
claude plugin marketplace add todorkolev/claude-achieve-plugin 2>/dev/null || true
claude plugin install achieve@claude-achieve-plugin --scope project 2>/dev/null || true
