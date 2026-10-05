#!/usr/bin/env bash
# System libraries the PyQt6 wheel needs on Ubuntu GitHub runners.
set -euo pipefail

sudo apt-get update
packages=(
  libegl1
  libgl1
  libdbus-1-3
  libxkbcommon0
  libxkbcommon-x11-0
  libfontconfig1
  libxcb-cursor0
  libxcb-icccm4
  libxcb-image0
  libxcb-keysyms1
  libxcb-randr0
  libxcb-render-util0
  libxcb-shape0
  libnss3
  libxcomposite1
  libxrandr2
  libxi6
  libxtst6
  libxrender1
)
if apt-cache show libglib2.0-0t64 >/dev/null 2>&1; then
  packages+=(libglib2.0-0t64)
else
  packages+=(libglib2.0-0)
fi
sudo apt-get install -y --no-install-recommends "${packages[@]}"
