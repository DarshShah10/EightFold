"""
Configuration and Taxonomies for GitHub Signal Extraction Engine
================================================================
Contains all classification patterns, taxonomies, and constants.
"""

# =============================================================================
# DEPENDENCY FILES TO TRACK
# =============================================================================

DEPENDENCY_FILES = [
    'requirements.txt', 'package.json', 'Cargo.toml', 'go.mod', 'pyproject.toml',
    'Pipfile', 'Gemfile', 'composer.json', 'pom.xml', 'build.gradle',
    'Cargo.lock', 'package-lock.json', 'yarn.lock', 'poetry.lock',
    'setup.py', 'setup.cfg', 'Pipfile.lock', 'vendor/', 'src/requirements.txt',
    'environment.yml', 'uv.lock', 'mix.exs'
]

# =============================================================================
# REPOSITORY STRUCTURE PATTERNS
# =============================================================================

STRUCTURE_PATTERNS = {
    'has_tests': [
        'test/', 'tests/', 'Test/', 'Tests/', '_test/', '__test__/',
        'spec/', 'Spec/', '__specs__/', '.test.', '.tests.', '_spec.'
    ],
    'has_docs': [
        'docs/', 'doc/', 'Documentation/', 'README.md', 'readme.md',
        'docs/README', 'API.md', 'CHANGELOG.md', 'CONTRIBUTING.md'
    ],
    'has_ci': [
        '.github/workflows/', '.circleci/', '.travis.yml', 'Jenkinsfile',
        'azure-pipelines.yml', '.gitlab-ci.yml', 'buildkite/', '.buildkite/'
    ],
    'has_dockerfile': [
        'Dockerfile', 'docker-compose.yml', 'Dockerfile.dev',
        'Dockerfile.prod', '.dockerignore', 'docker-entrypoint.sh'
    ],
    'has_makefile': [
        'Makefile', 'makefile', 'GNUMakefile', 'Rakefile', 'Taskfile.yml'
    ],
    'has_readme': [
        'README.md', 'README.rst', 'README.txt', 'README', 'readme.md'
    ],
    'has_license': [
        'LICENSE', 'LICENSE.txt', 'LICENSE.md', 'COPYING', 'COPYING.txt'
    ],
    'has_contributing': [
        'CONTRIBUTING.md', 'CONTRIBUTING.rst', '.github/CONTRIBUTING.md'
    ],
    'has_security': [
        'SECURITY.md', 'security.md', '.github/SECURITY.md', 'SECURITY.txt'
    ],
    'has_dependabot': [
        '.github/dependabot.yml', '.github/dependabot.yaml', 'dependabot.yml'
    ],
}

# =============================================================================
# LANGUAGE TO SKILL DOMAIN MAPPING
# =============================================================================

LANGUAGE_DOMAINS = {
    'Python': ['Data Science', 'Backend', 'ML/AI', 'Scripting'],
    'JavaScript': ['Frontend', 'Web', 'Fullstack'],
    'TypeScript': ['Frontend', 'Web', 'Fullstack', 'Type-Safe'],
    'Java': ['Backend', 'Enterprise', 'Android'],
    'C#': ['Backend', 'Game Dev', 'Windows'],
    'C++': ['Systems', 'Embedded', 'Game Dev', 'Performance'],
    'C': ['Systems', 'Embedded', 'Low-Level'],
    'Rust': ['Systems', 'Performance', 'WebAssembly'],
    'Go': ['Backend', 'Cloud', 'DevOps', 'Microservices'],
    'Swift': ['iOS', 'macOS', 'Apple Ecosystem'],
    'Kotlin': ['Android', 'Backend', 'JVM'],
    'Ruby': ['Backend', 'Web', 'DevOps'],
    'PHP': ['Web', 'Backend'],
    'Scala': ['Big Data', 'JVM', 'Functional'],
    'R': ['Data Science', 'Statistics'],
    'Julia': ['Scientific Computing', 'High Performance'],
    'Dart': ['Mobile', 'Flutter', 'Cross-Platform'],
    'Shell': ['DevOps', 'System Admin', 'Scripting'],
    'Haskell': ['Functional', 'Compilers', 'Type Theory'],
    'Elixir': ['Functional', 'Distributed', 'BEAM'],
}

# =============================================================================
# COMMIT MESSAGE CLASSIFICATION PATTERNS
# =============================================================================

COMMIT_PATTERNS = {
    'feat': r'(feat|feature|implement|add|introduce|create|new)',
    'fix': r'(fix|bugfix|hotfix|patch|resolve|bug|issue)',
    'refactor': r'(refactor|restructure|reorganize|cleanup|clean|simplify)',
    'docs': r'(docs?|documentation|readme|changelog)',
    'test': r'(test|spec|coverage|unittest|testsuite)',
    'perf': r'(perf|optimize|performance|speed|efficiency)',
    'chore': r'(chore|maintain|update|upgrade|bump|deps|dependencies)',
    'security': r'(security|secur|cve|vuln|auth)',
    'ci': r'(^ci|\bci\b|cd|pipeline|workflow|github action|travis|jenkins)',
    'revert': r'(revert|undo|backout)',
}

# =============================================================================
# HARVEST CONFIGURATION
# =============================================================================

# Default limits for data collection
DEFAULTS = {
    'max_commits_per_repo': 30,
    'max_prs_per_repo': 15,
    'max_issues_per_repo': 15,
    'max_events': 200,
    'max_starred': 100,
    'max_gists': 20,
    'max_branches_per_repo': 20,
    'max_releases_per_repo': 10,
    'max_top_repos': 10,  # For deep analysis
    'min_rate_limit_remaining': 10,
}
