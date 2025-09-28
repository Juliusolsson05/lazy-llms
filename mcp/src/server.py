#!/usr/bin/env python3
"""
LLM-Native Project Management MCP Server
Production-ready implementation with all fixes applied
"""
import os
import sys
import asyncio
import json
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("❌ Error: MCP library not installed. Run 'pip install mcp' first.")
    sys.exit(1)

from config import Config
from database import PMDatabase, DatabaseSession, _get_issue_field_json, Task, WorkLog
from models import *
from utils import *
from git_integration import git_status, git_current_branch, git_push_current
from docs_content import DOCS_CONTENT
from workflow_content import WORKFLOW_CONTENT

# Initialize MCP server
mcp = FastMCP("pm-server")

# Ensure database is initialized
PMDatabase.initialize()

# =============== Helper Functions ===============

def _auto_project_id() -> Optional[str]:
    """Pick project by CWD if PM_DEFAULT_PROJECT_ID not set."""
    env = Config.get_default_project_id()
    if env:
        return env
    try:
        cwd = Path(os.getcwd()).resolve()
        for p in PMDatabase.get_all_projects():
            try:
                p_path = Path(p.absolute_path).resolve()
                # exact repo or subdir
                if cwd == p_path or str(cwd).startswith(str(p_path) + os.sep):
                    return p.project_id
            except Exception:
                continue
    except Exception:
        pass
    # Fallback: first project if any
    projects = PMDatabase.get_all_projects()
    return projects[0].project_id if projects else None

def _require_project_id(explicit: Optional[str]) -> Optional[str]:
    return explicit or _auto_project_id()

def get_default_project_id() -> Optional[str]:
    """Get default project ID from config or first available"""
    if Config.DEFAULT_PROJECT_ID:
        return Config.DEFAULT_PROJECT_ID

    try:
        with DatabaseSession():
            projects = PMDatabase.get_all_projects()
            if projects:
                # projects is now a list of models, not dicts
                return projects[0].project_id
    except Exception:
        pass
    return None

# Use standardized response functions from utils
# Compatibility shim for migration period
def standard_response(success: bool, message: str, data: Optional[Dict[str, Any]] = None,
                     hints: Optional[List[str]] = None) -> Dict[str, Any]:
    """Compatibility shim - use ok() and err() for new code"""
    if success:
        return ok(message, data, hints)
    else:
        return err(message, data, hints)

# =============== Discovery Tools ===============

@mcp.tool()
def pm_docs(input: PMDocsInput) -> Dict[str, Any]:
    """
    Get comprehensive PM system documentation and workflow guidance.
    Returns complete documentation including all commands, workflows,
    troubleshooting, and best practices.
    """
    try:
        return ok("Complete PM Documentation", {
            "content": DOCS_CONTENT
        }, hints=["Use pm_workflow for methodology and best practices"])
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to get documentation: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check system configuration"]
        )

@mcp.tool()
def pm_workflow(input: PMWorkflowInput) -> Dict[str, Any]:
    """
    Get methodology and best practices for PM-driven development.
    This is the primary tool for new chat sessions, providing comprehensive
    guidance on how to work effectively with the PM system.
    """
    try:
        return ok("PM Workflow Methodology", {
            "content": WORKFLOW_CONTENT
        }, hints=["Follow this methodology throughout your development session"])
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to get workflow methodology: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check system configuration"]
        )

@mcp.tool()
@strict_project_scope
def pm_status(input: PMStatusInput) -> Dict[str, Any]:
    """
    Get comprehensive project status including issue counts, velocity metrics,
    and current work distribution. Essential for understanding project health.
    """
    try:
        with DatabaseSession():
            pid = _require_project_id(input.project_id)
            if not pid:
                return err("No project found. Initialize one with pm_init_project()", {})
            project = PMDatabase.get_project(pid)
            if not project:
                return err(f"Project not found: {pid}", {})

            # Convert project model to dict
            proj_dict = PMDatabase._project_to_dict(project)

            # Get project metrics with submodule breakdown if project has submodules
            has_submodules = bool(project.submodules)
            metrics = PMDatabase.project_metrics(project, include_submodule_breakdown=has_submodules)

            data = {
                "project": proj_dict,
                "metrics": metrics,
            }

            # Add submodule summary if applicable
            if has_submodules and "submodule_metrics" in metrics:
                submodule_summary = []
                for submodule in project.submodules:
                    sub_name = submodule["name"]
                    if sub_name in metrics["submodule_metrics"]:
                        sub_data = metrics["submodule_metrics"][sub_name]
                        submodule_summary.append({
                            "name": sub_name,
                            "path": submodule.get("path", ""),
                            "total_issues": sub_data["total"],
                            "in_progress": sub_data["in_progress_count"],
                            "blocked": sub_data["blocked_count"],
                            "completion_rate": sub_data["completion_rate"]
                        })
                data["submodule_summary"] = submodule_summary

            # Generate helpful hints
            hints = []
            if has_submodules:
                hints.append("Use pm_list_issues --submodule <name> to filter by submodule")
            if metrics["counts"]["by_status"].get("blocked", 0) > 0:
                hints.append("pm_blocked_issues to see what's blocked")

            return ok("Project status with submodule breakdown", data, hints=hints)
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to get project status: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check database connectivity", "Verify project exists"]
        )

@mcp.tool()
@strict_project_scope
def pm_list_issues(input: ListIssuesInput) -> Dict[str, Any]:
    """
    List and filter project issues with comprehensive details.
    Returns structured issue data suitable for analysis and planning.
    """
    try:
        with DatabaseSession():
            pid = _require_project_id(input.project_id)
            if not pid:
                return err("No project found. Initialize one with pm_init_project()", {})

            # If submodule is specified, use it as the module filter
            module_filter = input.submodule if input.submodule else input.module

            issues = PMDatabase.find_issues(pid,
                                            status=input.status, priority=input.priority,
                                            module=module_filter, q=None, query=None)

            # Add submodule info to response if filtering by submodule
            response_data = {
                "issues": [i.to_rich_dict() for i in issues],
                "count": len(issues)
            }
            if input.submodule:
                response_data["filtered_by_submodule"] = input.submodule

            return ok(f"Found {len(issues)} issues", response_data)
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to list issues: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check database connectivity", "Verify project exists"]
        )

@mcp.tool()
@strict_project_scope
def pm_get_issue(input: GetIssueInput) -> Dict[str, Any]:
    """
    Get comprehensive issue details including specifications, tasks, and work history.
    Essential for understanding issue context before starting work.
    FIXED: Uses Peewee models instead of raw SQL queries.
    """
    try:
        with DatabaseSession():
            if input.include_tasks or input.include_worklogs:
                # Get issue with all relations using Peewee models
                issue_data = PMDatabase.get_issue_with_relations(input.issue_key)
                if not issue_data:
                    return standard_response(
                        success=False,
                        message=f"Issue {input.issue_key} not found",
                        hints=["Use pm_search_issues to find issues", "Check issue key format"]
                    )

                result_data = {
                    "issue": issue_data['issue']
                }

                if input.include_tasks:
                    result_data["tasks"] = issue_data['tasks']

                if input.include_worklogs:
                    result_data["worklogs"] = issue_data['worklogs']

                # Add project info
                result_data["project"] = issue_data['project']

            else:
                # Get just the issue - scoped to current project
                issue = PMDatabase.get_issue_scoped(input.project_id, input.issue_key)
                if issue is None:
                    return standard_response(
                        success=False,
                        message=f"Issue {input.issue_key} not found in current project"
                    )
                result_data = {"issue": PMDatabase._issue_to_dict(issue)}

            # Add dependency analysis if requested
            if input.include_dependencies:
                # Get project_id - it could be in different places depending on the path taken
                issue_proj_id = None
                # First try direct project_id on issue
                if 'issue' in result_data:
                    issue_proj_id = result_data['issue'].get('project_id')
                # Then try separate project object
                if not issue_proj_id and 'project' in result_data:
                    issue_proj_id = result_data['project'].get('project_id')
                # Finally fall back to current scope
                if not issue_proj_id:
                    issue_proj_id = _require_project_id(None)
                all_issues = PMDatabase.get_issues(project_id=issue_proj_id, limit=1000)
                deps = analyze_dependencies(result_data['issue'], all_issues)
                result_data["dependencies"] = deps

            # Generate contextual next steps
            issue = result_data['issue']
            hints = []
            if issue['status'] == 'proposed':
                hints.extend([
                    f"pm_estimate --issue-key {issue['key']} to add effort estimates",
                    f"pm_refine_issue --issue-key {issue['key']} to refine requirements",
                    f"pm_start_work --issue-key {issue['key']} to begin implementation"
                ])
            elif issue['status'] == 'in_progress':
                hints.extend([
                    f"pm_log_work --issue-key {issue['key']} to track current activity",
                    f"pm_create_task --issue-key {issue['key']} to break down work",
                    f"pm_commit --issue-key {issue['key']} to save changes"
                ])
            elif issue['status'] == 'review':
                hints.extend([
                    f"pm_push_branch --issue-key {issue['key']} --create-pr to create pull request",
                    f"pm_update_status --issue-key {issue['key']} --status done when approved"
                ])

            return standard_response(
                success=True,
                message=f"Issue details for {input.issue_key}",
                data=result_data,
                hints=hints
            )

    except ScopeError as se:
        return err(str(se))
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to get issue: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check database connectivity", "Verify issue key format"]
        )

@mcp.tool()
def pm_search_issues(input: SearchIssuesInput) -> Dict[str, Any]:
    """
    Full-text search across all issue content.
    Searches titles, descriptions, and all rich content fields.
    """
    try:
        with DatabaseSession():
            issues = PMDatabase.search_issues(
                query_text=input.query,
                project_id=input.project_id,
                limit=input.limit,
                include_archived=input.include_archived
            )

            # If not including content, strip heavy fields for performance
            if not input.include_content:
                for issue in issues:
                    issue.pop('description', None)
                    issue.pop('technical_approach', None)

            return standard_response(
                success=True,
                message=f"Found {len(issues)} issues matching '{input.query}'{' (including archived)' if input.include_archived else ''}",
                data={
                    "query": input.query,
                    "project_id": input.project_id,
                    "results": issues,
                    "total_matches": len(issues),
                    "include_content": input.include_content
                },
                hints=[
                    f"Use pm_get_issue --issue-key {issues[0]['key']} for full details" if issues else "Try broader search terms",
                    "Use --include-content true to see full descriptions in results"
                ]
            )

    except Exception as e:
        return standard_response(
            success=False,
            message=f"Search failed: {type(e).__name__}",
            hints=["Check database connectivity", "Try simpler search terms"]
        )

@mcp.tool()
def pm_list_projects() -> Dict[str, Any]:
    """
    List all available projects in the system.
    Shows project metadata and basic statistics.
    """
    try:
        with DatabaseSession():
            projects = PMDatabase.get_all_projects()
            # Convert models to dicts
            data = {"projects": [PMDatabase._project_to_dict(p) for p in projects],
                    "count": len(projects)}
        return ok(f"Found {len(projects)} projects", data)
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to list projects: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check database connectivity", "Ensure database is initialized"]
        )

@mcp.tool()
@strict_project_scope
def pm_list_archived_issues(input: ListArchivedIssuesInput) -> Dict[str, Any]:
    """
    List archived/completed issues with comprehensive filtering.
    Provides access to historical work, decisions, and implementation details.
    All returned issues are clearly marked as archived.
    """
    try:
        with DatabaseSession():
            pid = _require_project_id(input.project_id)
            if not pid:
                return err("No project found. Initialize one with pm_init_project()", {})

            # Prepare filters for archived issues
            filters = {
                'priority': input.priority,
                'module': input.module,
                'type': input.type,
                'search_keyword': input.search_keyword,
                'date_from': input.date_from,
                'date_to': input.date_to
            }

            issues = PMDatabase.find_archived_issues(pid, **filters)

            # Limit results
            if input.limit:
                issues = issues[:input.limit]

            # Add archived indicator to each issue
            archived_issues = []
            for issue in issues:
                issue_dict = issue.to_rich_dict()
                issue_dict['is_archived'] = True
                issue_dict['archived_status'] = 'ARCHIVED'
                archived_issues.append(issue_dict)

            return ok(
                f"Found {len(archived_issues)} archived issues",
                {
                    "archived_issues": archived_issues,
                    "count": len(archived_issues),
                    "filters_applied": {k: v for k, v in filters.items() if v is not None}
                },
                hints=[
                    f"Use pm_get_archived_issue --issue-key {archived_issues[0]['key']} for full historical details" if archived_issues else "No archived issues match your filters",
                    "Archived issues represent completed/historical work"
                ]
            )
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to list archived issues: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check database connectivity", "Verify filters are valid"]
        )

@mcp.tool()
@strict_project_scope
def pm_get_archived_issue(input: GetArchivedIssueInput) -> Dict[str, Any]:
    """
    Retrieve comprehensive details of an archived issue.
    Returns full historical context including work logs, decisions, and artifacts.
    Clearly indicates this is archived/historical data.
    """
    try:
        with DatabaseSession():
            pid = _require_project_id(input.project_id)

            # Get the archived issue
            issue = PMDatabase.get_archived_issue(pid, input.issue_key)
            if not issue:
                return err(
                    f"Archived issue {input.issue_key} not found",
                    {},
                    hints=["Use pm_list_archived_issues to find archived issues", "Check issue key format"]
                )

            # Build result with archived indicators
            result_data = {
                "issue": issue.to_rich_dict(),
                "is_archived": True,
                "archived_status": "ARCHIVED - This is historical/completed work"
            }

            # Add work logs if requested
            if input.include_worklogs:
                worklogs = []
                for log in issue.worklogs:
                    log_data = log.to_dict()
                    # Include artifacts and context
                    log_data['artifacts'] = log.artifacts
                    log_data['context'] = log.context
                    worklogs.append(log_data)
                result_data["worklogs"] = worklogs
                result_data["total_worklogs"] = len(worklogs)

            # Add tasks if requested
            if input.include_tasks:
                tasks = []
                for task in issue.tasks:
                    task_data = task.to_dict()
                    task_data['checklist'] = task.checklist
                    task_data['notes'] = task.notes
                    tasks.append(task_data)
                result_data["tasks"] = tasks

            # Add project info
            result_data["project"] = PMDatabase._project_to_dict(issue.project)

            return ok(
                f"Archived issue {input.issue_key} retrieved",
                result_data,
                hints=[
                    "This is archived/historical data from completed work",
                    "Use work logs and artifacts to understand implementation details",
                    "Reference this for similar future work"
                ]
            )

    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to get archived issue: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check database connectivity", "Verify issue key format"]
        )

# =============== Planning Tools ===============

@mcp.tool()
@strict_project_scope
def pm_create_issue(input: CreateIssueInput) -> Dict[str, Any]:
    """
    Create a comprehensive issue with rich LLM-generated documentation.
    This is the primary tool for capturing work with full context and specifications.
    """
    try:
        with DatabaseSession():
            # ensure project_id is set / auto-scoped
            if not input.project_id:
                object.__setattr__(input, "project_id", _require_project_id(None))

            # Handle submodule - if provided, use it as the module
            if input.submodule:
                object.__setattr__(input, "module", input.submodule)

            issue = PMDatabase.create_issue(input)
            return ok("Issue created", {"issue": issue.to_rich_dict()},
                      hints=[f"Start work: pm_start_work --issue-key {issue.key}"])
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to create issue: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check database connectivity", "Verify all required fields are provided"]
        )

@mcp.tool()
@strict_project_scope
def pm_start_work(input: StartWorkInput) -> Dict[str, Any]:
    """
    Start work on an issue - updates status, optionally creates branch.
    This is the primary entry point for beginning implementation.
    """
    try:
        with DatabaseSession():
            # Get issue scoped to current project
            # The decorator adds project_id, but we need to get it properly
            project_id = _require_project_id(None)
            issue = PMDatabase.get_issue_scoped(project_id, input.issue_key)
            if issue is None:
                return standard_response(
                    success=False,
                    message=f"Issue {input.issue_key} not found in current project"
                )
            issue_dict = PMDatabase._issue_to_dict(issue)

            # Validate dependencies if requested
            if input.validate_dependencies:
                all_issues = PMDatabase.get_issues(project_id=issue_dict['project_id'], limit=1000)
                deps = analyze_dependencies(issue_dict, all_issues)
                if not deps['ready_to_work']:
                    pending = [d['key'] for d in deps['depends_on'] if not d['ready']]
                    return standard_response(
                        success=False,
                        message=f"Cannot start work - dependencies not completed: {', '.join(pending)}",
                        hints=[f"Complete dependencies first: {', '.join(pending)}"]
                    )

            # Update status to in_progress
            update_data = issue_dict.copy()
            old_status = issue_dict['status']
            update_data['status'] = 'in_progress'
            updated_issue = PMDatabase.create_or_update_issue(update_data)

            # Log work start
            PMDatabase.add_worklog({
                'issue_key': input.issue_key,
                'agent': Config.DEFAULT_OWNER,
                'activity': 'planning',
                'summary': f"Started work on {input.issue_key}: {issue_dict['title']}",
                'context': {
                    'previous_status': old_status,
                    'notes': input.notes or "Beginning implementation"
                }
            })

            result_data = {
                "issue": updated_issue,
                "status_changed": f"{old_status} → in_progress"
            }

            hints = [
                f"pm_log_work --issue-key {input.issue_key} to track progress",
                f"pm_create_task --issue-key {input.issue_key} to break down work"
            ]

            # Handle branch creation if requested
            if input.create_branch:
                project = PMDatabase.get_project(issue_dict['project_id'])
                if project:
                    try:
                        branch_name = issue_dict.get('branch_hint') or generate_branch_name(
                            input.issue_key, issue_dict['type'], issue_dict['title']
                        )

                        # Get project dict for path access
                        if hasattr(project, 'absolute_path'):
                            project_path = Path(project.absolute_path)
                        else:
                            project_dict = PMDatabase._project_to_dict(project) if project else {}
                            project_path = Path(project_dict['absolute_path']) if project_dict else Path.cwd()

                        # Ensure git setup
                        if not asyncio.run(ensure_project_git_setup(project_path)):
                            result_data['branch_warning'] = 'Git setup incomplete - manual branch creation recommended'
                        else:
                            git_result = run_git_command_sync(['checkout', '-b', branch_name], cwd=project_path)
                            if git_result['success']:
                                result_data['branch_created'] = branch_name
                                sanitized = sanitize_git_output(git_result['output'], git_result.get('error', ''))
                                result_data['git_output'] = sanitized['output']
                                hints.append(f"Branch '{branch_name}' created and checked out")
                            else:
                                result_data['branch_error'] = git_result['error']
                                hints.append("Branch creation failed - create manually if needed")
                    except Exception:
                        result_data['branch_error'] = 'Branch creation failed'

            return standard_response(
                success=True,
                message=f"Started work on {input.issue_key}",
                data=result_data,
                hints=hints
            )

    except ScopeError as se:
        return err(str(se))
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to start work: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check issue exists", "Verify issue is in startable state"]
        )

@mcp.tool()
@strict_project_scope
def pm_log_work(input: LogWorkInput) -> Dict[str, Any]:
    """
    Log development activity with artifacts and context.
    Essential for tracking progress and building project knowledge.
    """
    try:
        with DatabaseSession():
            # Validate issue belongs to current project - using strict scope
            # The decorator adds project_id, but we need to get it properly
            project_id = _require_project_id(None)
            issue = PMDatabase.get_issue_scoped(project_id, input.issue_key)
            if issue is None:
                return err("Issue not found in current project scope")
            issue_dict = PMDatabase._issue_to_dict(issue)

            # Build work log data
            context_data = {}
            if input.time_spent:
                context_data['time_spent'] = input.time_spent
                context_data['hours_logged'] = parse_duration(input.time_spent)
            if input.blockers:
                context_data['blockers'] = input.blockers
            if input.decisions:
                context_data['decisions'] = input.decisions

            worklog_data = {
                'issue_key': input.issue_key,
                'agent': Config.DEFAULT_OWNER,
                'activity': input.activity,
                'summary': input.summary,
                'artifacts': input.artifacts,
                'context': context_data
            }

            if input.task_id:
                worklog_data['task_id'] = input.task_id

            worklog = PMDatabase.add_worklog(worklog_data)

            # Calculate time for response
            hours_spent = parse_duration(input.time_spent) if input.time_spent else 0

            return standard_response(
                success=True,
                message=f"Logged {input.activity} work on {input.issue_key}",
                data={
                    "worklog": worklog,
                    "time_logged": input.time_spent,
                    "hours_logged": hours_spent,
                    "artifacts_count": len(input.artifacts)
                },
                hints=[
                    f"pm_commit --issue-key {input.issue_key} to save code changes",
                    f"pm_update_status --issue-key {input.issue_key} to change status when ready"
                ]
            )

    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to log work: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check issue exists", "Verify time format (e.g., '2h', '30m')"]
        )

@mcp.tool()
@strict_project_scope
def pm_update_status(input: UpdateStatusInput) -> Dict[str, Any]:
    """
    Update issue status with workflow validation.
    Validates status transitions and logs the change.
    """
    try:
        with DatabaseSession():
            # Get current project context
            project_id = _require_project_id(None)
            issue = PMDatabase.get_issue_scoped(project_id, input.issue_key)
            if issue is None:
                return err("Issue not found in current project scope")

            issue_dict = PMDatabase._issue_to_dict(issue)
            old_status = issue_dict['status']

            # Validate workflow transition
            valid_transitions = {
                'proposed': ['in_progress', 'canceled'],
                'in_progress': ['blocked', 'review', 'canceled'],
                'blocked': ['in_progress', 'canceled'],
                'review': ['in_progress', 'done', 'canceled'],
                'done': ['in_progress'],  # Can reopen
                'canceled': ['proposed']  # Can revive
            }

            if old_status not in valid_transitions:
                return err(f"Unknown current status: {old_status}")

            if input.status not in valid_transitions.get(old_status, []):
                return standard_response(
                    success=False,
                    message=f"Invalid status transition: {old_status} → {input.status}",
                    data={"valid_transitions": valid_transitions.get(old_status, [])},
                    hints=[f"Valid transitions from {old_status}: {', '.join(valid_transitions.get(old_status, []))}"]
                )

            # Check for blocker reason if blocking
            if input.status == 'blocked' and not input.blocker_reason:
                return err("Blocker reason required when setting status to 'blocked'")

            # Update the issue status
            update_data = issue_dict.copy()
            update_data['status'] = input.status

            # Add blocker info if blocking
            if input.status == 'blocked' and input.blocker_reason:
                planning = _get_issue_field_json(issue, 'planning')
                planning['blocker_reason'] = input.blocker_reason
                planning['blocked_at'] = datetime.utcnow().isoformat()
                update_data['planning'] = json.dumps(planning)

            updated_issue = PMDatabase.create_or_update_issue(update_data)

            # Log the status change
            context_data = {
                'previous_status': old_status,
                'new_status': input.status
            }
            if input.notes:
                context_data['notes'] = input.notes
            if input.blocker_reason:
                context_data['blocker_reason'] = input.blocker_reason

            PMDatabase.add_worklog({
                'issue_key': input.issue_key,
                'agent': Config.DEFAULT_OWNER,
                'activity': 'planning',
                'summary': f"Status changed from {old_status} to {input.status}",
                'context': context_data
            })

            # Build response hints based on new status
            hints = []
            if input.status == 'in_progress':
                hints.extend([
                    f"pm_log_work --issue-key {input.issue_key} to track progress",
                    f"pm_create_task --issue-key {input.issue_key} to break down work"
                ])
            elif input.status == 'review':
                hints.append(f"pm_push_branch --issue-key {input.issue_key} --create-pr to create pull request")
            elif input.status == 'done':
                hints.append(f"pm_daily_standup to report completion")
            elif input.status == 'blocked':
                hints.append(f"pm_blocked_issues to analyze blockers")

            return standard_response(
                success=True,
                message=f"Status updated: {old_status} → {input.status}",
                data={
                    "issue": updated_issue,
                    "old_status": old_status,
                    "new_status": input.status,
                    "transition": f"{old_status} → {input.status}"
                },
                hints=hints
            )

    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to update status: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check issue exists", "Verify status transition is valid"]
        )

@mcp.tool()
@strict_project_scope
def pm_delete_issue(input: DeleteIssueInput) -> Dict[str, Any]:
    """
    Delete an issue with all associated data.
    Requires confirmation and handles cascade deletion.
    """
    try:
        # Safety check - require explicit confirmation
        if not input.confirm:
            return standard_response(
                success=False,
                message="Deletion not confirmed",
                data={"safety_check": "Set confirm=true to delete"},
                hints=["This is a destructive operation - set confirm=true to proceed"]
            )

        with DatabaseSession():
            # Get current project context
            project_id = _require_project_id(None)
            issue = PMDatabase.get_issue_scoped(project_id, input.issue_key)
            if issue is None:
                return err("Issue not found in current project scope")

            issue_dict = PMDatabase._issue_to_dict(issue)

            # Check for blocking dependencies
            dependencies = issue_dict.get('dependencies', [])
            if dependencies:
                # Check if any issues depend on this one
                from src.jira_lite.models import Issue as JiraIssue
                all_issues = JiraIssue.select().where(JiraIssue.project == issue.project)
                blocked_by_this = []
                for other_issue in all_issues:
                    if other_issue.dependencies and input.issue_key in other_issue.dependencies:
                        blocked_by_this.append(other_issue.key)

                if blocked_by_this:
                    return standard_response(
                        success=False,
                        message=f"Cannot delete: Other issues depend on {input.issue_key}",
                        data={"blocked_by": blocked_by_this},
                        hints=["Remove dependencies from other issues first"]
                    )

            # Perform cascade deletion if requested
            deletion_summary = {
                "issue_key": input.issue_key,
                "issue_title": issue_dict['title'],
                "tasks_deleted": 0,
                "worklogs_deleted": 0
            }

            if input.cascade:
                # Delete all tasks
                tasks = Task.select().where(Task.issue == issue)
                deletion_summary["tasks_deleted"] = tasks.count()
                for task in tasks:
                    task.delete_instance()

                # Delete all worklogs
                worklogs = WorkLog.select().where(WorkLog.issue == issue)
                deletion_summary["worklogs_deleted"] = worklogs.count()
                for worklog in worklogs:
                    worklog.delete_instance()

            # Delete the issue itself
            issue.delete_instance()

            # Log the deletion if reason provided
            if input.reason:
                # Create a project-level log entry (no issue to attach to)
                # This would require a project-level worklog feature
                # For now, just include in response
                deletion_summary["deletion_reason"] = input.reason

            return standard_response(
                success=True,
                message=f"Issue {input.issue_key} deleted successfully",
                data=deletion_summary,
                hints=[
                    f"Issue and {deletion_summary['tasks_deleted']} tasks deleted",
                    f"{deletion_summary['worklogs_deleted']} worklogs removed"
                ]
            )

    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to delete issue: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check issue exists", "Ensure no other issues depend on this one"]
        )

# =============== Git Integration Tools ===============

@mcp.tool()
@strict_project_scope
def pm_create_branch(input: CreateBranchInput) -> Dict[str, Any]:
    """
    Create a git branch for an issue following naming conventions.
    Automatically configures branch tracking and updates issue metadata.
    FIXED: Proper error handling and security.
    """
    try:
        with DatabaseSession():
            issue = PMDatabase.get_issue(input.issue_key)
            if not issue:
                return standard_response(
                    success=False,
                    message=f"Issue {input.issue_key} not found"
                )
            issue_dict = PMDatabase._issue_to_dict(issue)

            project = PMDatabase.get_project(issue_dict['project_id'])
            if not project:
                return standard_response(
                    success=False,
                    message=f"Project {issue_dict['project_id']} not found"
                )

            # Rate limiting check
            if not git_rate_limiter.can_proceed():
                return standard_response(
                    success=False,
                    message="Rate limit exceeded for git operations",
                    hints=["Wait a moment before retrying git operations"]
                )

            # Generate or validate branch name
            branch_name = input.branch_name or issue_dict.get('branch_hint') or generate_branch_name(
                input.issue_key, issue_dict['type'], issue_dict['title']
            )

            if not validate_branch_name(branch_name):
                return standard_response(
                    success=False,
                    message=f"Invalid branch name: {branch_name}",
                    hints=["Use alphanumeric characters and hyphens only"]
                )

            # Get project dict for path access
            if hasattr(project, 'absolute_path'):
                project_path = Path(project.absolute_path)
            else:
                project_dict = PMDatabase._project_to_dict(project) if project else {}
                project_path = Path(project_dict['absolute_path']) if project_dict else Path.cwd()

            # Check if issue belongs to a submodule and adjust working path
            working_path = project_path
            project_dict = PMDatabase._project_to_dict(project)
            if issue.module and project_dict.get('metadata', {}).get('submodules'):
                submodules = project_dict['metadata']['submodules']
                for submodule in submodules:
                    if submodule['name'] == issue.module:
                        # This issue belongs to a specific submodule
                        submodule_path = project_path / submodule['path']
                        if submodule_path.exists() and (submodule_path / '.git').exists():
                            # Submodule has its own git repo
                            working_path = submodule_path
                        break

            # Ensure git setup
            setup_success = asyncio.run(ensure_project_git_setup(working_path))
            if not setup_success:
                return standard_response(
                    success=False,
                    message="Git setup failed - ensure repository is properly initialized",
                    hints=["Check if directory is a git repository", "Verify git is installed"]
                )

            # Checkout base branch safely
            git_result = run_git_command_sync(['checkout', input.base_branch], cwd=working_path)
            if not git_result['success']:
                return standard_response(
                    success=False,
                    message=f"Failed to checkout base branch {input.base_branch}",
                    data={"git_error": git_result['error']},
                    hints=[f"Ensure branch '{input.base_branch}' exists"]
                )

            # Pull latest changes (handle gracefully if no remote)
            pull_result = run_git_command_sync(['pull'], cwd=working_path)
            # Don't fail on pull errors - might be offline or no remote

            # Create new branch
            git_result = run_git_command_sync(['checkout', '-b', branch_name], cwd=working_path)

            if git_result['success']:
                # Update issue with branch info
                update_data = issue_dict.copy()
                update_data['branch_hint'] = branch_name
                PMDatabase.create_or_update_issue(update_data)

                # Log branch creation
                PMDatabase.add_worklog({
                    'issue_key': input.issue_key,
                    'agent': Config.DEFAULT_OWNER,
                    'activity': 'code',
                    'summary': f"Created branch: {branch_name}",
                    'artifacts': [
                        {
                            'type': 'branch',
                            'name': branch_name,
                            'base': input.base_branch
                        }
                    ]
                })

                sanitized = sanitize_git_output(git_result['output'], git_result.get('error', ''))

                return standard_response(
                    success=True,
                    message=f"Created and checked out branch: {branch_name}",
                    data={
                        "branch": branch_name,
                        "base_branch": input.base_branch,
                        "git_output": sanitized['output']
                    },
                    hints=[
                        f"pm_log_work --issue-key {input.issue_key} to start tracking work",
                        f"pm_commit --issue-key {input.issue_key} to save changes"
                    ]
                )
            else:
                sanitized = sanitize_git_output(git_result.get('output', ''), git_result.get('error', ''))
                return standard_response(
                    success=False,
                    message="Failed to create branch",
                    data={"git_error": sanitized['error']},
                    hints=["Check if branch already exists", "Ensure working directory is clean"]
                )

    except Exception as e:
        return standard_response(
            success=False,
            message=f"Branch creation failed: {type(e).__name__}",
            hints=["Check git repository status", "Verify project path exists"]
        )

@mcp.tool()
def pm_commit(input: CommitInput) -> Dict[str, Any]:
    """
    Create a git commit with PM trailers and issue context.
    Automatically formats commit messages with conventional commit style.
    FIXED: Proper regex handling and async safety.
    """
    try:
        with DatabaseSession():
            issue = PMDatabase.get_issue(input.issue_key)
            if not issue:
                return standard_response(
                    success=False,
                    message=f"Issue {input.issue_key} not found"
                )
            issue_dict = PMDatabase._issue_to_dict(issue)

            project = PMDatabase.get_project(issue_dict['project_id'])
            if not project:
                return standard_response(
                    success=False,
                    message=f"Project {issue_dict['project_id']} not found"
                )

            # Rate limiting
            if not git_rate_limiter.can_proceed():
                return standard_response(
                    success=False,
                    message="Rate limit exceeded for git operations"
                )

            # Get project dict for path access
            if hasattr(project, 'absolute_path'):
                project_path = Path(project.absolute_path)
            else:
                project_dict = PMDatabase._project_to_dict(project) if project else {}
                project_path = Path(project_dict['absolute_path']) if project_dict else Path.cwd()

            # Check if issue belongs to a submodule and adjust working path
            working_path = project_path
            project_dict = PMDatabase._project_to_dict(project)
            if issue.module and project_dict.get('metadata', {}).get('submodules'):
                submodules = project_dict['metadata']['submodules']
                for submodule in submodules:
                    if submodule['name'] == issue.module:
                        # This issue belongs to a specific submodule
                        submodule_path = project_path / submodule['path']
                        if submodule_path.exists() and (submodule_path / '.git').exists():
                            # Submodule has its own git repo
                            working_path = submodule_path
                        break

            # Ensure git identity is set
            setup_success = asyncio.run(ensure_project_git_setup(working_path))
            if not setup_success:
                return standard_response(
                    success=False,
                    message="Git identity setup failed"
                )

            # Format commit message with FIXED regex
            commit_message = format_commit_message(input.issue_key, input.message)

            # Stage files if specified
            if input.files:
                for file in input.files:
                    git_result = run_git_command_sync(['add', file], cwd=working_path)
                    if not git_result['success']:
                        return standard_response(
                            success=False,
                            message=f"Failed to stage file: {file}",
                            data={"git_error": git_result['error']}
                        )
            else:
                # Stage all changes
                git_result = run_git_command_sync(['add', '-A'], cwd=working_path)

            # Create commit
            commit_args = ['commit', '-m', commit_message]
            if input.amend:
                commit_args.append('--amend')

            git_result = run_git_command_sync(commit_args, cwd=working_path)

            if git_result['success']:
                # Get commit SHA
                sha_result = run_git_command_sync(['rev-parse', 'HEAD'], cwd=working_path)
                commit_sha = sha_result['output'][:7] if sha_result['success'] else 'unknown'

                # Log commit as work activity if requested
                if input.log_work:
                    PMDatabase.add_worklog({
                        'issue_key': input.issue_key,
                        'agent': Config.DEFAULT_OWNER,
                        'activity': 'code',
                        'summary': f"Committed: {input.message}",
                        'artifacts': [
                            {
                                'type': 'commit',
                                'sha': commit_sha,
                                'message': commit_message,
                                'files': input.files or []
                            }
                        ]
                    })

                sanitized = sanitize_git_output(git_result['output'], git_result.get('error', ''))

                return standard_response(
                    success=True,
                    message="Commit created successfully",
                    data={
                        "commit_sha": commit_sha,
                        "commit_message": commit_message,
                        "git_output": sanitized['output']
                    },
                    hints=[
                        f"pm_push_branch --issue-key {input.issue_key} to push changes",
                        f"pm_log_work --issue-key {input.issue_key} to continue tracking work"
                    ]
                )
            else:
                sanitized = sanitize_git_output(git_result.get('output', ''), git_result.get('error', ''))
                return standard_response(
                    success=False,
                    message="Failed to create commit",
                    data={"git_error": sanitized['error']},
                    hints=["Check if there are changes to commit", "Verify git repository state"]
                )

    except Exception as e:
        return standard_response(
            success=False,
            message=f"Commit failed: {type(e).__name__}",
            hints=["Check git repository status", "Verify working directory"]
        )

# =============== Analytics Tools ===============

@mcp.tool()
@strict_project_scope
def pm_my_queue(input: MyQueueInput) -> Dict[str, Any]:
    """
    Get personalized work queue with intelligent prioritization.
    Helps agents focus on the most important work.
    """
    owner = input.owner or Config.DEFAULT_OWNER

    try:
        with DatabaseSession():
            # Get assigned issues
            my_issues = PMDatabase.get_issues(owner=owner, limit=100)

            # Filter to actionable statuses
            actionable = [
                i for i in my_issues
                if i['status'] in ['proposed', 'in_progress', 'review']
            ]

            # Add blocked issues that might be unblockable
            if input.include_blocked:
                blocked_issues = PMDatabase.get_blocked_issues()
                all_issues = PMDatabase.get_issues(limit=1000)

                for blocked in blocked_issues:
                    deps = analyze_dependencies(blocked, all_issues)
                    if deps['ready_to_work']:
                        blocked['unblockable'] = True
                        actionable.append(blocked)

            # Sort based on criteria
            if input.sort_by == 'priority':
                priority_order = {'P1': 1, 'P2': 2, 'P3': 3, 'P4': 4, 'P5': 5}
                actionable.sort(key=lambda i: priority_order.get(i['priority'], 6))
            elif input.sort_by == 'urgency':
                actionable.sort(key=calculate_urgency_score, reverse=True)
            elif input.sort_by == 'dependency':
                # Sort by blocking others first, then by dependency count
                all_issues = PMDatabase.get_issues(limit=1000)
                def dep_score(issue):
                    deps = analyze_dependencies(issue, all_issues)
                    return (deps['blocking_count'] * 10) - deps['dependency_count']
                actionable.sort(key=dep_score, reverse=True)
            else:  # age
                actionable.sort(key=lambda i: i['created_utc'])

            # Format queue with recommendations
            queue = []
            for issue in actionable[:input.limit]:
                age_days = (datetime.utcnow() - datetime.fromisoformat(issue['created_utc'].rstrip('Z'))).days

                item = {
                    "key": issue['key'],
                    "title": issue['title'],
                    "type": issue['type'],
                    "status": issue['status'],
                    "priority": issue['priority'],
                    "age_days": age_days,
                    "urgency_score": calculate_urgency_score(issue)
                }

                # Add actionable recommendations
                if issue['status'] == 'proposed':
                    item['recommended_action'] = "pm_start_work"
                elif issue['status'] == 'in_progress':
                    item['recommended_action'] = "pm_log_work or pm_commit"
                elif issue['status'] == 'review':
                    item['recommended_action'] = "pm_push_branch --create-pr"
                elif issue['status'] == 'blocked' and issue.get('unblockable'):
                    item['recommended_action'] = "pm_update_status --status in_progress"

                queue.append(item)

            hints = []
            if queue:
                top_item = queue[0]
                hints.append(f"Focus on {top_item['key']}: {top_item['title']} ({top_item['recommended_action']})")
            else:
                hints.append("Queue is empty - consider pm_create_issue to add new work")

            if len(actionable) > input.limit:
                hints.append(f"Showing top {input.limit} of {len(actionable)} actionable items")

            return standard_response(
                success=True,
                message=f"Work queue for {owner}",
                data={
                    "owner": owner,
                    "queue": queue,
                    "total_assigned": len(my_issues),
                    "actionable_count": len(actionable),
                    "sort_method": input.sort_by
                },
                hints=hints
            )

    except Exception as e:
        return standard_response(
            success=False,
            message=f"Failed to get work queue: {type(e).__name__}",
            hints=["Check database connectivity"]
        )

@mcp.tool()
def pm_blocked_issues(input: BlockedIssuesInput) -> Dict[str, Any]:
    """
    Find and analyze blocked issues with unblocking recommendations.
    Helps identify systematic blockers and resolution paths.
    """
    try:
        with DatabaseSession():
            blocked = PMDatabase.get_blocked_issues(project_id=input.project_id)

            if not blocked:
                return standard_response(
                    success=True,
                    message="No blocked issues found",
                    data={"blocked_issues": [], "total_blocked": 0},
                    hints=["Great! No blockers to resolve"]
                )

            all_issues = PMDatabase.get_issues(project_id=input.project_id, limit=1000)
            result_issues = []

            for issue in blocked:
                blocked_info = {
                    'issue': issue,
                    'can_unblock': False,
                    'unblock_actions': [],
                    'days_blocked': 0
                }

                # Analyze dependencies
                deps = analyze_dependencies(issue, all_issues)
                blocked_info['can_unblock'] = deps['ready_to_work']

                if deps['ready_to_work']:
                    blocked_info['unblock_actions'].append('All dependencies completed - ready to resume')
                else:
                    pending = [d['key'] for d in deps['depends_on'] if not d['ready']]
                    blocked_info['unblock_actions'].append(f"Waiting for: {', '.join(pending)}")

                # Check how long it's been blocked
                updated = datetime.fromisoformat(issue['updated_utc'].rstrip('Z'))
                days_blocked = (datetime.utcnow() - updated).days
                blocked_info['days_blocked'] = days_blocked

                if input.include_stale and days_blocked > 7:
                    blocked_info['unblock_actions'].append(f'Blocked for {days_blocked} days - review if still valid')
                    blocked_info['stale'] = True

                # Include based on filters
                if input.actionable_only:
                    if blocked_info['can_unblock'] or (input.include_stale and days_blocked > 7):
                        result_issues.append(blocked_info)
                else:
                    result_issues.append(blocked_info)

            # Sort by actionability and age
            result_issues.sort(key=lambda x: (x['can_unblock'], -x['days_blocked']), reverse=True)

            recommendations = []
            for item in result_issues[:5]:
                if item['can_unblock']:
                    recommendations.append(f"Unblock {item['issue']['key']}: {item['issue']['title']}")

            hints = []
            actionable_count = len([i for i in result_issues if i['can_unblock']])
            if actionable_count > 0:
                hints.append(f"{actionable_count} issues can be unblocked now")
            if len(result_issues) > actionable_count:
                hints.append(f"{len(result_issues) - actionable_count} issues still waiting on dependencies")

            return standard_response(
                success=True,
                message=f"Found {len(result_issues)} blocked issues",
                data={
                    "blocked_issues": result_issues,
                    "total_blocked": len(blocked),
                    "actionable": actionable_count,
                    "recommendations": recommendations
                },
                hints=hints
            )

    except Exception as e:
        return standard_response(
            success=False,
            message=f"Failed to analyze blocked issues: {type(e).__name__}",
            hints=["Check database connectivity"]
        )

# =============== Workflow Tools ===============

@mcp.tool()
@strict_project_scope
def pm_daily_standup(input: DailyStandupInput) -> Dict[str, Any]:
    """
    Generate daily standup report with yesterday's work, today's plan, and blockers.
    Perfect for automated status updates and team synchronization.
    """
    # Project scoping handled by decorator
    owner = input.owner or Config.DEFAULT_OWNER

    try:
        with DatabaseSession():
            # Get yesterday's work logs
            yesterday = datetime.utcnow() - timedelta(days=1)
            yesterday_work = PMDatabase.get_recent_worklogs(
                project_id=input.project_id,
                limit=50
            )

            # Filter to yesterday and specific owner
            yesterday_work = [
                w for w in yesterday_work
                if (datetime.fromisoformat(w['timestamp_utc'].rstrip('Z')).date() == yesterday.date() and
                    w.get('agent') == owner)
            ]

            # Get today's planned work (in_progress issues)
            today_issues = PMDatabase.get_issues(
                project_id=input.project_id,
                owner=owner,
                status='in_progress',
                limit=10
            )

            # Get blockers
            blocked_issues = PMDatabase.get_blocked_issues(project_id=input.project_id)

            # Format based on requested format
            if input.format == 'markdown':
                content = format_standup_report(yesterday_work, today_issues, blocked_issues)
            elif input.format == 'structured':
                content = {
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "yesterday": [
                        {
                            "issue": w['issue_key'],
                            "activity": w.get('activity', 'unknown'),
                            "summary": w['summary']
                        } for w in yesterday_work
                    ],
                    "today": [
                        {
                            "issue": i['key'],
                            "title": i['title'],
                            "priority": i['priority']
                        } for i in today_issues
                    ],
                    "blockers": [
                        {
                            "issue": b['key'],
                            "title": b['title'],
                            "blocked_since": b['updated_utc']
                        } for b in blocked_issues
                    ]
                }
            else:  # text
                lines = [f"Daily Standup - {datetime.now().strftime('%Y-%m-%d')}"]
                lines.append(f"\nOwner: {owner}")
                lines.append("\nYesterday:")
                for w in yesterday_work:
                    lines.append(f"- {w['issue_key']}: {w['summary']}")
                if not yesterday_work:
                    lines.append("- No logged work yesterday")

                lines.append("\nToday:")
                for i in today_issues:
                    lines.append(f"- {i['key']}: {i['title']} ({i['priority']})")
                if not today_issues:
                    lines.append("- No active issues")

                lines.append("\nBlockers:")
                for b in blocked_issues[:3]:  # Limit to prevent spam
                    lines.append(f"- {b['key']}: {b['title']}")
                if not blocked_issues:
                    lines.append("- No blockers")

                content = "\n".join(lines)

            hints = []
            if not yesterday_work:
                hints.append("No work logged yesterday - consider pm_log_work for better tracking")
            if not today_issues:
                hints.append("No active work - use pm_my_queue to find work or pm_create_issue to add new work")
            if blocked_issues:
                hints.append(f"pm_blocked_issues to analyze {len(blocked_issues)} blocked items")

            return standard_response(
                success=True,
                message=f"Daily standup for {owner}",
                data={
                    "report": content,
                    "format": input.format,
                    "stats": {
                        "yesterday_items": len(yesterday_work),
                        "today_items": len(today_issues),
                        "blockers": len(blocked_issues)
                    },
                    "project": input.project_id,
                    "owner": owner
                },
                hints=hints
            )

    except Exception as e:
        return standard_response(
            success=False,
            message=f"Failed to generate standup: {type(e).__name__}",
            hints=["Check database connectivity", "Verify project exists"]
        )

# =============== Main Entry Point ===============

def main():
    """Main entry point for the MCP server with proper configuration handling"""
    import argparse

    parser = argparse.ArgumentParser(description="PM MCP Server - LLM-Native Project Management")
    parser.add_argument("--transport", choices=["stdio", "http", "sse"],
                       default=Config.DEFAULT_TRANSPORT,
                       help="Transport method")
    parser.add_argument("--port", type=int, default=Config.DEFAULT_PORT,
                       help="Port for HTTP transport")
    parser.add_argument("--host", default=Config.DEFAULT_HOST,
                       help="Host for HTTP transport")
    parser.add_argument("--validate-config", action="store_true",
                       help="Validate configuration and exit")
    parser.add_argument("--database-path", type=str,
                       help="Override database path")

    args = parser.parse_args()

    # Override database path if provided
    if args.database_path:
        Config.set_database_path(args.database_path)

    # Validate configuration
    if args.validate_config:
        is_valid, messages = Config.validate(strict=False)
        print(f"{'✅' if is_valid else '⚠️'} Configuration:")

        config_summary = Config.get_summary()
        for key, value in config_summary.items():
            print(f"   {key}: {value}")

        print("\nValidation messages:")
        for msg in messages:
            print(f"   - {msg}")

        return 0 if is_valid else 1

    # Initialize database connection
    try:
        PMDatabase.initialize()
        print(f"✅ Connected to database: {Config.get_database_path()}")

        # Get project count for validation
        with DatabaseSession():
            projects = PMDatabase.get_all_projects()
            print(f"   Found {len(projects)} projects")

            if projects and not Config.DEFAULT_PROJECT_ID:
                # projects is now a list of models, not dicts
                print(f"   Using first project as default: {projects[0].project_id}")

    except Exception as e:
        print(f"❌ Database error: {e}")
        print(f"   Database path: {Config.get_database_path()}")
        print(f"   Run the Jira-lite migration first if database doesn't exist")
        return 1

    # Start server
    print(f"🚀 Starting PM MCP Server")
    print(f"   Transport: {args.transport}")

    if args.transport == "stdio":
        print(f"   Mode: Standard I/O for Claude Desktop")
        mcp.run()
    else:
        print(f"   URL: http://{args.host}:{args.port}")
        # For HTTP mode, FastMCP might have different parameters
        try:
            mcp.run(port=args.port)
        except TypeError:
            # Fallback to basic run
            mcp.run()

    return 0

# =============== Initialization Tools ===============

@mcp.tool()
def pm_init_project(project_path: str = ".", project_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Initialize a new project for PM tracking. Scans directory structure,
    creates project metadata, and generates stable project ID.
    """
    try:
        with DatabaseSession():
            from datetime import datetime
            import json
            path = Path(project_path or ".").resolve()
            slug = (project_name or path.name).lower().replace(" ", "-")

            # Detect submodules by looking for subdirectories with specific patterns
            submodules = []
            for subdir in path.iterdir():
                if subdir.is_dir() and not subdir.name.startswith('.') and not subdir.name.startswith('__'):
                    # Check if it looks like a submodule (has backend, frontend, infra, etc. in name)
                    # or has its own package.json, requirements.txt, etc.
                    subdir_name = subdir.name.lower()
                    is_submodule = False

                    # Check by naming patterns
                    if any(pattern in subdir_name for pattern in ['backend', 'frontend', 'infra', 'api', 'web', 'mobile', 'testing', 'docs']):
                        is_submodule = True
                    # Check by project files
                    elif any((subdir / f).exists() for f in ['package.json', 'requirements.txt', 'pom.xml', 'build.gradle', 'Cargo.toml']):
                        is_submodule = True

                    if is_submodule:
                        # Check if it has its own git repo
                        has_git = (subdir / '.git').exists()
                        submodules.append({
                            'name': subdir.name,
                            'path': str(subdir.relative_to(path)),
                            'absolute_path': str(subdir),
                            'is_separate_repo': has_git,
                            'manage_separately': True
                        })

            metadata = {
                "vcs": {"git_root": str(path), "default_branch": "main"},
                "submodules": submodules
            }

            # upsert-like behavior
            existing = [p for p in PMDatabase.get_all_projects() if Path(p.absolute_path).resolve() == path]
            if existing:
                proj = existing[0]
                proj.project_slug = slug
                proj.metadata = json.dumps(metadata)
                proj.updated_utc = datetime.utcnow()
                proj.save()
            else:
                # simple unique id
                from database import Project
                proj = Project.create(
                    project_id=f"pn_{abs(hash(str(path))) % (10**16)}",
                    project_slug=slug,
                    absolute_path=str(path),
                    metadata=json.dumps(metadata),
                    created_utc=datetime.utcnow(),
                    updated_utc=datetime.utcnow(),
                )

            result_data = PMDatabase._project_to_dict(proj)
            if submodules:
                result_data['submodules_detected'] = len(submodules)
                result_data['submodule_names'] = [s['name'] for s in submodules]

            return ok("Project initialized with submodule detection", {"project": result_data})
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to init project: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check if path exists and is a git repository", "Verify you have write permissions"]
        )


@mcp.tool()
def pm_register_project(server_url: str = "http://127.0.0.1:1929",
                       project_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Register project with Jira-lite web UI server.
    Enables bidirectional sync between MCP and web interface.
    """
    try:
        project_id = project_id or get_default_project_id()
        if not project_id:
            return standard_response(
                success=False,
                message="No project specified and none found",
                hints=["Run pm_init_project first", "Use pm_list_projects to see available projects"]
            )

        with DatabaseSession():
            project = PMDatabase.get_project(project_id)
            if not project:
                return standard_response(
                    success=False,
                    message=f"Project {project_id} not found",
                    hints=["Run pm_init_project first"]
                )

            # Prepare registration data - convert model to dict first
            project_dict = PMDatabase._project_to_dict(project)
            registration_data = {
                'project_id': project_dict['project_id'],
                'project_slug': project_dict['project_slug'],
                'absolute_path': project_dict['absolute_path'],
                'submodules': project_dict.get('submodules', []),
                'vcs': project_dict.get('vcs', {}),
                'mcp': project_dict.get('mcp', {})
            }

            # Try to register with web UI
            try:
                import requests
                response = requests.post(
                    f"{server_url}/api/projects/register",
                    json=registration_data,
                    timeout=10
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    return standard_response(
                        success=True,
                        message=f"Registered project with web UI: {result.get('slug')}",
                        data={
                            "registration": result,
                            "dashboard_url": result.get('dashboard_url'),
                            "server_url": server_url
                        },
                        hints=[
                            f"Visit dashboard: {result.get('dashboard_url')}",
                            "pm_create_issue to start adding work"
                        ]
                    )
                else:
                    return standard_response(
                        success=False,
                        message=f"Registration failed: HTTP {response.status_code}",
                        data={"response": response.text[:200]},
                        hints=["Ensure Jira-lite server is running", f"Check server URL: {server_url}"]
                    )

            except ImportError:
                return standard_response(
                    success=False,
                    message="requests library not available for web UI registration",
                    hints=["Install requests: pip install requests", "Or register manually via web UI"]
                )
            except ScopeError as se:
                return err(str(se))
            except Exception as e:
                return standard_response(
                    success=False,
                    message=f"Registration failed: {type(e).__name__}",
                    hints=[
                        "Ensure Jira-lite server is running",
                        f"Check server URL: {server_url}",
                        "Verify network connectivity"
                    ]
                )

    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to register project: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check database connectivity", "Verify project exists"]
        )

# =============== Critical Missing Tools ===============

@mcp.tool()
@strict_project_scope
def pm_add_submodule(input: AddSubmoduleInput) -> Dict[str, Any]:
    """
    Add a new submodule to an existing project for better component organization.
    Updates project metadata to include the new submodule configuration.
    """
    try:
        with DatabaseSession():
            # Get project
            pid = _require_project_id(input.project_id)
            project = PMDatabase.get_project(pid)
            if not project:
                return standard_response(
                    success=False,
                    message=f"Project {pid} not found"
                )

            # Get current project metadata
            project_dict = PMDatabase._project_to_dict(project)
            metadata = project_dict.get('metadata', {})
            submodules = metadata.get('submodules', [])

            # Check if submodule already exists
            for sub in submodules:
                if sub['name'] == input.name:
                    return standard_response(
                        success=False,
                        message=f"Submodule '{input.name}' already exists",
                        hints=["Use a different name", "Remove existing submodule first"]
                    )

            # Construct absolute path for the submodule
            project_path = Path(project.absolute_path)
            submodule_path = project_path / input.path

            # Check if path exists
            if not submodule_path.exists():
                submodule_path.mkdir(parents=True, exist_ok=True)

            # Add new submodule
            new_submodule = {
                'name': input.name,
                'path': input.path,
                'absolute_path': str(submodule_path),
                'is_separate_repo': input.is_separate_repo,
                'manage_separately': input.manage_separately
            }
            submodules.append(new_submodule)

            # Update metadata
            metadata['submodules'] = submodules
            project.metadata = json.dumps(metadata)
            project.save()

            return standard_response(
                success=True,
                message=f"Submodule '{input.name}' added to project",
                data={
                    "submodule": new_submodule,
                    "total_submodules": len(submodules)
                },
                hints=[
                    f"pm_create_issue --submodule {input.name} to create issues for this submodule",
                    f"pm_list_issues --submodule {input.name} to filter issues"
                ]
            )

    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to add submodule: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}}
        )

@mcp.tool()
@strict_project_scope
def pm_remove_submodule(input: RemoveSubmoduleInput) -> Dict[str, Any]:
    """
    Remove a submodule from a project.
    Optionally reassigns issues from the removed submodule to another module.
    """
    try:
        with DatabaseSession():
            # Get project
            pid = _require_project_id(input.project_id)
            project = PMDatabase.get_project(pid)
            if not project:
                return standard_response(
                    success=False,
                    message=f"Project {pid} not found"
                )

            # Get current project metadata
            project_dict = PMDatabase._project_to_dict(project)
            metadata = project_dict.get('metadata', {})
            submodules = metadata.get('submodules', [])

            # Find submodule to remove
            found = False
            new_submodules = []
            for sub in submodules:
                if sub['name'] == input.name:
                    found = True
                else:
                    new_submodules.append(sub)

            if not found:
                return standard_response(
                    success=False,
                    message=f"Submodule '{input.name}' not found",
                    hints=["pm_list_submodules to see available submodules"]
                )

            # Update issues if needed
            issues_updated = 0
            if input.reassign_issues_to is not None:
                # Find all issues with this module
                issues = PMDatabase.find_issues(pid, module=input.name)
                for issue in issues:
                    issue.module = input.reassign_issues_to
                    issue.save()
                    issues_updated += 1

            # Update metadata
            metadata['submodules'] = new_submodules
            project.metadata = json.dumps(metadata)
            project.save()

            return standard_response(
                success=True,
                message=f"Submodule '{input.name}' removed from project",
                data={
                    "removed": input.name,
                    "issues_reassigned": issues_updated,
                    "reassigned_to": input.reassign_issues_to,
                    "remaining_submodules": len(new_submodules)
                }
            )

    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to remove submodule: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}}
        )

@mcp.tool()
@strict_project_scope
def pm_list_submodules(input: ListSubmodulesInput) -> Dict[str, Any]:
    """
    List all submodules in a project with optional statistics.
    Shows submodule configuration and issue distribution.
    """
    try:
        with DatabaseSession():
            # Get project
            pid = _require_project_id(input.project_id)
            project = PMDatabase.get_project(pid)
            if not project:
                return standard_response(
                    success=False,
                    message=f"Project {pid} not found"
                )

            # Get project metadata
            project_dict = PMDatabase._project_to_dict(project)
            metadata = project_dict.get('metadata', {})
            submodules = metadata.get('submodules', [])

            if not submodules:
                return standard_response(
                    success=True,
                    message="No submodules configured for this project",
                    hints=[
                        "pm_add_submodule to add a new submodule",
                        "pm_init_project to auto-detect submodules"
                    ]
                )

            # Add statistics if requested
            if input.include_stats:
                for submodule in submodules:
                    # Get issue counts for this submodule
                    issues = PMDatabase.find_issues(pid, module=submodule['name'])

                    # Calculate stats
                    stats = {
                        'total_issues': len(issues),
                        'by_status': {},
                        'by_priority': {},
                        'completion_rate': 0.0
                    }

                    for issue in issues:
                        # Status counts
                        status = issue.status
                        stats['by_status'][status] = stats['by_status'].get(status, 0) + 1

                        # Priority counts
                        priority = issue.priority
                        stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1

                    # Calculate completion rate
                    done_count = stats['by_status'].get('done', 0) + stats['by_status'].get('archived', 0)
                    if stats['total_issues'] > 0:
                        stats['completion_rate'] = round(done_count / stats['total_issues'] * 100, 1)

                    submodule['stats'] = stats

            return standard_response(
                success=True,
                message=f"Found {len(submodules)} submodules",
                data={
                    "submodules": submodules,
                    "count": len(submodules),
                    "project": {
                        "id": project_dict['project_id'],
                        "slug": project_dict['project_slug'],
                        "path": project_dict['absolute_path']
                    }
                }
            )

    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to list submodules: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}}
        )

@mcp.tool()
def pm_estimate(input: EstimateIssueInput) -> Dict[str, Any]:
    """Add effort and complexity estimates to an issue with detailed reasoning"""
    try:
        with DatabaseSession():
            issue = PMDatabase.get_issue(input.issue_key)
            if not issue:
                return err(f"Issue not found: {input.issue_key}")

            issue = PMDatabase.update_issue_planning_estimate(
                issue, effort=input.effort, complexity=input.complexity, reasoning=input.reasoning
            )

            return ok("Estimate updated", {
                "issue_key": issue.key,
                "estimated_effort": input.effort,
                "complexity": input.complexity
            }, hints=[
                f"pm_start_work --issue-key {input.issue_key} to begin implementation"
            ])
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to update estimate: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check issue exists", "Verify estimate format (e.g., '2-3 days', '1 week')"]
        )

@mcp.tool()
def pm_create_task(input: CreateTaskInput) -> Dict[str, Any]:
    """Create a task within an issue for work breakdown"""
    try:
        with DatabaseSession():
            issue = PMDatabase.get_issue(input.issue_key)
            if not issue:
                return err(f"Issue not found: {input.issue_key}")

            task = PMDatabase.create_task(issue, input.title, input.assignee, input.details)

            return ok("Task created", {
                "task_id": task.task_id,
                "title": task.title,
                "status": task.status,
                "issue_key": input.issue_key
            }, hints=[
                f"pm_update_task --task-id {task.task_id} to update status",
                f"pm_log_work --issue-key {input.issue_key} --task-id {task.task_id} to log task work"
            ])
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to create task: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check issue exists", "Verify task doesn't already exist"]
        )

@mcp.tool()
def pm_update_task(input: UpdateTaskInput) -> Dict[str, Any]:
    """Update task status, title, assignee, or details"""
    try:
        with DatabaseSession():
            task = PMDatabase.get_task(input.task_id)
            if not task:
                return err(f"Task not found: {input.task_id}")

            task = PMDatabase.update_task(task, input.title, input.status, input.assignee, input.details)

            return ok("Task updated", {
                "task_id": task.task_id,
                "title": task.title,
                "status": task.status,
                "assignee": task.assignee
            })
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to update task: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check task exists", "Verify status is valid (todo, doing, blocked, review, done)"]
        )

@mcp.tool()
def pm_git_status(project_id: Optional[str] = None) -> Dict[str, Any]:
    """Enhanced git status with issue context"""
    try:
        with DatabaseSession():
            pid = project_id or get_default_project_id()
            if not pid:
                return err("No project_id provided and PM_DEFAULT_PROJECT_ID is not set")

            project = PMDatabase.get_project(pid)
            if not project:
                return err(f"Project not found: {pid}")

            project_dict = PMDatabase._project_to_dict(project)
            repo_path = project_dict.get('vcs', {}).get('git_root', project_dict['absolute_path'])

            br = git_current_branch(repo_path)
            st = git_status(repo_path)

            data = {
                "project": project_dict['project_slug'],
                "branch": br["out"] if br["rc"] == 0 else None,
                "status": st["out"] if st["rc"] == 0 else "",
                "has_changes": bool(st["out"].strip()) if st["rc"] == 0 else False
            }

            hints = []
            if st["out"]:
                hints.append("You have local changes. Consider committing before push.")

            return ok("Git status", data, hints=hints)
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to get git status: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check if you're in a git repository", "Verify git is installed"]
        )

@mcp.tool()
def pm_push_branch(project_id: Optional[str] = None, remote: str = "origin") -> Dict[str, Any]:
    """Push current branch to remote"""
    try:
        with DatabaseSession():
            pid = project_id or get_default_project_id()
            if not pid:
                return err("No project_id provided and PM_DEFAULT_PROJECT_ID is not set")

            project = PMDatabase.get_project(pid)
            if not project:
                return err(f"Project not found: {pid}")

            project_dict = PMDatabase._project_to_dict(project)
            repo_path = project_dict.get('vcs', {}).get('git_root', project_dict['absolute_path'])

            res = git_push_current(repo_path, remote=remote)
            if res["rc"] != 0:
                return err("Push failed", {"stderr": res["err"]})

            return ok("Branch pushed", {
                "stdout": res["out"],
                "remote": remote
            }, hints=["Create a PR in your VCS host if desired."])
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to push branch: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check remote exists", "Verify git credentials are configured"]
        )

@mcp.tool()
def pm_project_dashboard(input: ProjectDashboardInput) -> Dict[str, Any]:
    """Get comprehensive project dashboard with metrics"""
    try:
        with DatabaseSession():
            pid = input.project_id or get_default_project_id()
            if not pid:
                return err("No project_id provided and PM_DEFAULT_PROJECT_ID is not set")

            project = PMDatabase.get_project(pid)
            if not project:
                return err(f"Project not found: {pid}")

            project_dict = PMDatabase._project_to_dict(project)
            metrics = PMDatabase.project_metrics(project)

            return ok("Project dashboard", {
                "project": project_dict,
                "metrics": metrics,
                "timeframe": input.timeframe
            })
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to compute dashboard: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}},
            hints=["Check database connectivity", "Verify project exists"]
        )

@mcp.tool()
def pm_reminder() -> Dict[str, Any]:
    """
    Get helpful reminders about using the PM system properly.
    This tool helps LLM agents remember to follow proper PM workflows during longer sessions.
    Returns best practices and workflow reminders for consistent PM usage.
    """
    try:
        reminders = """# PM System Workflow Reminders

## 🎯 Core Philosophy
**When developing, ALWAYS think about reporting and documenting progress from the PM perspective.**

## 📝 Essential Reminders

### 1. Always Use PM Tools Throughout Work
- **Start work properly**: Use `pm_start_work` when beginning an issue
- **Log progress regularly**: Use `pm_log_work` to document what you're doing
- **Update status**: Use `pm_update_status` when moving between stages

### 2. Use PM-Specific Git Commands
- **Always use `pm_commit`** instead of regular git commit
  - It adds proper PM trailers and links to issues
  - Example: `pm_commit --issue-key PROJ-001 --message "feat: add auth"`
- **Create branches with PM**: Use `pm_create_branch` for consistent naming

### 3. Document Everything
- **Log work regularly**: Don't wait until the end - log as you go
  - After implementing a feature: `pm_log_work --activity code`
  - After fixing a bug: `pm_log_work --activity debug`
  - When blocked: `pm_log_work --activity blocked`
- **Include artifacts**: Reference files, decisions, and blockers in logs

### 4. Status Updates Are Critical
- **Proposed** → **In Progress**: When starting work
- **In Progress** → **Review**: When ready for review
- **Review** → **Done**: After approval and merge
- **Any** → **Blocked**: When encountering blockers

### 5. Break Down Complex Work
- Use `pm_create_task` to split issues into manageable pieces
- Track progress on individual tasks with `pm_update_task`

## 🚀 Quick Workflow Checklist

Before starting work:
✅ `pm_status` - Check project health
✅ `pm_my_queue` - Get your prioritized work
✅ `pm_get_issue --issue-key XXX` - Understand the full context

During work:
✅ `pm_start_work --issue-key XXX` - Mark as in progress
✅ `pm_log_work` - Document progress (multiple times!)
✅ `pm_commit` - Use PM commits, not regular git

After completing:
✅ `pm_update_status --status done` - Mark complete
✅ `pm_log_work --activity review` - Log final summary

## 💡 Pro Tips
- Call `pm_reminder` periodically during long sessions
- Use `pm_docs` for detailed command documentation
- Run `pm_daily_standup` to generate status reports
- Check `pm_blocked_issues` to help unblock work

Remember: **The PM system is your development companion, not an afterthought!**"""

        return ok("PM workflow reminders", {
            "reminders": reminders,
            "last_reminder": datetime.utcnow().isoformat() + 'Z'
        }, hints=[
            "Call pm_reminder periodically to maintain PM discipline",
            "Use pm_docs for detailed command reference",
            "Always prefer PM tools over direct git/file operations"
        ])
    except Exception as e:
        tb = traceback.format_exc()
        return standard_response(
            success=False,
            message=f"Failed to get reminders: {type(e).__name__}",
            data={"error_details": {"error": str(e), "traceback": tb}}
        )

if __name__ == "__main__":
    sys.exit(main())