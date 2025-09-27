"""Pydantic models for PM MCP Server tools with comprehensive validation"""
from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
import json

# =============== Standard Response Model ===============

class PMOperationResult(BaseModel):
    """Standard result for all PM operations"""
    success: bool = Field(description="Whether operation succeeded")
    message: str = Field(description="Human-readable result message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Operation-specific data")
    hints: Optional[List[str]] = Field(default=None, description="Helpful hints for next steps")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')

    @classmethod
    def success_result(cls, message: str, data: Optional[Dict[str, Any]] = None,
                      hints: Optional[List[str]] = None) -> "PMOperationResult":
        """Create success result"""
        return cls(success=True, message=message, data=data, hints=hints)

    @classmethod
    def error_result(cls, message: str, details: Optional[Dict[str, Any]] = None) -> "PMOperationResult":
        """Create error result"""
        return cls(success=False, message=message, data=details)

# =============== Discovery Models ===============

class PMDocsInput(BaseModel):
    """Input for pm_docs tool"""
    section: Optional[Literal["overview", "commands", "workflow", "git", "troubleshooting"]] = Field(
        default=None,
        description="Specific section to retrieve. If omitted, returns comprehensive overview."
    )

class PMStatusInput(BaseModel):
    """Input for pm_status tool"""
    project_id: Optional[str] = Field(
        default=None,
        description="Project ID to get status for. Uses default if not specified."
    )
    verbose: bool = Field(
        default=False,
        description="Include detailed breakdowns of issues by status, priority, and module"
    )
    include_velocity: bool = Field(
        default=True,
        description="Include velocity metrics and trends"
    )

class ListIssuesInput(BaseModel):
    """Input for pm_list_issues tool"""
    project_id: Optional[str] = Field(
        default=None,
        description="Filter by project ID. Uses default if not specified."
    )
    status: Optional[Literal["proposed", "in_progress", "review", "done", "canceled", "blocked"]] = Field(
        default=None,
        description="Filter by issue status"
    )
    priority: Optional[Literal["P1", "P2", "P3", "P4", "P5"]] = Field(
        default=None,
        description="Filter by priority (P1=highest, P5=lowest)"
    )
    module: Optional[str] = Field(
        default=None,
        description="Filter by module/component name"
    )
    owner: Optional[str] = Field(
        default=None,
        description="Filter by owner (e.g., 'agent:claude-code')"
    )
    type: Optional[Literal["feature", "bug", "refactor", "chore", "spike"]] = Field(
        default=None,
        description="Filter by issue type"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of issues to return"
    )
    sort_by: Literal["updated", "created", "priority", "status"] = Field(
        default="updated",
        description="Sort order for results"
    )

class GetIssueInput(BaseModel):
    """Input for pm_get_issue tool"""
    issue_key: str = Field(
        description="Issue key (e.g., 'PROJ-001')",
        pattern=r"^[A-Z]+-\d+-\d{3}$"
    )
    include_tasks: bool = Field(
        default=True,
        description="Include associated tasks in response"
    )
    include_worklogs: bool = Field(
        default=True,
        description="Include work logs in response"
    )
    include_dependencies: bool = Field(
        default=True,
        description="Include dependency analysis"
    )

class SearchIssuesInput(BaseModel):
    """Input for pm_search_issues tool"""
    query: str = Field(
        description="Search query across titles, descriptions, and specifications",
        min_length=2
    )
    project_id: Optional[str] = Field(
        default=None,
        description="Limit search to specific project"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of results to return"
    )
    include_content: bool = Field(
        default=False,
        description="Include full content in results (slower but more context)"
    )

# =============== Planning Models ===============

class CreateIssueInput(BaseModel):
    """Input for pm_create_issue tool"""
    project_id: Optional[str] = Field(
        default=None,
        description="Project ID for the new issue. Uses default if not specified."
    )
    type: Literal["feature", "bug", "refactor", "chore", "spike"] = Field(
        description="Issue type determining workflow and branch naming"
    )
    title: str = Field(
        description="Brief, descriptive title for the issue",
        min_length=5,
        max_length=200
    )
    description: str = Field(
        description="Comprehensive description with business context, technical approach, and implementation details",
        min_length=20
    )
    priority: Literal["P1", "P2", "P3", "P4", "P5"] = Field(
        default="P3",
        description="Priority level (P1=critical/urgent, P5=nice-to-have)"
    )
    module: Optional[str] = Field(
        default=None,
        description="Module/component this issue belongs to"
    )
    acceptance_criteria: List[str] = Field(
        default_factory=list,
        description="List of specific, measurable acceptance criteria"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of issue keys this depends on"
    )
    estimated_effort: Optional[str] = Field(
        default=None,
        description="Estimated effort (e.g., '1-2 days', '1 week', '3h')"
    )
    complexity: Literal["Low", "Medium", "High", "Very High"] = Field(
        default="Medium",
        description="Technical complexity assessment"
    )
    owner: Optional[str] = Field(
        default=None,
        description="Owner assignment (defaults to current agent)"
    )
    technical_approach: Optional[str] = Field(
        default=None,
        description="Detailed technical implementation approach"
    )
    stakeholders: List[str] = Field(
        default_factory=list,
        description="List of stakeholders to notify about this issue"
    )

class UpdateIssueInput(BaseModel):
    """Input for pm_update_issue tool"""
    issue_key: str = Field(
        description="Issue key to update",
        pattern=r"^[A-Z]+-\d+-\d{3}$"
    )
    title: Optional[str] = Field(default=None, min_length=5, max_length=200)
    description: Optional[str] = Field(default=None, min_length=20)
    status: Optional[Literal["proposed", "in_progress", "review", "done", "canceled", "blocked"]] = None
    priority: Optional[Literal["P1", "P2", "P3", "P4", "P5"]] = None
    module: Optional[str] = None
    owner: Optional[str] = None
    acceptance_criteria: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    estimated_effort: Optional[str] = None
    complexity: Optional[Literal["Low", "Medium", "High", "Very High"]] = None
    notes: Optional[str] = Field(
        default=None,
        description="Notes about this update for the work log"
    )

class EstimateIssueInput(BaseModel):
    """Input for pm_estimate tool"""
    issue_key: str = Field(
        description="Issue key to estimate",
        pattern=r"^[A-Z]+-\d+-\d{3}$"
    )
    effort: str = Field(
        description="Effort estimate (e.g., '2-3 days', '1 week', '4h')"
    )
    complexity: Literal["Low", "Medium", "High", "Very High"] = Field(
        description="Complexity assessment"
    )
    confidence: Literal["Low", "Medium", "High"] = Field(
        default="Medium",
        description="Confidence level in the estimate"
    )
    reasoning: str = Field(
        description="Detailed reasoning for the estimate including approach and risks"
    )
    risks: List[str] = Field(
        default_factory=list,
        description="Identified risks that could affect the estimate"
    )

class RefineIssueInput(BaseModel):
    """Input for pm_refine_issue tool"""
    issue_key: str = Field(
        description="Issue key to refine",
        pattern=r"^[A-Z]+-\d+-\d{3}$"
    )
    aspect: Literal["requirements", "technical", "acceptance", "risks", "dependencies"] = Field(
        description="Aspect of the issue to refine"
    )
    suggestions: str = Field(
        description="Refinement suggestions, questions, or additional content",
        min_length=10
    )
    auto_apply: bool = Field(
        default=False,
        description="Automatically apply refinements without review"
    )

# =============== Execution Models ===============

class StartWorkInput(BaseModel):
    """Input for pm_start_work tool"""
    issue_key: str = Field(
        description="Issue key to start work on",
        pattern=r"^[A-Z]+-\d+-\d{3}$"
    )
    create_branch: bool = Field(
        default=True,
        description="Automatically create a git branch for this issue"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Notes about starting this work"
    )
    validate_dependencies: bool = Field(
        default=True,
        description="Check that all dependencies are completed before starting"
    )

class LogWorkInput(BaseModel):
    """Input for pm_log_work tool"""
    issue_key: str = Field(
        description="Issue key to log work against",
        pattern=r"^[A-Z]+-\d+-\d{3}$"
    )
    activity: Literal["planning", "design", "code", "test", "review", "refactor", "debug", "document", "deploy", "blocked", "research"] = Field(
        description="Type of activity performed"
    )
    summary: str = Field(
        description="Summary of work performed including key decisions and outcomes",
        min_length=10
    )
    time_spent: Optional[str] = Field(
        default=None,
        description="Time spent (e.g., '2h', '30m', '1.5d')"
    )
    artifacts: Optional[Union[str, List[Dict[str, Any]]]] = Field(
        default_factory=list,
        description="List of artifacts or JSON string list"
    )
    blockers: Optional[str] = Field(
        default=None,
        description="Description of any blockers encountered"
    )
    task_id: Optional[str] = Field(
        default=None,
        description="Optional task ID if work is on a specific task"
    )
    decisions: Optional[str] = Field(
        default=None,
        description="Key technical or architectural decisions made"
    )

    @validator("artifacts", pre=True)
    def _normalize_artifacts(cls, v):
        """Handle flexible artifact input"""
        if v is None:
            return []
        if isinstance(v, list):
            return v
        # Try JSON string
        try:
            parsed = json.loads(v)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []

class UpdateStatusInput(BaseModel):
    """Input for pm_update_status tool"""
    issue_key: str = Field(
        description="Issue key to update",
        pattern=r"^[A-Z]+-\d+-\d{3}$"
    )
    status: Literal["proposed", "in_progress", "review", "done", "canceled", "blocked"] = Field(
        description="New status with workflow validation"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Notes about this status change for stakeholders"
    )
    notify: bool = Field(
        default=True,
        description="Whether to notify stakeholders about status change"
    )
    blocker_reason: Optional[str] = Field(
        default=None,
        description="Required if status is 'blocked' - reason for blocking"
    )

class CreateTaskInput(BaseModel):
    """Input for pm_create_task tool"""
    issue_key: str = Field(
        description="Parent issue key",
        pattern=r"^[A-Z]+-\d+-\d{3}$"
    )
    title: str = Field(
        description="Task title",
        min_length=5,
        max_length=200
    )
    checklist: List[str] = Field(
        default_factory=list,
        description="Checklist items for this task"
    )
    assignee: Optional[str] = Field(
        default=None,
        description="Task assignee (defaults to issue owner)"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes for the task"
    )
    time_estimate: Optional[str] = Field(
        default=None,
        description="Time estimate for the task (e.g., '2h', '1d')"
    )
    status: Literal["todo", "doing", "blocked", "review", "done"] = Field(
        default="todo",
        description="Initial task status"
    )

# =============== Git Integration Models ===============

class GitStatusInput(BaseModel):
    """Input for pm_git_status tool"""
    issue_context: bool = Field(
        default=True,
        description="Include issue context for current branch"
    )
    show_suggestions: bool = Field(
        default=True,
        description="Show suggested next actions"
    )

class CreateBranchInput(BaseModel):
    """Input for pm_create_branch tool"""
    issue_key: str = Field(
        description="Issue key to create branch for",
        pattern=r"^[A-Z]+-\d+-\d{3}$"
    )
    branch_name: Optional[str] = Field(
        default=None,
        description="Custom branch name (auto-generated if not provided)"
    )
    base_branch: str = Field(
        default="main",
        description="Base branch to create from"
    )
    push_upstream: bool = Field(
        default=False,
        description="Push branch to upstream after creation"
    )

class CommitInput(BaseModel):
    """Input for pm_commit tool"""
    issue_key: str = Field(
        description="Issue key for commit context",
        pattern=r"^[A-Z]+-\d+-\d{3}$"
    )
    message: str = Field(
        description="Commit message (will be formatted with PM trailers)",
        min_length=5
    )
    files: List[str] = Field(
        default_factory=list,
        description="Specific files to commit (all staged if empty)"
    )
    amend: bool = Field(
        default=False,
        description="Amend previous commit"
    )
    log_work: bool = Field(
        default=True,
        description="Automatically log this commit as work activity"
    )

class PushBranchInput(BaseModel):
    """Input for pm_push_branch tool"""
    issue_key: str = Field(
        description="Issue key to push branch for",
        pattern=r"^[A-Z]+-\d+-\d{3}$"
    )
    create_pr: bool = Field(
        default=False,
        description="Create pull request after push"
    )
    pr_title: Optional[str] = Field(
        default=None,
        description="Custom PR title (auto-generated from issue if not provided)"
    )
    pr_body: Optional[str] = Field(
        default=None,
        description="Custom PR body (auto-generated from issue if not provided)"
    )
    reviewers: List[str] = Field(
        default_factory=list,
        description="List of PR reviewers"
    )
    draft: bool = Field(
        default=False,
        description="Create as draft PR"
    )

class StashWorkInput(BaseModel):
    """Input for pm_stash_work tool"""
    issue_key: str = Field(
        description="Issue key for stash context",
        pattern=r"^[A-Z]+-\d+-\d{3}$"
    )
    message: Optional[str] = Field(
        default=None,
        description="Custom stash message"
    )
    include_untracked: bool = Field(
        default=False,
        description="Include untracked files in stash"
    )

# =============== Analytics Models ===============

class ProjectDashboardInput(BaseModel):
    """Input for pm_project_dashboard tool"""
    project_id: Optional[str] = Field(
        default=None,
        description="Project ID (uses default if not specified)"
    )
    timeframe: str = Field(
        default="1w",
        description="Timeframe for metrics (e.g., '1d', '1w', '1m', '3m')",
        pattern=r"^\d+[dwmh]$"
    )
    include_velocity: bool = Field(
        default=True,
        description="Include velocity metrics"
    )
    include_burndown: bool = Field(
        default=True,
        description="Include burndown chart data"
    )
    include_health: bool = Field(
        default=True,
        description="Include project health indicators"
    )

class MyQueueInput(BaseModel):
    """Input for pm_my_queue tool"""
    owner: Optional[str] = Field(
        default=None,
        description="Owner to get queue for (defaults to current agent)"
    )
    include_blocked: bool = Field(
        default=True,
        description="Include blocked issues that might be unblockable"
    )
    sort_by: Literal["priority", "urgency", "age", "dependency"] = Field(
        default="urgency",
        description="Sort order for queue"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum items in queue"
    )

class BlockedIssuesInput(BaseModel):
    """Input for pm_blocked_issues tool"""
    project_id: Optional[str] = Field(
        default=None,
        description="Filter by project"
    )
    actionable_only: bool = Field(
        default=True,
        description="Only show blocked issues that can be unblocked now"
    )
    include_stale: bool = Field(
        default=True,
        description="Include issues blocked for > 7 days"
    )

class DependencyGraphInput(BaseModel):
    """Input for pm_dependency_graph tool"""
    issue_key: Optional[str] = Field(
        default=None,
        description="Center graph on specific issue, or show all if not specified"
    )
    project_id: Optional[str] = Field(
        default=None,
        description="Limit to specific project"
    )
    depth: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum depth of dependency traversal"
    )
    format: Literal["json", "ascii", "summary"] = Field(
        default="summary",
        description="Output format for dependency graph"
    )

# =============== Workflow Models ===============

class DailyStandupInput(BaseModel):
    """Input for pm_daily_standup tool"""
    project_id: Optional[str] = Field(
        default=None,
        description="Project ID for standup"
    )
    owner: Optional[str] = Field(
        default=None,
        description="Owner for personalized standup"
    )
    format: Literal["markdown", "text", "structured"] = Field(
        default="markdown",
        description="Output format"
    )
    include_metrics: bool = Field(
        default=True,
        description="Include velocity and progress metrics"
    )

class WeeklyReportInput(BaseModel):
    """Input for pm_weekly_report tool"""
    project_id: Optional[str] = Field(
        default=None,
        description="Project ID for report"
    )
    week_offset: int = Field(
        default=0,
        ge=-4,
        le=0,
        description="Week offset (0=current week, -1=last week)"
    )
    include_velocity: bool = Field(
        default=True,
        description="Include velocity metrics"
    )
    include_risks: bool = Field(
        default=True,
        description="Include risk assessment"
    )
    audience: Literal["technical", "executive", "stakeholder"] = Field(
        default="technical",
        description="Target audience for report tone and detail level"
    )

class CapacityPlanningInput(BaseModel):
    """Input for pm_capacity_planning tool"""
    project_id: Optional[str] = Field(
        default=None,
        description="Project to analyze"
    )
    timeframe: str = Field(
        default="2w",
        description="Planning timeframe",
        pattern=r"^\d+[dw]$"
    )
    include_estimates: bool = Field(
        default=True,
        description="Include effort estimates in capacity calculation"
    )
    team_members: List[str] = Field(
        default_factory=list,
        description="Specific team members to analyze (all if empty)"
    )

class RiskAssessmentInput(BaseModel):
    """Input for pm_risk_assessment tool"""
    project_id: Optional[str] = Field(
        default=None,
        description="Project to assess"
    )
    category: Literal["all", "technical", "timeline", "resource", "external"] = Field(
        default="all",
        description="Risk category to focus on"
    )
    critical_only: bool = Field(
        default=False,
        description="Only show critical/high-impact risks"
    )
    include_mitigation: bool = Field(
        default=True,
        description="Include suggested mitigation strategies"
    )

# =============== Advanced Models ===============

class ExtractRequirementsInput(BaseModel):
    """Input for pm_extract_requirements tool"""
    source: str = Field(
        description="Source content to extract requirements from (markdown, meeting notes, etc.)"
    )
    create_issues: bool = Field(
        default=False,
        description="Automatically create issues from extracted requirements"
    )
    project_id: Optional[str] = Field(
        default=None,
        description="Project ID for created issues"
    )
    default_priority: Literal["P1", "P2", "P3", "P4", "P5"] = Field(
        default="P3",
        description="Default priority for created issues"
    )

class GenerateTestPlanInput(BaseModel):
    """Input for pm_generate_test_plan tool"""
    issue_key: str = Field(
        description="Issue key to generate test plan for",
        pattern=r"^[A-Z]+-\d+-\d{3}$"
    )
    include_performance: bool = Field(
        default=False,
        description="Include performance testing considerations"
    )
    include_security: bool = Field(
        default=False,
        description="Include security testing considerations"
    )
    test_types: List[Literal["unit", "integration", "e2e", "performance", "security", "accessibility"]] = Field(
        default_factory=lambda: ["unit", "integration"],
        description="Types of tests to include in plan"
    )

class SecurityReviewInput(BaseModel):
    """Input for pm_security_review tool"""
    issue_key: str = Field(
        description="Issue key to review for security",
        pattern=r"^[A-Z]+-\d+-\d{3}$"
    )
    compliance: List[Literal["OWASP", "SOC2", "GDPR", "PCI", "HIPAA"]] = Field(
        default_factory=lambda: ["OWASP"],
        description="Compliance frameworks to check against"
    )
    include_checklist: bool = Field(
        default=True,
        description="Include detailed security checklist"
    )

# =============== Utility Models ===============

class WorkflowStatusInput(BaseModel):
    """Input for pm_workflow_status tool"""
    project_id: Optional[str] = Field(
        default=None,
        description="Project to analyze"
    )
    owner: Optional[str] = Field(
        default=None,
        description="Specific owner to analyze"
    )
    detailed: bool = Field(
        default=False,
        description="Include detailed workflow state analysis"
    )

class SuggestNextWorkInput(BaseModel):
    """Input for pm_suggest_next_work tool"""
    project_id: Optional[str] = Field(
        default=None,
        description="Project to suggest work from"
    )
    time_available: Optional[str] = Field(
        default=None,
        description="Available time (e.g., '2h', '1d') for work suggestions"
    )
    skills: List[str] = Field(
        default_factory=list,
        description="Agent skills/preferences for work matching"
    )
    avoid_complex: bool = Field(
        default=False,
        description="Avoid high-complexity issues"
    )

# =============== Missing Core Models ===============

class EstimateIssueInput(BaseModel):
    """Input for pm_estimate tool"""
    issue_key: str = Field(
        description="Issue key to estimate",
        pattern=r"^[A-Z]+-\d+-\d{3}$"
    )
    effort: str = Field(
        description="Effort estimate (e.g., '2-3 days', '1 week')"
    )
    complexity: Optional[str] = Field(
        default="Medium",
        description="Low|Medium|High|Very High"
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Detailed reasoning for estimate including assumptions"
    )

class CreateTaskInput(BaseModel):
    """Input for pm_create_task tool"""
    issue_key: str = Field(
        description="Parent issue key",
        pattern=r"^[A-Z]+-\d+-\d{3}$"
    )
    title: str = Field(
        description="Task title",
        min_length=5
    )
    assignee: Optional[str] = Field(
        default=None,
        description="Task assignee"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional task metadata"
    )

class UpdateTaskInput(BaseModel):
    """Input for pm_update_task tool"""
    task_id: str = Field(
        description="Task ID (e.g., PROJ-001-T1)"
    )
    title: Optional[str] = Field(
        default=None,
        description="New task title"
    )
    status: Optional[str] = Field(
        default=None,
        description="New status: todo|doing|blocked|review|done"
    )
    assignee: Optional[str] = Field(
        default=None,
        description="New assignee"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Updated task metadata"
    )

# =============== Error/Result Models ===============

class ErrorDetails(BaseModel):
    """Detailed error information"""
    error_type: str = Field(description="Type of error")
    error_code: Optional[str] = Field(default=None, description="Error code if available")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    suggestions: Optional[List[str]] = Field(default=None, description="Suggested remediation steps")

# =============== Validation Helpers ===============

def validate_issue_key(key: str) -> bool:
    """Validate issue key format"""
    import re
    return bool(re.match(r"^[A-Z]+-\d+-\d{3}$", key))

def validate_time_format(time_str: str) -> bool:
    """Validate time format"""
    import re
    return bool(re.match(r"^\d+(\.\d+)?[hmd]$", time_str))

def validate_project_id(project_id: str) -> bool:
    """Validate project ID format"""
    return project_id.startswith('pn_') and len(project_id) > 10