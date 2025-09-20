#!/bin/bash
# Automated archive cleanup script
# Generated: 2025-09-20T21:53:50.114459

# Add this line to your crontab (crontab -e):
# 0 2 * * * cd . && python C:\repo\gonogo\tools\archive_cleanup.py --apply 2>&1 | logger -t archive_cleanup

# Or run manually:
cd .
python tools/archive_cleanup.py --apply --quiet

# For metrics only:
# python tools/archive_cleanup.py --metrics --quiet
