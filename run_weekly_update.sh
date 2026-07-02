#!/bin/bash
# Electoral Dashboard — Weekly Auto-Updater
# Runs every Monday at 8:00 AM via cron
# Logs output to: ~/Documents/Claude/Projects/Electoral Dashboard/update_log.txt

SCRIPT_DIR="$HOME/Documents/Claude/Projects/Electoral Dashboard"
LOG_FILE="$SCRIPT_DIR/update_log.txt"
PYTHON=$(which python3)

echo "======================================" >> "$LOG_FILE"
echo "Run started: $(date)" >> "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"

# Load environment (picks up GOOGLE_CREDENTIALS from .zshrc)
source "$HOME/.zshrc" 2>/dev/null || source "$HOME/.bash_profile" 2>/dev/null

# Run the updater
cd "$SCRIPT_DIR" && \
  GOOGLE_CREDENTIALS="$(base64 -i "$SCRIPT_DIR/service_account.json")" \
  $PYTHON "$SCRIPT_DIR/update_sheet.py" \
  --sheet-id 1THi4cJ8BQNTFjgBhE3myc_F6SvAS0MrqUJ-gpLTmIqA \
  >> "$LOG_FILE" 2>&1

# Apply any pending Constants patch (written by Claude during the weekly briefing)
cd "$SCRIPT_DIR" && \
  GOOGLE_CREDENTIALS="$(base64 -i "$SCRIPT_DIR/service_account.json")" \
  $PYTHON "$SCRIPT_DIR/apply_constants_patch.py" \
  --sheet-id 1THi4cJ8BQNTFjgBhE3myc_F6SvAS0MrqUJ-gpLTmIqA \
  >> "$LOG_FILE" 2>&1

echo "Run finished: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
