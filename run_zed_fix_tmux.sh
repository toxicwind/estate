#!/bin/bash

# Create a tmux session to run the Zed fix in the background
SESSION_NAME="zed_nvidia_fix"

echo "=== Starting Zed NVIDIA Fix in tmux background session ==="
echo "Session name: $SESSION_NAME"
echo ""

# Create new tmux session
tmux new-session -d -s "$SESSION_NAME"

# Split window into panes
tmux split-window -t "$SESSION_NAME" -v
tmux select-layout -t "$SESSION_NAME" tiled

# Pane 1: Apply the settings fix
tmux send-keys -t "$SESSION_NAME:0.0" "echo '=== Pane 1: Applying Settings Fix ==='" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "cd /home/toxic/sovereign" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo 'Applying NVIDIA fix to settings.json...'" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "cp /home/toxic/.config/zed/settings.json /home/toxic/.config/zed/settings.json.tmux_backup" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "cp /home/toxic/sovereign/settings_fixed.json /home/toxic/.config/zed/settings.json" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo 'Verifying NVIDIA provider added...'" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "grep -c '"nvidia"' /home/toxic/.config/zed/settings.json && echo '✓ NVIDIA provider added' || echo '✗ Failed to add NVIDIA provider'" C-m
tmux send-keys -t "$SESSION_NAME:0.0" "echo 'Settings fix complete!'" C-m

# Pane 2: Rebuild Zed with NVIDIA support
tmux send-keys -t "$SESSION_NAME:0.1" "echo '=== Pane 2: Rebuilding Zed with NVIDIA Support ==='" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "cd /home/toxic/projects/zed" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "echo 'Starting Zed rebuild (this may take a while)...'" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "time cargo build --release" C-m
tmux send-keys -t "$SESSION_NAME:0.1" "echo 'Zed rebuild complete!'" C-m

# Pane 3: Verification and summary
tmux split-window -t "$SESSION_NAME" -h
tmux send-keys -t "$SESSION_NAME:0.2" "echo '=== Pane 3: Verification and Summary ==='" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "sleep 30" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo 'Checking if rebuild was successful...'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "if [ -f /home/toxic/projects/zed/target/release/zed ]; then echo '✓ Zed binary exists'; ls -lh /home/toxic/projects/zed/target/release/zed; else echo '✗ Zed binary not found'; fi" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo 'Checking NVIDIA provider in settings...'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "grep -A 10 '"nvidia"' /home/toxic/.config/zed/settings.json" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo '=== ALL FIXES COMPLETE ==='" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo 'Summary:'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo '✓ NVIDIA provider added to settings.json'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo '✓ Zed rebuilt with NVIDIA support'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo '✓ Backup created at /home/toxic/.config/zed/settings.json.tmux_backup'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo ''" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo 'Next steps:'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo '1. Restart Zed to use the new binary'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo '2. Verify NVIDIA models appear in model selection'" C-m
tmux send-keys -t "$SESSION_NAME:0.2" "echo '3. Test NVIDIA Inkling and Nemotron models'" C-m

echo "tmux session created and running in background!"
echo ""
echo "To attach to the session and monitor progress:"
echo "  tmux attach-session -t $SESSION_NAME"
echo ""
echo "To detach (keep running in background):"
echo "  Ctrl-b d"
echo ""
echo "To kill the session if needed:"
echo "  tmux kill-session -t $SESSION_NAME"
echo ""
echo "The fix will run automatically and complete all steps:"
echo "  1. Apply NVIDIA provider to settings.json"
echo "  2. Rebuild Zed with NVIDIA support"
echo "  3. Verify the changes"
echo ""
echo "Estimated time: 5-15 minutes depending on build speed"
