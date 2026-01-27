#!/bin/bash
# Download sample data from the QuantConnect/Lean repository
# Provides basic equity data for backtesting sample algorithms

set -euo pipefail

DATA_DIR="${1:-./data}"

echo "Downloading Lean sample data to: $DATA_DIR"
mkdir -p "$DATA_DIR"

TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

wget -q --show-progress -O "$TMP_DIR/lean.tar.gz" \
    "https://github.com/QuantConnect/Lean/archive/refs/heads/master.tar.gz"

echo "Extracting data directory..."
tar -xzf "$TMP_DIR/lean.tar.gz" -C "$TMP_DIR" "Lean-master/Data/"
cp -r "$TMP_DIR/Lean-master/Data/"* "$DATA_DIR/"

echo "Sample data downloaded successfully to: $DATA_DIR"
echo "Contents:"
ls "$DATA_DIR/"
