#!/bin/bash
# K4H818 utilities installer for HamVOIP
#
# Fetch and run:
#   wget -O - https://raw.githubusercontent.com/Kits4Hams/K4H818_utilities/main/install_hamvoip.sh | bash
#
# HamVOIP's shell is already root -- no sudo needed anywhere here.

set -e

INSTALL_DIR="/usr/local/sbin"
GITHUB_BASE="https://raw.githubusercontent.com/Kits4Hams/K4H818_utilities/main"

echo "Installing K4H818 utilities to $INSTALL_DIR ..."

# avrdude: install only if missing. Not our package to keep current.
if command -v avrdude >/dev/null 2>&1; then
    echo "avrdude already installed, skipping."
else
    echo "avrdude not found -- installing..."
    pacman -Sy --noconfirm avrdude
fi

# K4H818-prog and K4H818-update: always fetched fresh and overwritten,
# every run -- no version check needed. Fetched from GitHub under their
# real .py names, but saved locally WITHOUT an extension, matching
# HamVOIP's confirmed convention (files run as bare commands, no
# implicit extension resolution the way Windows sometimes does).
echo "Fetching K4H818-prog ..."
wget -q -O "$INSTALL_DIR/K4H818-prog" "$GITHUB_BASE/K4H818-prog.py"
chmod +x "$INSTALL_DIR/K4H818-prog"

echo "Fetching K4H818-update ..."
wget -q -O "$INSTALL_DIR/K4H818-update" "$GITHUB_BASE/K4H818-update.py"
chmod +x "$INSTALL_DIR/K4H818-update"

echo ""
echo "Done. Run with:"
echo "  K4H818-prog"
echo "  K4H818-update"
echo ""
echo "Re-run this same installer any time to update both to the latest"
echo "version and re-check avrdude."
