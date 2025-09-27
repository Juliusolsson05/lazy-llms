"""Utility functions for PM MCP Server with all fixes applied"""
import re
import asyncio
import subprocess
import json
import os
import functools
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable, TypeVar, cast
from slugify import slugify
from config import Config

T = TypeVar("T")

def now_iso() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def safe_json(value, default):
    """Safely parse JSON with fallback"""
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default

def safe_json_loads(val, default=None):
    """Parse JSON safely with default fallback - compatibility version"""
    if default is None:
        default = {}
    if val is None:
        return default
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except Exception:
        return default

def _path_is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False

def resolve_project_id_from_env_or_cwd(PMDatabase) -> Optional[str]:
    """
    Auto-scope: prefer explicit env var, else detect by current working directory.
    Returns matching project_id or None if not found.
    """
    # 1) Explicit override
    env_pid = os.getenv("PM_DEFAULT_PROJECT_ID")
    if env_pid:
        proj = PMDatabase.get_project(env_pid)
        if proj is not None:
            return env_pid

    # 2) CWD match (including submodules)
    cwd = Path.cwd()
    for p in PMDatabase.get_all_projects():  # returns *models*
        try:
            project_path = Path(p.absolute_path)
        except Exception:
            continue
        if cwd == project_path or _path_is_within(cwd, project_path):
            return p.project_id
    return None

class ScopeError(Exception):
    pass

def strict_project_scope(tool_fn: Callable[..., T]) -> Callable[..., T]:
    """
    HARD rule:
    - Resolve project_id from CWD (or PM_DEFAULT_PROJECT_ID)
    - Inject it into input.project_id
    - If input.project_id is present and differs → error
    - If cannot resolve → error
    """
    @functools.wraps(tool_fn)
    def wrapper(*args, **kwargs):
        input_obj = kwargs.get("input")
        if input_obj is None and len(args) >= 2:
            input_obj = args[1]
        from database import PMDatabase  # local import to avoid cycles
        resolved = resolve_project_id_from_env_or_cwd(PMDatabase)
        if not resolved:
            raise ScopeError("No project scope: run inside a registered project or set PM_DEFAULT_PROJECT_ID.")
        if hasattr(input_obj, "project_id"):
            passed = getattr(input_obj, "project_id")
            if passed and passed != resolved:
                raise ScopeError(f"Project scope mismatch. Resolved={resolved}, Passed={passed}.")
            setattr(input_obj, "project_id", resolved)
        return cast(T, tool_fn(*args, **kwargs))
    return wrapper

def assert_issue_in_scope(issue_project_id: Optional[str], scoped_project_id: str) -> None:
    if not issue_project_id or issue_project_id != scoped_project_id:
        raise ScopeError("Issue does not belong to the current project scope.")

def ok(message: str, data: Optional[Dict[str, Any]] = None, hints: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create success response"""
    return {
        "success": True,
        "message": message,
        "data": data or {},
        "hints": hints or [],
        "timestamp": now_iso(),
    }

def err(message: str, details: Optional[Dict[str, Any]] = None, hints: Optional[List[str]] = None) -> Dict[str, Any]:
    """Create error response"""
    return {
        "success": False,
        "message": message,
        "data": {"error_details": details or {}},
        "hints": hints or [],
        "timestamp": now_iso(),
    }

def run_git(repo_path: str, args: List[str]) -> Dict[str, Any]:
    """Run git command with security allowlist"""
    # Very conservative allowlist
    allow = {"status", "rev-parse", "branch", "push", "config", "checkout", "add", "commit", "remote", "pull", "log", "init"}
    if not args:
        return {"rc": 1, "out": "", "err": "No git args"}
    if args[0] not in allow:
        return {"rc": 1, "out": "", "err": f"git subcommand not allowed: {args[0]}"}
    cmd = ["git"] + args
    try:
        proc = subprocess.run(cmd, cwd=repo_path, capture_output=True, text=True, timeout=15)
        return {"rc": proc.returncode, "out": proc.stdout.strip(), "err": proc.stderr.strip()}
    except Exception as e:
        return {"rc": 1, "out": "", "err": str(e)}

def sanitize_path(p: str) -> str:
    """Avoid directory traversal; keep as repo-local hints"""
    return os.path.normpath("/" + p).lstrip("/")

def generate_issue_key(project_slug: str, existing_count: int) -> str:
    """Generate issue key with proper collision handling"""
    prefix = project_slug.upper()[:4].replace('-', '')
    if not prefix:
        prefix = "PROJ"

    # Use date-based format for uniqueness
    date_part = datetime.now().strftime("%Y%m")

    # Add 1 to existing count to get next number
    return f"{prefix}-{date_part}-{existing_count + 1:03d}"

def generate_branch_name(issue_key: str, issue_type: str, title: str) -> str:
    """Generate git branch name from issue details"""
    type_map = {
        "feature": "feat",
        "bug": "fix",
        "refactor": "refactor",
        "chore": "chore",
        "spike": "spike"
    }

    type_prefix = type_map.get(issue_type, "feat")
    title_slug = slugify(title)[:40]

    return f"{type_prefix}/{issue_key.lower()}-{title_slug}"

def format_commit_message(issue_key: str, message: str) -> str:
    """
    Format commit message with PM trailers - FIXED REGEX VERSION
    Handles conventional commit format properly including scopes
    """
    # Fixed regex that properly handles scopes like feat(api):
    cc_pattern = r'^(?P<type>feat|fix|docs|style|refactor|test|chore)(?P<scope>\([^)]+\))?:\s*(?P<rest>.*)'
    match = re.match(cc_pattern, message, re.DOTALL)

    if match:
        # Insert preamble properly
        type_part = match.group('type')
        scope_part = match.group('scope') or ''
        rest_part = match.group('rest')
        message = f"{type_part}{scope_part}: [pm {issue_key}] {rest_part}".strip()
    else:
        # Prepend preamble
        message = f"[pm {issue_key}] {message}"

    # Add trailer if not present
    trailer = f"\n\nPM: {issue_key}"
    if trailer not in message:
        message += trailer

    return message

def parse_timeframe(timeframe: str) -> timedelta:
    """Parse timeframe string to timedelta with decimal support"""
    match = re.match(r'^(\d+(?:\.\d+)?)([dwmh])$', timeframe.lower())
    if not match:
        return timedelta(weeks=1)

    value = float(match.group(1))  # Support decimals
    unit = match.group(2)

    if unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    elif unit == 'w':
        return timedelta(weeks=value)
    elif unit == 'm':
        return timedelta(days=value * 30)
    else:
        return timedelta(weeks=1)

def parse_duration(duration: str) -> float:
    """Parse duration string to hours with decimal support"""
    if not duration:
        return 0.0

    # Handle formats like "2h", "30m", "1.5d", "2.5h"
    match = re.match(r'^(\d+(?:\.\d+)?)([hmd])$', duration.lower())
    if not match:
        return 0.0

    value = float(match.group(1))  # Support decimals
    unit = match.group(2)

    if unit == 'm':
        return value / 60
    elif unit == 'h':
        return value
    elif unit == 'd':
        return value * 8  # 8-hour workday
    else:
        return 0.0

async def run_git_command_async(args: List[str], cwd: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run git command asynchronously with proper security and error handling
    """
    # Security: validate git command
    if not args or args[0] not in Config.ALLOWED_GIT_COMMANDS:
        return {
            'success': False,
            'output': '',
            'error': f'Git command not allowed: {args[0] if args else "empty"}'
        }

    # Security: sanitize working directory
    if cwd:
        try:
            cwd = Path(cwd).resolve()
            if not cwd.exists() or not cwd.is_dir():
                return {
                    'success': False,
                    'output': '',
                    'error': 'Invalid working directory'
                }
        except Exception:
            return {
                'success': False,
                'output': '',
                'error': 'Invalid working directory path'
            }

    try:
        # Run command asynchronously to avoid blocking
        process = await asyncio.create_subprocess_exec(
            'git', *args,
            cwd=str(cwd) if cwd else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await process.communicate()

        return {
            'success': process.returncode == 0,
            'output': stdout.decode().strip(),
            'error': stderr.decode().strip() if process.returncode != 0 else None
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': f'Command execution failed: {type(e).__name__}'  # Don't expose details
        }

def run_git_command_sync(args: List[str], cwd: Optional[Path] = None) -> Dict[str, Any]:
    """
    Synchronous version for non-async contexts with security
    """
    # Security: validate git command
    if not args or args[0] not in Config.ALLOWED_GIT_COMMANDS:
        return {
            'success': False,
            'output': '',
            'error': f'Git command not allowed: {args[0] if args else "empty"}'
        }

    try:
        result = subprocess.run(
            ['git'] + args,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            timeout=30,  # Prevent hanging
            check=False
        )

        return {
            'success': result.returncode == 0,
            'output': result.stdout.strip(),
            'error': result.stderr.strip() if result.returncode != 0 else None
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '',
            'error': 'Git command timed out'
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': f'Command execution failed: {type(e).__name__}'
        }

async def setup_git_identity(project_path: Path) -> bool:
    """Setup git identity for commits with security"""
    try:
        # Set user name
        result = await run_git_command_async(
            ['config', 'user.name', Config.GIT_USER_NAME],
            cwd=project_path
        )
        if not result['success']:
            return False

        # Set user email
        result = await run_git_command_async(
            ['config', 'user.email', Config.GIT_USER_EMAIL],
            cwd=project_path
        )
        return result['success']
    except Exception:
        return False

def calculate_velocity(completed_issues: List[Dict[str, Any]],
                      timeframe_days: int = 7) -> Dict[str, Any]:
    """Calculate velocity metrics with better error handling"""
    if not completed_issues:
        return {
            'issues_per_day': 0.0,
            'story_points_per_week': 0.0,
            'average_cycle_time_hours': 0.0,
            'note': 'No completed issues in dataset'
        }

    try:
        # Count issues completed in timeframe
        cutoff = datetime.utcnow() - timedelta(days=timeframe_days)
        recent_issues = []

        for issue in completed_issues:
            try:
                updated_str = issue['updated_utc'].rstrip('Z')
                updated_dt = datetime.fromisoformat(updated_str)
                if updated_dt > cutoff:
                    recent_issues.append(issue)
            except (ValueError, KeyError):
                continue  # Skip invalid dates

        issues_per_day = len(recent_issues) / max(timeframe_days, 1)

        # Calculate average cycle time
        cycle_times = []
        for issue in recent_issues:
            try:
                created = datetime.fromisoformat(issue['created_utc'].rstrip('Z'))
                completed = datetime.fromisoformat(issue['updated_utc'].rstrip('Z'))
                cycle_hours = (completed - created).total_seconds() / 3600
                if cycle_hours > 0:  # Sanity check
                    cycle_times.append(cycle_hours)
            except (ValueError, KeyError):
                continue

        avg_cycle_time = sum(cycle_times) / len(cycle_times) if cycle_times else 0

        return {
            'issues_per_day': round(issues_per_day, 2),
            'story_points_per_week': round(issues_per_day * 7 * 3, 1),  # Heuristic estimate
            'average_cycle_time_hours': round(avg_cycle_time, 1),
            'completed_this_period': len(recent_issues),
            'total_completed': len(completed_issues),
            'note': 'story_points_per_week is heuristic (3 points per issue average)'
        }
    except Exception as e:
        return {
            'issues_per_day': 0.0,
            'story_points_per_week': 0.0,
            'average_cycle_time_hours': 0.0,
            'error': f'Velocity calculation failed: {type(e).__name__}'
        }

def format_standup_report(yesterday_work: List[Dict[str, Any]],
                         today_plan: List[Dict[str, Any]],
                         blockers: List[Dict[str, Any]]) -> str:
    """Format daily standup report with rich context"""
    report = "# Daily Standup Report\n\n"
    report += f"**Date:** {datetime.now().strftime('%Y-%m-%d')}\n\n"

    report += "## Yesterday's Progress\n"
    if yesterday_work:
        for work in yesterday_work[:5]:  # Limit to prevent spam
            report += f"- **{work.get('issue_key', 'UNKNOWN')}**: {work.get('summary', 'No summary')}\n"
        if len(yesterday_work) > 5:
            report += f"- ... and {len(yesterday_work) - 5} more activities\n"
    else:
        report += "- No logged work yesterday\n"

    report += "\n## Today's Plan\n"
    if today_plan:
        for issue in today_plan[:5]:  # Limit to prevent spam
            priority = issue.get('priority', 'P3')
            report += f"- **{issue.get('key', 'UNKNOWN')}** ({priority}): {issue.get('title', 'No title')}\n"
        if len(today_plan) > 5:
            report += f"- ... and {len(today_plan) - 5} more issues in queue\n"
    else:
        report += "- No issues in queue\n"

    report += "\n## Blockers\n"
    if blockers:
        for blocker in blockers[:3]:  # Limit blockers shown
            report += f"- **{blocker.get('key', 'UNKNOWN')}**: {blocker.get('title', 'No title')}\n"
            if blocker.get('blocker_reason'):
                report += f"  - Reason: {blocker['blocker_reason']}\n"
        if len(blockers) > 3:
            report += f"- ... and {len(blockers) - 3} more blocked issues\n"
    else:
        report += "- No blockers\n"

    return report

def analyze_dependencies(issue: Dict[str, Any], all_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze issue dependencies and blocking relationships"""
    issue_key = issue['key']
    dependencies = issue.get('dependencies', [])

    # Find what this issue depends on
    depends_on = []
    for dep_key in dependencies:
        dep_issue = next((i for i in all_issues if i['key'] == dep_key), None)
        if dep_issue:
            depends_on.append({
                'key': dep_key,
                'title': dep_issue['title'],
                'status': dep_issue['status'],
                'ready': dep_issue['status'] == 'done'
            })
        else:
            depends_on.append({
                'key': dep_key,
                'title': 'Not found',
                'status': 'unknown',
                'ready': False
            })

    # Find what depends on this issue
    blocks = []
    for other_issue in all_issues:
        if issue_key in other_issue.get('dependencies', []):
            blocks.append({
                'key': other_issue['key'],
                'title': other_issue['title'],
                'status': other_issue['status']
            })

    # Calculate readiness
    ready_to_work = len(depends_on) == 0 or all(d['ready'] for d in depends_on)
    blocking_others = len(blocks) > 0

    return {
        'depends_on': depends_on,
        'blocks': blocks,
        'ready_to_work': ready_to_work,
        'blocking_others': blocking_others,
        'dependency_count': len(depends_on),
        'blocking_count': len(blocks)
    }

def calculate_urgency_score(issue: Dict[str, Any]) -> float:
    """Calculate urgency score for work prioritization"""
    try:
        # Base priority score
        priority_scores = {'P1': 100, 'P2': 80, 'P3': 60, 'P4': 40, 'P5': 20}
        priority_score = priority_scores.get(issue.get('priority', 'P3'), 60)

        # Age factor (older issues get slight boost)
        created = datetime.fromisoformat(issue['created_utc'].rstrip('Z'))
        age_days = (datetime.utcnow() - created).days
        age_score = min(age_days * 2, 20)  # Cap at 20 points

        # Blocking factor (issues blocking others get boost)
        blocking_score = 15 if issue.get('blocking_others', False) else 0

        # Status factor
        status_scores = {
            'proposed': 5,
            'in_progress': 10,
            'review': 8,
            'blocked': 0
        }
        status_score = status_scores.get(issue.get('status', 'proposed'), 5)

        return priority_score + age_score + blocking_score + status_score
    except Exception:
        return 50.0  # Default score

def sanitize_git_output(output: str, error: str) -> Dict[str, str]:
    """Sanitize git output to remove sensitive information"""
    # Remove absolute paths
    sanitized_output = re.sub(r'/[^\s]+/', '[PATH]/', output)
    sanitized_error = re.sub(r'/[^\s]+/', '[PATH]/', error) if error else ''

    # Remove potential environment variables
    sanitized_output = re.sub(r'\$[A-Z_]+', '[ENV_VAR]', sanitized_output)
    sanitized_error = re.sub(r'\$[A-Z_]+', '[ENV_VAR]', sanitized_error)

    return {
        'output': sanitized_output,
        'error': sanitized_error
    }

def validate_branch_name(branch_name: str) -> bool:
    """Validate git branch name"""
    # Git branch name rules
    if not branch_name:
        return False

    # Cannot start with dash, dot, or slash
    if branch_name.startswith(('-', '.', '/')):
        return False

    # Cannot end with slash or dot
    if branch_name.endswith(('/', '.')):
        return False

    # Cannot contain special characters
    invalid_chars = ['..', '~', '^', ':', '?', '*', '[', '\\', ' ']
    if any(char in branch_name for char in invalid_chars):
        return False

    return True

def extract_requirements_from_text(text: str) -> List[Dict[str, Any]]:
    """Extract potential requirements from text content"""
    requirements = []

    # Look for numbered lists
    numbered_pattern = r'^\d+\.\s+(.+)$'
    for match in re.finditer(numbered_pattern, text, re.MULTILINE):
        requirement = match.group(1).strip()
        if len(requirement) > 10:  # Filter out short items
            requirements.append({
                'title': requirement[:100],  # Truncate for title
                'description': requirement,
                'type': 'feature',  # Default type
                'priority': 'P3',   # Default priority
                'source_line': match.group(0)
            })

    # Look for bullet points
    bullet_pattern = r'^[-*]\s+(.+)$'
    for match in re.finditer(bullet_pattern, text, re.MULTILINE):
        requirement = match.group(1).strip()
        if len(requirement) > 10 and not any(req['title'] == requirement[:100] for req in requirements):
            requirements.append({
                'title': requirement[:100],
                'description': requirement,
                'type': 'feature',
                'priority': 'P3',
                'source_line': match.group(0)
            })

    # Look for "should" statements
    should_pattern = r'(\w+\s+should\s+[^.]+\.)'
    for match in re.finditer(should_pattern, text, re.IGNORECASE):
        requirement = match.group(1).strip()
        if len(requirement) > 10:
            requirements.append({
                'title': requirement[:100],
                'description': requirement,
                'type': 'feature',
                'priority': 'P3',
                'source_line': requirement
            })

    return requirements[:10]  # Limit to prevent spam

def generate_test_plan(issue: Dict[str, Any], test_types: List[str]) -> Dict[str, Any]:
    """Generate comprehensive test plan for an issue"""
    test_plan = {
        'issue_key': issue['key'],
        'title': issue['title'],
        'test_types': test_types,
        'test_cases': [],
        'setup_requirements': [],
        'automation_notes': []
    }

    description = issue.get('description', '')
    acceptance_criteria = issue.get('acceptance_criteria', [])

    # Generate test cases from acceptance criteria
    for i, criterion in enumerate(acceptance_criteria):
        test_plan['test_cases'].append({
            'id': f"TC-{i+1:03d}",
            'title': f"Verify: {criterion}",
            'type': 'acceptance',
            'priority': 'high',
            'steps': [
                f"Given the implementation of {issue['title']}",
                f"When {criterion.lower()}",
                "Then verify the expected behavior"
            ]
        })

    # Add type-specific test cases
    if 'unit' in test_types:
        test_plan['test_cases'].append({
            'id': 'TC-UNIT-001',
            'title': 'Unit test coverage for core functionality',
            'type': 'unit',
            'priority': 'high',
            'steps': ['Create unit tests for all public methods', 'Achieve >90% code coverage']
        })

    if 'integration' in test_types:
        test_plan['test_cases'].append({
            'id': 'TC-INT-001',
            'title': 'Integration test for end-to-end workflow',
            'type': 'integration',
            'priority': 'medium',
            'steps': ['Test complete user workflow', 'Verify system integration points']
        })

    if 'performance' in test_types:
        test_plan['test_cases'].append({
            'id': 'TC-PERF-001',
            'title': 'Performance benchmarks',
            'type': 'performance',
            'priority': 'medium',
            'steps': ['Establish baseline metrics', 'Test under expected load']
        })

    # Setup requirements
    test_plan['setup_requirements'] = [
        'Test database with sample data',
        'Mock external services',
        'Test environment configuration'
    ]

    # Automation notes
    test_plan['automation_notes'] = [
        'Consider adding to CI/CD pipeline',
        'Use existing test framework if available',
        'Ensure tests are deterministic and fast'
    ]

    return test_plan

def generate_security_checklist(issue: Dict[str, Any], compliance_frameworks: List[str]) -> Dict[str, Any]:
    """Generate security review checklist"""
    checklist = {
        'issue_key': issue['key'],
        'title': issue['title'],
        'frameworks': compliance_frameworks,
        'checks': [],
        'risk_areas': [],
        'recommendations': []
    }

    # Base security checks
    base_checks = [
        'Input validation and sanitization',
        'Authentication and authorization',
        'Data encryption in transit and at rest',
        'Error handling does not leak sensitive information',
        'Logging does not expose sensitive data',
        'Rate limiting and abuse prevention'
    ]

    # Add framework-specific checks
    if 'OWASP' in compliance_frameworks:
        base_checks.extend([
            'SQL injection prevention',
            'XSS protection',
            'CSRF protection',
            'Security headers configured'
        ])

    if 'GDPR' in compliance_frameworks:
        base_checks.extend([
            'Personal data minimization',
            'Right to deletion support',
            'Data processing consent',
            'Privacy by design principles'
        ])

    checklist['checks'] = [{'item': check, 'status': 'pending'} for check in base_checks]

    # Analyze issue for risk areas
    description = issue.get('description', '').lower()
    if any(word in description for word in ['auth', 'login', 'password', 'token']):
        checklist['risk_areas'].append('Authentication/Authorization')
    if any(word in description for word in ['database', 'sql', 'query']):
        checklist['risk_areas'].append('Database Security')
    if any(word in description for word in ['api', 'endpoint', 'http']):
        checklist['risk_areas'].append('API Security')
    if any(word in description for word in ['user', 'input', 'form']):
        checklist['risk_areas'].append('Input Validation')

    # General recommendations
    checklist['recommendations'] = [
        'Conduct threat modeling session',
        'Review code with security focus',
        'Run security scanning tools',
        'Test with security test cases'
    ]

    return checklist

def create_pr_template(issue: Dict[str, Any]) -> Dict[str, str]:
    """Create PR title and body from issue"""
    # PR title
    pr_title = f"[{issue['key']}] {issue['title']}"

    # PR body
    pr_body = f"""## Issue
{issue['key']}: {issue['title']}

## Description
{issue.get('description', 'No description available')[:500]}{'...' if len(issue.get('description', '')) > 500 else ''}

## Acceptance Criteria
"""

    for criterion in issue.get('acceptance_criteria', []):
        pr_body += f"- [ ] {criterion}\n"

    if not issue.get('acceptance_criteria'):
        pr_body += "- No specific acceptance criteria defined\n"

    pr_body += f"""
## Type
{issue.get('type', 'feature').title()}

## Priority
{issue.get('priority', 'P3')}

## Module
{issue.get('module', 'N/A')}

---
*Generated by PM MCP Server*
"""

    return {
        'title': pr_title,
        'body': pr_body
    }

async def ensure_project_git_setup(project_path: Path) -> bool:
    """Ensure project has proper git setup"""
    try:
        # Check if it's a git repo
        result = await run_git_command_async(['status'], cwd=project_path)
        if not result['success']:
            # Initialize git repo if not exists
            init_result = await run_git_command_async(['init'], cwd=project_path)
            if not init_result['success']:
                return False

        # Setup git identity
        await run_git_command_async(
            ['config', 'user.name', Config.GIT_USER_NAME or 'PM Agent'],
            cwd=project_path
        )
        await run_git_command_async(
            ['config', 'user.email', Config.GIT_USER_EMAIL or 'pm@local'],
            cwd=project_path
        )
        return True
    except Exception:
        return False

class RateLimiter:
    """Simple rate limiter for git operations"""
    def __init__(self, max_operations: int = 10, window_seconds: int = 60):
        self.max_operations = max_operations
        self.window_seconds = window_seconds
        self.operations = []

    def can_proceed(self) -> bool:
        """Check if operation can proceed within rate limits"""
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)

        # Remove old operations
        self.operations = [op for op in self.operations if op > cutoff]

        # Check limit
        if len(self.operations) >= self.max_operations:
            return False

        # Record this operation
        self.operations.append(now)
        return True

# Global rate limiter for git operations
git_rate_limiter = RateLimiter(max_operations=20, window_seconds=60)