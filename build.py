#!/usr/bin/env python3
"""
Frontend Build Script for GoNoGo

Usage:
    python build.py dev      # Development build
    python build.py prod     # Production build
    python build.py watch    # Watch mode
    python build.py info     # Build info
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from fe.build import BuildManager


def main():
    if len(sys.argv) < 2:
        print("Usage: python build.py [dev|prod|watch|info]")
        print("Commands:")
        print("  dev    - Development build (no minification)")
        print("  prod   - Production build (minified, optimized)")
        print("  watch  - Watch for changes and rebuild")
        print("  info   - Show build information")
        sys.exit(1)

    manager = BuildManager()
    command = sys.argv[1]

    if command == "dev":
        result = manager.development_build()
        print("\nBuild Summary:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    elif command == "prod":
        result = manager.production_build()
        print("\nBuild Summary:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    elif command == "watch":
        manager.watch_mode()
    elif command == "info":
        info = manager.get_build_info()
        print("\nBuild Info:")
        for key, value in info.items():
            print(f"  {key}: {value}")
    else:
        print(f"Unknown command: {command}")
        print("Available commands: dev, prod, watch, info")
        sys.exit(1)


if __name__ == "__main__":
    main()
