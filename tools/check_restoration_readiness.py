#!/usr/bin/env python3
"""
Pre-restoration Readiness Check

This script verifies that all prerequisites are met before running the comprehensive
GitHub issues restoration script.

Usage:
    python tools/check_restoration_readiness.py [--repo REPO]
"""

import argparse
import json
import subprocess
import sys
from typing import List, Tuple

# Add parent directory to path for imports
sys.path.append('src')

def check_github_cli() -> Tuple[bool, str]:
    """Check if GitHub CLI is installed and authenticated."""
    try:
        # Check if gh is installed
        result = \
            subprocess.run(["gh", "--version"], capture_output=True, text=True, check=True)
        version = result.stdout.strip().split('\n')[0]

        # Check if authenticated
        result = \
            subprocess.run(["gh", "auth", "status"], capture_output=True, text=True, check=True)
        auth_info = result.stderr.strip()  # gh auth status outputs to stderr

        return True, f"✅ GitHub CLI ready: {version}"
    except subprocess.CalledProcessError as e:
        return False, f"❌ GitHub CLI issue: {e.stderr.strip()}"
    except FileNotFoundError:
        return False, "❌ GitHub CLI not found. Please install GitHub CLI (gh)"

def check_database_connection() -> Tuple[bool, str]:
    """Check database connectivity."""
    try:
        from be.database import check_database_health
        health = check_database_health()

        if health["status"] == "healthy":
            return True, f"✅ Database connection: {health['database_url']}"
        else:
            return False, f"❌ Database unhealthy: {health.get('error', 'Unknown error')}"
    except Exception as e:
        return False, f"❌ Database connection failed: {e}"

def check_repository_access(repo: str) -> Tuple[bool, str]:
    """Check if we can access the specified repository."""
    try:
        # Try to list a few issues to test access
        cmd = ["gh", "issue", "list", "--repo", repo, "--limit", "1", "--json", "number"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        issues = json.loads(result.stdout)

        return True, f"✅ Repository accessible: {repo} (found {len(issues)} sample issues)"
    except subprocess.CalledProcessError as e:
        return False, f"❌ Repository access failed: {e.stderr.strip()}"
    except Exception as e:
        return False, f"❌ Repository check error: {e}"

def check_capabilities_in_db() -> Tuple[bool, str]:
    """Check if required capabilities exist in database."""
    try:
        from be.database import get_db_session
        from be.models.traceability.capability import Capability

        session = get_db_session()
        try:
            required_caps = ["CAP-00001", "CAP-00002", "CAP-00003", "CAP-00004"]
            existing_caps = session.query(Capability.capability_id).filter(
                Capability.capability_id.in_(required_caps)
            ).all()
            existing_cap_ids = [cap[0] for cap in existing_caps]

            missing = [cap for cap in required_caps if cap not in existing_cap_ids]

            if not missing:
                return True, f"✅ All capabilities present: {', '.join(existing_cap_ids)}"
            else:
                return False, f"⚠️  Missing capabilities: {', '.join(missing)} (will be auto-created)"
        finally:
            session.close()
    except Exception as e:
        return False, f"❌ Capability check failed: {e}"

def estimate_github_api_usage(repo: str) -> Tuple[bool, str]:
    """Estimate GitHub API usage for the restoration."""
    try:
        # Get total issue count
        cmd = ["gh", "api", f"/repos/{repo}", "--jq", ".open_issues_count"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        open_issues = int(result.stdout.strip())

        # Note: This is just open issues, we need all issues including closed
        estimated_total = open_issues * 2  # Rough estimate including closed issues

        # Check rate limit status
        cmd = ["gh", "api", "/rate_limit", "--jq", ".rate.remaining"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        remaining_calls = int(result.stdout.strip())

        if remaining_calls > estimated_total + 100:  # Buffer for safety
            return True, f"✅ API quota sufficient: ~{estimated_total} issues estimated, {remaining_calls} calls remaining"
        else:
            return False, f"⚠️  API quota may be insufficient: ~{estimated_total} issues estimated, only {remaining_calls} calls remaining"

    except Exception as e:
        return False, f"⚠️  Could not check API usage: {e}"

def run_readiness_check(repo: str) -> bool:
    """Run all readiness checks."""
    print("GitHub Issues Restoration - Readiness Check")
    print("=" * 60)

    checks = [
        ("GitHub CLI Installation & Auth", lambda: check_github_cli()),
        ("Database Connection", lambda: check_database_connection()),
        ("Repository Access", lambda: check_repository_access(repo)),
        ("Required Capabilities", lambda: check_capabilities_in_db()),
        ("GitHub API Usage", lambda: estimate_github_api_usage(repo))
    ]

    all_passed = True

    for check_name, check_func in checks:
        print(f"\n{check_name}:")
        try:
            passed, message = check_func()
            print(f"  {message}")
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"  ❌ Check failed with exception: {e}")
            all_passed = False

    print("\n" + "=" * 60)

    if all_passed:
        print("🎉 All checks passed! Ready to run restoration.")
        print("\nRun the restoration with:")
        print(f"python tools/restore_github_issues_comprehensive.py --repo {repo}")
    else:
        print("⚠️  Some checks failed. Please address the issues above.")
        print("\nFor a dry run to see what would happen:")
        print(
            f"python tools/restore_github_issues_comprehensive.py"
            f"--repo {repo} --dry-run"
        )

    return all_passed

def main():
    parser = argparse.ArgumentParser(
        description="Check readiness for GitHub issues restoration"
    )
    parser.add_argument(
        "--repo",
        default="your-org/your-repo",
        help="GitHub repository in format 'owner/repo'"
    )

    args = parser.parse_args()

    success = run_readiness_check(args.repo)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()