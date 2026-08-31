#!/bin/bash
# K4H818 installer stub for HamVOIP. Bundled directly into the
# distribution image -- deliberately contains no real logic of its own,
# so it never needs to be updated. Just fetches and runs the real,
# current installer from GitHub every time it's run. Re-run this same
# stub any time to update K4H818-prog/K4H818-update to whatever's
# current.
wget -O - https://raw.githubusercontent.com/Kits4Hams/K4H818_utilities/main/install_hamvoip.sh | bash
