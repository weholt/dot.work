# FEAT-004@b8e1d4 Investigation Notes

## Issue: Implement dot-work init-work CLI command
Started: 2024-12-20T19:40:00Z

## Analysis

### Current State
- `init` command exists in cli.py but just calls `install()` - wrong behavior
- No command creates the `.work/` directory structure
- setup-issue-tracker.prompt.md defines the complete structure

### Required .work/ Structure
```
.work/
├── baseline.md               # Placeholder only (generated separately)
└── agent/
    ├── focus.md              
    ├── memory.md             
    ├── notes/                
    │   └── .gitkeep
    └── issues/
        ├── critical.md       
        ├── high.md           
        ├── medium.md         
        ├── low.md            
        ├── backlog.md        
        ├── shortlist.md      
        ├── history.md        
        └── references/       
            └── .gitkeep
```

### Required Files with Content
1. focus.md - Initial empty state
2. memory.md - Project context template
3. shortlist.md - User priority file
4. critical.md - P0 issues
5. high.md - P1 issues
6. medium.md - P2 issues
7. low.md - P3 issues
8. backlog.md - Untriaged
9. history.md - Completed issues

### Design Decision
- Add new command `init-work` (not `init` which exists)
- Create function `initialize_work_directory()` in installer.py
- Support `--target` and `--force` options
- Detect project context for memory.md (language, framework)

### Files to Modify
1. `src/dot_work/cli.py` - Add `init-work` command
2. `src/dot_work/installer.py` - Add `initialize_work_directory()` function
3. `tests/unit/test_installer.py` - Add tests for new function

### Implementation Approach
1. Create template content as module-level constants in installer.py
2. Add `initialize_work_directory()` function
3. Add `init-work` CLI command
4. Add tests for directory creation and file content
