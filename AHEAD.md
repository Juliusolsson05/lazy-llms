# Next Steps for LLM-Native PM System Enhancement

## Overview
This document outlines the next steps for improving the LLM-Native Project Management system after successfully fixing all critical MCP tool errors. We are now eating our own dog food - using the PM system to track these improvements.

## Context
- ✅ All 4 critical MCP tool errors have been fixed (pm_get_issue, pm_start_work, pm_log_work, pm_register_project)
- ✅ 21 of 21 tested MCP tools are now working correctly (100% success rate)
- ✅ Enhanced error logging with stack traces implemented for debugging
- ✅ Complete PM workflow verified: issue creation → work tracking → task management → web UI registration
- ✅ Issues created in PM system for all upcoming work (LAZY-202509-004 through LAZY-202509-008)

## Current Issues Tracking Our Work

### Priority 1 Issues
1. **LAZY-202509-004**: Add comprehensive error handling to all MCP methods
2. **LAZY-202509-005**: Update Jira-lite frontend templates to show all collected data *(IN PROGRESS)*

### Priority 2 Issues
3. **LAZY-202509-006**: Add issue deletion functionality to PM system
4. **LAZY-202509-007**: Rewrite pm_docs to focus on LLM workflow and best practices

### Priority 3 Issues
5. **LAZY-202509-008**: Remove all mock data generation functionality

## Detailed Task Breakdown

### 1. Frontend Template Updates (LAZY-202509-005) - HIGHEST PRIORITY
**Status**: IN PROGRESS
**Problem**: Jira-lite web UI templates are outdated and not displaying all the rich data we're collecting

**Current Analysis**:
- ✅ Base template (base.html) is modern with Tailwind CSS
- ✅ Dashboard template shows basic project info and issue lists
- ❌ Missing many new data fields in issue detail page
- ❌ Tasks section incomplete (no checklist support, missing details)
- ❌ Worklogs missing artifacts and context information
- ❌ No dependencies visualization
- ❌ Estimates/complexity not prominently displayed
- ❌ No delete functionality in UI

**Missing Fields to Add**:
- **Issue Details**: `technical_approach`, detailed `planning` info, `estimate_notes`, `risks`
- **Tasks**: Full checklist implementation, `time_estimate`, detailed `notes`
- **Worklogs**: `artifacts` display, `context` information, `time_spent`
- **Dependencies**: Visualization of issue dependencies
- **Estimates**: Prominent display of effort/complexity with reasoning
- **Git Integration**: Better branch/commit information display

**Next Steps**:
1. Complete reading all template files (currently at issue_detail.html)
2. Identify all missing fields by comparing with database models
3. Update issue_detail.html to show all specification fields
4. Implement proper task checklist display
5. Add worklogs with artifacts and context
6. Create dependencies visualization
7. Add delete issue functionality to UI

### 2. Comprehensive Error Handling (LAZY-202509-004)
**Problem**: Only 4 of ~24 MCP methods have detailed error logging with stack traces

**Approach**:
- Apply the same error handling pattern used in recent fixes
- Add `import traceback` usage consistently
- Enhance error responses with detailed error information
- Ensure no unhandled exceptions can crash MCP server

### 3. LLM-Focused Documentation (LAZY-202509-007)
**Problem**: Current pm_docs explains what tools do, not HOW LLMs should use them

**Required Changes**:
- Rewrite from LLM perspective ("As an LLM, you should...")
- Add workflow examples for common scenarios
- Include best practices for issue creation and tracking
- Show how to document progress effectively
- Explain when to create issues vs tasks
- Provide examples of good descriptions and work logs
- Create decision trees for workflow choices

### 4. Issue Deletion Functionality (LAZY-202509-006)
**Components Needed**:
- New MCP tool `pm_delete_issue` with safety checks
- Delete button in web UI with confirmation dialog
- Cascade delete for tasks and worklogs
- Consider soft delete with `deleted_at` field
- Audit trail for deleted issues
- Prevent deletion of issues with open dependencies

### 5. Mock Data Cleanup (LAZY-202509-008)
**Files to Review/Clean**:
- `src/jira_lite/init_db.py` - Remove mock data generation
- Any standalone mock data scripts
- Test data creation functions
- Ensure system works with empty database

## Technical Notes for Implementation

### Database Models Structure
Key models to reference when updating templates:
- **Issue**: `specification`, `planning`, `implementation`, `communication`, `analytics` JSON fields
- **Task**: `details` JSON field containing checklist and notes
- **WorkLog**: `artifacts` and `context` JSON fields with rich information
- **Project**: `metadata` JSON field with submodules and VCS info

### Error Handling Pattern
Use this pattern for all MCP methods:
```python
try:
    # method implementation
except Exception as e:
    tb = traceback.format_exc()
    return standard_response(
        success=False,
        message=f"Failed: {type(e).__name__}",
        data={"error_details": {"error": str(e), "traceback": tb}},
        hints=[...]
    )
```

### Template Update Strategy
1. Read each template file completely
2. Compare with database models to identify missing fields
3. Look at successful MCP tool responses to see data structure
4. Update HTML templates to display all available data
5. Add proper CSS styling using existing Tailwind classes
6. Test all pages to ensure data displays correctly

## Success Criteria
- [ ] All template files display comprehensive PM data
- [ ] All MCP methods have robust error handling
- [ ] Documentation guides LLMs effectively
- [ ] Issue deletion works safely with confirmations
- [ ] No mock data remains in codebase
- [ ] Web UI shows all collected information
- [ ] System is production-ready for LLM project management

## Current Work Status
- **LAZY-202509-005** is in progress
- Template file analysis partially complete
- Ready to continue with issue_detail.html updates
- Other issues ready for implementation

## Commands for Fresh Agent
1. Check current work: `pm_my_queue`
2. Get issue details: `pm_get_issue --issue-key LAZY-202509-005`
3. Log progress: `pm_log_work --issue-key LAZY-202509-005`
4. Create tasks: `pm_create_task --issue-key LAZY-202509-005`

The PM system is now fully functional and ready for iterative improvements!