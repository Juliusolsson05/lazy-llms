"""Git integration helpers with security"""
from typing import Dict, Any
from utils import run_git

def git_status(repo_path: str) -> Dict[str, Any]:
    """Return porcelain git status for parsable output"""
    return run_git(repo_path, ["status", "--porcelain=v1"])

def git_current_branch(repo_path: str) -> Dict[str, Any]:
    """Get current branch name"""
    return run_git(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])

def git_push_current(repo_path: str, remote: str = "origin") -> Dict[str, Any]:
    """Push current HEAD to same branch name"""
    branch = git_current_branch(repo_path)
    if branch["rc"] != 0:
        return branch
    name = branch["out"].strip()
    return run_git(repo_path, ["push", remote, f"HEAD:{name}"])

def git_has_changes(repo_path: str) -> bool:
    """Check if repository has uncommitted changes"""
    status = git_status(repo_path)
    return status["rc"] == 0 and bool(status["out"].strip())

def git_branch_exists(repo_path: str, branch_name: str) -> bool:
    """Check if branch exists locally"""
    result = run_git(repo_path, ["branch", "--list", branch_name])
    return result["rc"] == 0 and branch_name in result["out"]