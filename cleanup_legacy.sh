#!/bin/bash
# Remove legacy Chainlit and unused files. Review before running.
set -e

read -p "This will delete legacy Chainlit files. Continue? [y/N] " -r
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 1
fi

rm -f launch.bat
rm -f launch_https.sh
rm -f test_alitaos.py
rm -f test_alitaos_internal.py
rm -f AUDIO_TROUBLESHOOTING.md

# Remove Chainlit app files
rm -f app/alita.py
rm -rf app/realtime
rm -rf app/.chainlit

# Remove chainlit mocks/tests
rm -rf app/scripts/test_tools

# Optional: remove chainlit-based tools if not used by Streamlit
# Uncomment after confirming Streamlit tools exist
# rm -f app/tools/browser.py app/tools/email.py app/tools/linkedin.py app/tools/database.py

# Docker references to Chainlit
rm -f Dockerfile

# Remove stray Chainlit docs
rm -f app/chainlit.md

echo "✅ Cleanup complete."
