#!/bin/bash
# K4H818 utilities installer for ASL3
#
# Fetch and run:
#   wget -O - https://raw.githubusercontent.com/Kits4Hams/K4H818_utilities/main/install_asl3.sh | bash
#
# Deliberately NOT run under sudo at the top level -- installing into the
# user's own home directory needs no elevated privilege at all. sudo is
# used internally, only for the one command that genuinely needs root
# (installing avrdude). Running the whole script as root would make a
# naive use of $HOME resolve to root's home, not the real user's.

set -e

INSTALL_DIR="$HOME"
GITHUB_BASE="https://raw.githubusercontent.com/Kits4Hams/K4H818_utilities/main"

echo "Installing K4H818 utilities to $INSTALL_DIR ..."

# avrdude: install only if missing. Not our package to keep current --
# that's apt's job (apt upgrade), not this installer's.
if command -v avrdude >/dev/null 2>&1; then
    echo "avrdude already installed, skipping."
else
    echo "avrdude not found -- installing (will prompt for your password)..."
    sudo apt-get update
    sudo apt-get install -y avrdude
fi

# K4H818-prog.py and K4H818-update.py: always fetched fresh and
# overwritten, every run -- no version check needed. Re-running this
# same installer later is exactly how these two stay up to date.
echo "Fetching K4H818-prog.py ..."
wget -q -O "$INSTALL_DIR/K4H818-prog.py" "$GITHUB_BASE/K4H818-prog.py"
chmod +x "$INSTALL_DIR/K4H818-prog.py"

echo "Fetching K4H818-update.py ..."
wget -q -O "$INSTALL_DIR/K4H818-update.py" "$GITHUB_BASE/K4H818-update.py"
chmod +x "$INSTALL_DIR/K4H818-update.py"

echo ""
echo "Done. Run with:"
echo "  $INSTALL_DIR/K4H818-prog.py"
echo "  $INSTALL_DIR/K4H818-update.py"
echo ""
echo "Re-run this same installer any time to update both to the latest"
echo "version and re-check avrdude."
