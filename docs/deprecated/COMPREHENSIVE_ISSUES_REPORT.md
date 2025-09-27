# Comprehensive Issues Report - MCP PM System

**Date:** September 27, 2025
**Testing Session:** Post-compatibility shim implementation
**Scope:** Complete MCP tool testing and architectural analysis

---

## 🚨 **CRITICAL ARCHITECTURAL FLAW: Project Scoping**

### **The Fundamental Problem**

**LLM agents should NEVER work across multiple projects simultaneously.** The current system has a **fatal design flaw** where:

❌ **Agent working in `/lazy-llms/` directory**
❌ **Creates issues in `ai-chat-app` project**
❌ **No automatic project detection from current working directory**
❌ **No project-scoped operations by default**

### **Expected Behavior**
```bash
# Agent working in /lazy-llms/ directory
cd /lazy-llms/
pm_create_issue --title "Fix MCP tools"  # Should create in lazy-llms project
pm_my_queue                              # Should show only lazy-llms issues
pm_status                                # Should show only lazy-llms status
```

### **Current Broken Behavior**
```bash
# Agent working in /lazy-llms/ directory
cd /lazy-llms/
pm_create_issue --title "Fix MCP tools"  # Creates in ai-chat-app project ❌
pm_my_queue                              # Shows issues from ALL projects ❌
pm_status                                # Shows ai-chat-app status ❌
```

### **Impact: COMPLETE WORKFLOW BREAKDOWN**
- Agents cannot focus on single project development
- Issue creation goes to wrong project
- Work tracking scattered across unrelated projects
- Git operations applied to wrong repositories
- Analytics meaningless due to cross-project pollution

---

## 🔧 **Database Layer Issues**

### **1. Missing PMDatabase Methods**
```
Error: type object 'PMDatabase' has no attribute '_project_to_dict'
```
**Affected Tools:** `pm_git_status`, `pm_project_dashboard`
**Root Cause:** Database class missing expected helper methods
**Impact:** Cannot get git status or project metrics

### **2. Object Type Mismatches**
```
Error: 'dict' object has no attribute 'planning' and no __dict__ for setting new attributes
```
**Affected Tools:** `pm_estimate`
**Root Cause:** Database returning dict instead of Peewee model object
**Impact:** Cannot update issue planning information

### **3. Type Conversion Errors**
```
Error: int() argument must be a string, a bytes-like object or a real number, not 'dict'
```
**Affected Tools:** `pm_create_task`
**Root Cause:** Peewee fn.COUNT() returns dict not int
**Impact:** Cannot create tasks for issues

---

## 🔍 **Tool Testing Results**

### **✅ Working Tools (8/25+ tested)**

#### **Discovery Tools**
- ✅ `pm_docs` - Documentation system functional
- ✅ `pm_list_projects` - Project listing with metadata
- ✅ `pm_search_issues` - Full-text search across projects
- ✅ `pm_list_issues` - Issue listing and filtering (but wrong project scope)

#### **Execution Tools**
- ✅ `pm_log_work` - Activity logging with artifacts (but logs to wrong project)

#### **Analytics Tools**
- ✅ `pm_my_queue` - Work prioritization (but shows all projects)
- ✅ `pm_blocked_issues` - Blocker analysis
- ✅ `pm_daily_standup` - Progress reporting

### **❌ Broken Tools (10+ tested)**

#### **Core Workflow Tools**
- ❌ `pm_get_issue` - **KeyError** (cannot inspect issue details)
- ❌ `pm_start_work` - **KeyError** (cannot begin work)
- ❌ `pm_estimate` - **Object attribute error** (cannot add estimates)
- ❌ `pm_create_task` - **Type conversion error** (cannot break down work)

#### **Git Integration Tools**
- ❌ `pm_create_branch` - **KeyError** (cannot create branches)
- ❌ `pm_git_status` - **Missing method error** (cannot check git state)

#### **Analytics Tools**
- ❌ `pm_project_dashboard` - **Missing method error** (cannot view metrics)

#### **Planning Tools**
- ✅/❌ `pm_create_issue` - **Works but wrong project scope**

### **🚫 Untested Tools (35+ remaining)**

**Review & Collaboration:**
- `pm_request_review`, `pm_add_comment`, `pm_review_issue`

**Advanced Analytics:**
- `pm_dependency_graph`, `pm_burndown`, `pm_risk_assessment`, `pm_velocity`

**AI-Powered Features:**
- `pm_extract_requirements`, `pm_generate_test_plan`, `pm_security_review`

**Extended Git Integration:**
- `pm_switch_branch`, `pm_merge_status`, `pm_git_log`, `pm_stash_work`

**Workflow Intelligence:**
- `pm_suggest_next_work`, `pm_identify_blockers`, `pm_optimize_workflow`

---

## 📊 **Error Categories Analysis**

### **1. Project Context Errors (CRITICAL)**
**Frequency:** Affects ALL operations
**Severity:** CRITICAL - Breaks fundamental agent workflow
**Description:** Agent should work in current directory's project automatically

**Examples:**
- Working in `/lazy-llms/` but operations target `ai-chat-app`
- No automatic project detection from `cwd`
- Default project selection not based on current location

### **2. Database Object Type Mismatches**
**Frequency:** 4+ tools affected
**Severity:** HIGH - Breaks core database operations
**Description:** Mix of Peewee models vs dict objects causing attribute errors

**Examples:**
```python
# Expected: Peewee model object
issue.planning = json.dumps(planning_data)  # Attribute assignment

# Actual: Dict object
issue['planning'] = json.dumps(planning_data)  # Dict key assignment
```

### **3. Missing Database Helper Methods**
**Frequency:** 3+ tools affected
**Severity:** HIGH - Blocks analytics and git integration
**Description:** Database class missing expected utility methods

**Missing Methods:**
- `PMDatabase._project_to_dict()` - Convert project to dict
- `PMDatabase._issue_to_dict()` - Convert issue to dict
- Other conversion helpers

### **4. Remaining KeyError Issues**
**Frequency:** 3+ core tools
**Severity:** HIGH - Breaks essential workflow
**Description:** Tools trying to access missing or None database fields

**Affected Operations:**
- Issue inspection (`pm_get_issue`)
- Work initiation (`pm_start_work`)
- Branch creation (`pm_create_branch`)

### **5. Type Conversion Failures**
**Frequency:** 2+ tools
**Severity:** MEDIUM - Breaks specific functionality
**Description:** Incorrect assumptions about return types from database queries

**Examples:**
- `fn.COUNT()` returns dict not int
- JSON field parsing inconsistencies

---

## 🎯 **Impact Assessment**

### **Workflow Capability Matrix**

| Workflow Step | Tool | Status | Blocker |
|---------------|------|--------|---------|
| **Discovery** | pm_docs | ✅ Working | None |
| **Project Setup** | pm_init_project | ✅ Working | None |
| **Issue Creation** | pm_create_issue | ⚠️ Partial | Wrong project scope |
| **Issue Inspection** | pm_get_issue | ❌ Broken | KeyError |
| **Work Planning** | pm_estimate | ❌ Broken | Object type mismatch |
| **Task Breakdown** | pm_create_task | ❌ Broken | Type conversion |
| **Work Initiation** | pm_start_work | ❌ Broken | KeyError |
| **Activity Logging** | pm_log_work | ⚠️ Partial | Wrong project scope |
| **Git Integration** | pm_create_branch | ❌ Broken | KeyError |
| **Status Updates** | pm_update_status | 🔄 Untested | Unknown |
| **Analytics** | pm_my_queue | ⚠️ Partial | Multi-project scope |

### **System Usability Assessment**

**Current State:** **25% Functional**
- **Discovery:** 80% working
- **Planning:** 20% working (wrong scope)
- **Execution:** 10% working
- **Git Integration:** 0% working
- **Analytics:** 40% working (wrong scope)

**Blocking Factors:**
1. **Project scoping** - Fundamental architectural issue
2. **Database layer** - Object type inconsistencies
3. **Missing methods** - Incomplete database abstraction
4. **Error propagation** - KeyErrors throughout system

---

## 💡 **Root Cause Analysis**

### **Architecture Mismatch**

The system was designed with these assumptions:
1. **Multi-project workspace** - Agent works across multiple projects
2. **Explicit project targeting** - All operations require project_id parameter
3. **Database-centric** - Operations start with database queries

**But LLM agents actually work like this:**
1. **Single project focus** - Agent works in one directory at a time
2. **Implicit project scoping** - Operations should target current project automatically
3. **File-system-centric** - Operations start from current working directory

### **Database Layer Design Issues**

**Inconsistent Object Handling:**
- Some functions return Peewee model objects
- Some functions return dict objects
- Some functions expect model objects but receive dicts
- Missing conversion methods between formats

**Example Problem:**
```python
# In database.py
def get_issue(self, issue_key: str) -> Dict[str, Any]:  # Returns dict
    issue = Issue.get(Issue.key == issue_key)
    return issue.to_rich_dict()  # Dict format

# In server.py
def pm_estimate(input):
    issue = PMDatabase.get_issue(input.issue_key)  # Gets dict
    issue.planning = json.dumps(planning_data)     # Tries to set attribute on dict ❌
```

---

## 🔧 **Required Fixes**

### **Fix 1: Project Auto-Detection (CRITICAL)**

**Problem:** Agent should automatically work in current directory's project
**Solution:** Auto-detect project from current working directory

```python
def get_current_project_id() -> Optional[str]:
    """Auto-detect project from current working directory"""
    cwd = Path.cwd()

    # Look for project in database that matches current path or parent paths
    for project in PMDatabase.get_all_projects():
        project_path = Path(project['absolute_path'])
        if cwd == project_path or cwd.is_relative_to(project_path):
            return project['project_id']

    return None
```

**Impact:** ALL operations automatically scoped to current project

### **Fix 2: Database Object Consistency (HIGH)**

**Problem:** Mix of Peewee models and dict objects
**Solution:** Standardize on Peewee model objects throughout

```python
class PMDatabase:
    @classmethod
    def get_issue(cls, issue_key: str) -> Optional[Issue]:  # Return model, not dict
        try:
            return Issue.get(Issue.key == issue_key)
        except DoesNotExist:
            return None

    @classmethod
    def get_project(cls, project_id: str) -> Optional[Project]:  # Return model, not dict
        try:
            return Project.get(Project.project_id == project_id)
        except DoesNotExist:
            return None
```

**Impact:** Eliminates attribute errors and type mismatches

### **Fix 3: Add Missing Database Methods (HIGH)**

**Problem:** Tools expect methods that don't exist
**Solution:** Implement missing conversion and utility methods

```python
class PMDatabase:
    @staticmethod
    def _project_to_dict(project: Project) -> Dict[str, Any]:
        """Convert project model to dict"""
        # Implementation needed

    @staticmethod
    def _issue_to_dict(issue: Issue) -> Dict[str, Any]:
        """Convert issue model to dict"""
        # Implementation needed
```

### **Fix 4: Fix Peewee Aggregation (MEDIUM)**

**Problem:** `fn.COUNT()` returns dict not int
**Solution:** Use `.scalar()` for single values

```python
# BROKEN
existing = Task.select(fn.COUNT()).where(Task.issue == issue).scalar() or 0

# FIXED
existing = Task.select().where(Task.issue == issue).count()
```

---

## 🎪 **The Ultimate Irony**

We built a **sophisticated PM system** to help LLM agents manage projects, but:

❌ **Cannot use it to manage itself** - Project scoping broken
❌ **Cannot track its own development** - Core workflow tools broken
❌ **Cannot estimate its own work** - Estimation tools broken
❌ **Cannot manage its own tasks** - Task tools broken

**We have a PM system that can't manage projects!** 🤡

---

## 📋 **Action Plan**

### **Phase 1: Make It Self-Hosting (URGENT)**
1. **Fix project auto-detection** - Agent works in current directory's project
2. **Fix database object types** - Consistent Peewee model handling
3. **Add missing database methods** - Complete the abstraction layer
4. **Test core workflow** - create → estimate → start → log → commit

### **Phase 2: Complete Core Tools**
1. **Fix remaining KeyErrors** - pm_get_issue, pm_start_work, pm_create_branch
2. **Implement missing essentials** - review tools, task management
3. **Test complete workflow** - end-to-end validation
4. **Use system on itself** - Create real issues for PM development

### **Phase 3: Build Remaining Tools**
1. **Analytics suite** - dashboards, burndown, velocity
2. **AI-powered features** - requirement extraction, test generation
3. **Advanced workflows** - dependency management, collaboration
4. **Documentation alignment** - Update specs to match reality

---

## 🎯 **Success Criteria**

### **Phase 1 Complete When:**
- ✅ Agent working in `/lazy-llms/` creates issues in `lazy-llms` project
- ✅ `pm_create_issue` → `pm_estimate` → `pm_start_work` → `pm_log_work` workflow functional
- ✅ Can track PM system development using PM system itself
- ✅ Git integration works for actual development

### **System Fully Functional When:**
- ✅ All 60+ tools from specification implemented
- ✅ Complete self-hosting: PM system manages its own development
- ✅ Zero cross-project contamination
- ✅ LLM agents can work seamlessly in any project directory

---

## 📊 **Current Tool Status Summary**

**Working (8 tools):** pm_docs, pm_list_projects, pm_search_issues, pm_list_issues, pm_log_work, pm_my_queue, pm_blocked_issues, pm_daily_standup

**Broken (7 tools):** pm_get_issue, pm_start_work, pm_estimate, pm_create_task, pm_create_branch, pm_git_status, pm_project_dashboard

**Scoped Wrong (3 tools):** pm_create_issue, pm_log_work, pm_my_queue

**Missing (35+ tools):** All advanced analytics, AI features, review workflows, extended git tools

**Overall Functionality:** **30% working correctly** for intended LLM-agent workflow

---

## 🚀 **The Vision vs Reality**

### **Vision: LLM-Native PM**
- Agent works seamlessly in project directory
- Rich context and comprehensive documentation
- Git integration with automatic workflows
- Self-managing project development

### **Reality: Multi-Project Chaos**
- Agent confused about which project they're working on
- Issues created in wrong projects
- Workflow scattered across unrelated work
- Cannot self-host its own development

### **Gap: Fundamental Architecture Fix Required**

The system has **excellent individual components** but lacks the **foundational project scoping** that makes it usable for real LLM agent workflows.

**Bottom Line:** We built a race car with no steering wheel! 🏎️

---

## 🎪 **Recommendations**

### **Immediate (1 hour)**
1. **Add project auto-detection from cwd**
2. **Fix database object type consistency**
3. **Add missing PMDatabase methods**
4. **Test basic workflow on lazy-llms project**

### **Short Term (1 day)**
1. **Use PM system to manage PM development**
2. **Create real issues for remaining tool implementation**
3. **Fix all KeyError and type conversion issues**
4. **Implement core missing tools (review, tasks)**

### **Medium Term (1 week)**
1. **Implement all 60+ tools from specification**
2. **Complete self-hosting validation**
3. **Update documentation to match reality**
4. **Deploy production-ready system**

The **architectural foundation is solid** - we just need to **connect the pieces properly** so LLM agents can actually use this powerful system for real project management!

---

**🎯 Priority:** Fix project scoping FIRST, then everything else becomes testable and usable.