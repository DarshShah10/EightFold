"""
Environment Setup Script for GitHub Signal Extraction Engine
=========================================================
Run this script to set up the environment and configure your GitHub token.
"""

import os
import sys


def setup_environment():
    """Guide user through environment setup."""

    print("=" * 60)
    print("GitHub Signal Extraction Engine - Environment Setup")
    print("=" * 60)

    # Check Python version
    print(f"\nPython version: {sys.version}")
    if sys.version_info < (3, 9):
        print("Python 3.9+ required!")
        return False
    print("Python version OK")

    # Check if required packages are installed
    print("\nChecking dependencies...")
    required_packages = {
        'github': 'PyGithub',
        'radon': 'radon',
        'numpy': 'numpy',
        'pandas': 'pandas',
        'toml': 'toml',
    }

    missing = []
    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"   {package_name}")
        except ImportError:
            print(f"   {package_name} - NOT INSTALLED")
            missing.append(package_name)

    if missing:
        print(f"\n Missing packages: {', '.join(missing)}")
        print("\nRun this to install:")
        print(f"  pip install {' '.join(missing)}")
        print("\nOr run: pip install -r requirements.txt")
        return False

    # Check GitHub token
    print("\n" + "-" * 60)
    print("GitHub Token Setup")
    print("-" * 60)

    token = os.environ.get('GITHUB_TOKEN')

    if token:
        print("GITHUB_TOKEN is set")
        print(f"  Token preview: {token[:4]}...{token[-4:]}")
    else:
        print("GITHUB_TOKEN is NOT set")
        print("\nHow to get a GitHub token:")
        print("  1. Go to: https://github.com/settings/tokens")
        print("  2. Click 'Generate new token (classic)'")
        print("  3. Give it a name like 'talent-intelligence'")
        print("  4. Select scopes: 'repo' (full control), 'read:user', 'read:org'")
        print("  5. Click 'Generate token'")
        print("  6. COPY the token (you won't see it again!)")
        print("\nHow to set the token:")

        if sys.platform == "win32":
            print("\nWindows (PowerShell) - Session only:")
            print('  $env:GITHUB_TOKEN = "ghp_your_token_here"')
            print("\nWindows (PowerShell) - Permanent:")
            print("  [System.Environment]::SetEnvironmentVariable('GITHUB_TOKEN', 'your_token', 'User')")
        else:
            print("\nmacOS/Linux - Session only:")
            print('  export GITHUB_TOKEN="ghp_your_token_here"')
            print("\nmacOS/Linux - Permanent (add to ~/.bashrc or ~/.zshrc):")
            print('  echo \'export GITHUB_TOKEN="ghp_your_token_here"\' >> ~/.bashrc')
            print('  source ~/.bashrc')

    print("\n" + "=" * 60)
    print("Setup check complete!")
    print("=" * 60)

    return token is not None


def test_github_connection():
    """Test GitHub API connection."""
    print("\n" + "=" * 60)
    print("Testing GitHub Connection")
    print("=" * 60)

    try:
        from github import Github

        token = os.environ.get('GITHUB_TOKEN')
        if token:
            g = Github(token)
            user = g.get_user()
            print(f"\nAuthenticated as: @{user.login}")
            print(f"  Name: {user.name}")
            print(f"  Followers: {user.followers}")
            print(f"  Public Repos: {user.public_repos}")

            # Check rate limit
            rate = g.get_rate_limit()
            if hasattr(rate, 'core'):
                core = rate.core
                print(f"\nAPI Rate Limit Status:")
                print(f"  Remaining: {core.remaining}")
                print(f"  Limit: {core.limit}")
                print(f"  Resets at: {core.reset}")
        else:
            g = Github()
            print("\nUsing unauthenticated access (rate limited)")
            print("Set GITHUB_TOKEN for full access")

            rate = g.get_rate_limit()
            if hasattr(rate, 'core'):
                core = rate.core
                print(f"\nRate Limit Status:")
                print(f"  Remaining: {core.remaining}")
                print(f"  Limit: {core.limit}")

        return True

    except Exception as e:
        print(f"\nConnection failed: {e}")
        return False


def install_dependencies():
    """Install required dependencies."""
    print("\n" + "=" * 60)
    print("Installing Dependencies")
    print("=" * 60)

    import subprocess

    packages = [
        'PyGithub>=1.59.0',
        'radon>=6.0.1',
        'numpy>=1.24.0',
        'pandas>=2.0.0',
        'toml>=0.10.2',
        'requests>=2.31.0',
    ]

    for pkg in packages:
        print(f"Installing {pkg}...")
        try:
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', pkg],
                check=True,
                capture_output=True
            )
            print(f"  {pkg} installed")
        except subprocess.CalledProcessError as e:
            print(f"  Failed to install {pkg}")
            print(f"     Run manually: pip install {pkg}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Setup GitHub Signal Extraction Engine")
    parser.add_argument('--install', action='store_true', help='Install dependencies')
    parser.add_argument('--test', action='store_true', help='Test GitHub connection')
    parser.add_argument('--full', action='store_true', help='Run full setup')

    args = parser.parse_args()

    if args.full:
        install_dependencies()
        setup_environment()
        test_github_connection()
    elif args.install:
        install_dependencies()
    elif args.test:
        test_github_connection()
    else:
        setup_environment()
        test_github_connection()