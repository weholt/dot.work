# Regression Guard Integration Examples

## GitHub Actions Integration

### Basic Pull Request Validation

```yaml
# .github/workflows/regression-guard.yml
name: Regression Guard

on:
  pull_request:
    branches: [main, develop]

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install regression-guard
          pip install -r requirements.txt
      
      - name: Find task ID
        id: find-task
        run: |
          if [ -d ".work/tasks" ]; then
            TASK_ID=$(ls -t .work/tasks | head -n 1)
            echo "task_id=$TASK_ID" >> $GITHUB_OUTPUT
            echo "Found task: $TASK_ID"
          else
            echo "No tasks found"
            exit 1
          fi
      
      - name: Run validation
        run: |
          regression-guard finalize ${{ steps.find-task.outputs.task_id }}
      
      - name: Upload validation report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: regression-report
          path: .work/tasks/${{ steps.find-task.outputs.task_id }}/final_report.md
```

### With PR Comments

```yaml
# .github/workflows/regression-guard-comment.yml
name: Regression Guard with PR Comments

on:
  pull_request:
    branches: [main]

permissions:
  contents: read
  pull-requests: write

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install regression-guard
        run: pip install regression-guard
      
      - name: Run validation
        id: validation
        run: |
          TASK_ID=$(ls -t .work/tasks 2>/dev/null | head -n 1)
          if [ -z "$TASK_ID" ]; then
            echo "No task found"
            exit 0
          fi
          
          regression-guard finalize $TASK_ID || true
          echo "task_id=$TASK_ID" >> $GITHUB_OUTPUT
      
      - name: Comment PR with results
        if: steps.validation.outputs.task_id
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const taskId = '${{ steps.validation.outputs.task_id }}';
            const reportPath = `.work/tasks/${taskId}/final_report.md`;
            
            if (fs.existsSync(reportPath)) {
              const report = fs.readFileSync(reportPath, 'utf8');
              github.rest.issues.createComment({
                issue_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo,
                body: `## Regression Guard Validation\n\n${report}`
              });
            }
```

## Pre-commit Hook

### `.pre-commit-config.yaml`

```yaml
repos:
  - repo: local
    hooks:
      - id: regression-guard-subtask
        name: Regression Guard - Validate Current Subtask
        entry: regression-guard-pre-commit
        language: system
        pass_filenames: false
        stages: [commit]
```

### Custom Pre-commit Script

```bash
#!/bin/bash
# Save as: .git/hooks/pre-commit
# Make executable: chmod +x .git/hooks/pre-commit

set -e

# Find the most recent task
TASK_DIR=".work/tasks"
if [ ! -d "$TASK_DIR" ]; then
    echo "No regression guard tasks found"
    exit 0
fi

TASK_ID=$(ls -t "$TASK_DIR" | head -n 1)
if [ -z "$TASK_ID" ]; then
    echo "No active task found"
    exit 0
fi

# Get list of modified files
MODIFIED_FILES=$(git diff --cached --name-only)

# Find which subtask is being worked on (based on modified files)
# This is a simple heuristic - customize for your needs
echo "Checking for relevant subtasks..."

# For now, just check if any subtasks are pending validation
MANIFEST="$TASK_DIR/$TASK_ID/manifest.json"
if [ -f "$MANIFEST" ]; then
    echo "Task: $TASK_ID"
    echo "Remember to validate your subtasks before committing:"
    echo "  regression-guard validate <subtask-id>"
fi
```

## GitLab CI Integration

```yaml
# .gitlab-ci.yml
stages:
  - validate

regression-guard:
  stage: validate
  image: python:3.11
  
  before_script:
    - pip install regression-guard
    - pip install -r requirements.txt
  
  script:
    - |
      TASK_ID=$(ls -t .work/tasks 2>/dev/null | head -n 1)
      if [ -n "$TASK_ID" ]; then
        regression-guard finalize $TASK_ID
      else
        echo "No tasks to validate"
      fi
  
  artifacts:
    when: always
    paths:
      - .work/tasks/*/final_report.md
    reports:
      junit: .work/tasks/*/junit.xml
  
  only:
    - merge_requests
```

## Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install regression-guard'
                sh 'pip install -r requirements.txt'
            }
        }
        
        stage('Validate') {
            steps {
                script {
                    def taskId = sh(
                        script: 'ls -t .work/tasks 2>/dev/null | head -n 1',
                        returnStdout: true
                    ).trim()
                    
                    if (taskId) {
                        sh "regression-guard finalize ${taskId}"
                    } else {
                        echo 'No tasks to validate'
                    }
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: '.work/tasks/*/final_report.md', allowEmptyArchive: true
        }
    }
}
```

## Docker Integration

### Dockerfile for Validation

```dockerfile
# Dockerfile.regression-guard
FROM python:3.11-slim

WORKDIR /app

# Install regression-guard
RUN pip install --no-cache-dir regression-guard

# Copy project files
COPY . .

# Install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run validation
CMD ["sh", "-c", "TASK_ID=$(ls -t .work/tasks | head -n 1) && regression-guard finalize $TASK_ID"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  regression-guard:
    build:
      context: .
      dockerfile: Dockerfile.regression-guard
    volumes:
      - ./.work:/app/.work
      - ./tests:/app/tests
    environment:
      - PYTHONUNBUFFERED=1
```

## VS Code Integration

### Task Configuration

```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Regression Guard: Start Task",
      "type": "shell",
      "command": "regression-guard",
      "args": [
        "start",
        "${input:taskDescription}"
      ],
      "problemMatcher": [],
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Regression Guard: Validate Subtask",
      "type": "shell",
      "command": "regression-guard",
      "args": [
        "validate",
        "${input:subtaskId}"
      ],
      "problemMatcher": []
    },
    {
      "label": "Regression Guard: Finalize Task",
      "type": "shell",
      "command": "regression-guard",
      "args": [
        "finalize",
        "${input:taskId}"
      ],
      "problemMatcher": []
    },
    {
      "label": "Regression Guard: Show Status",
      "type": "shell",
      "command": "regression-guard",
      "args": [
        "status",
        "${input:taskId}"
      ],
      "problemMatcher": []
    }
  ],
  "inputs": [
    {
      "id": "taskDescription",
      "type": "promptString",
      "description": "Task description"
    },
    {
      "id": "subtaskId",
      "type": "promptString",
      "description": "Subtask ID"
    },
    {
      "id": "taskId",
      "type": "promptString",
      "description": "Task ID"
    }
  ]
}
```

## Make Integration

```makefile
# Makefile
.PHONY: rg-start rg-validate rg-finalize rg-status

# Start new regression guard task
rg-start:
	@read -p "Task description: " desc; \
	regression-guard start "$$desc"

# Validate current subtask
rg-validate:
	@read -p "Subtask ID: " subtask; \
	regression-guard validate $$subtask

# Finalize task
rg-finalize:
	@TASK_ID=$$(ls -t .work/tasks | head -n 1); \
	regression-guard finalize $$TASK_ID

# Show task status
rg-status:
	@TASK_ID=$$(ls -t .work/tasks | head -n 1); \
	regression-guard status $$TASK_ID

# Full development workflow
dev-workflow: rg-start
	@echo "Implement your changes, then run: make rg-validate"
	@echo "When all subtasks are done, run: make rg-finalize"
```

## Python Script Integration

```python
#!/usr/bin/env python3
"""
Custom workflow integration with Regression Guard.
"""

import subprocess
import sys
from pathlib import Path


def run_regression_guard(command: list[str]) -> bool:
    """Run regression-guard command."""
    try:
        result = subprocess.run(
            ["regression-guard"] + command,
            capture_output=True,
            text=True,
            check=False,
        )
        print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False


def main():
    """Main workflow."""
    # Start task
    if not run_regression_guard(["start", "Implement feature X"]):
        sys.exit(1)
    
    # Get task ID
    tasks_dir = Path(".work/tasks")
    task_id = sorted(tasks_dir.iterdir())[-1].name
    
    print(f"Task started: {task_id}")
    print("Implement subtasks and validate...")
    
    # Example: Validate specific subtask
    # if not run_regression_guard(["validate", "subtask-1-create"]):
    #     sys.exit(1)
    
    # Finalize when done
    # if not run_regression_guard(["finalize", task_id]):
    #     sys.exit(1)


if __name__ == "__main__":
    main()
```

## Monitoring and Notifications

### Slack Notification Script

```bash
#!/bin/bash
# slack-notify.sh

WEBHOOK_URL="YOUR_SLACK_WEBHOOK_URL"
TASK_ID=$1
REPORT_PATH=".work/tasks/$TASK_ID/final_report.md"

if [ -f "$REPORT_PATH" ]; then
    STATUS=$(grep -m 1 "Status:" "$REPORT_PATH" | sed 's/.*Status: //')
    
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"Regression Guard: Task $TASK_ID - $STATUS\"}" \
        $WEBHOOK_URL
fi
```

### Email Notification (Python)

```python
import smtplib
from email.mime.text import MIMEText
from pathlib import Path


def send_validation_report(task_id: str, recipient: str):
    """Send validation report via email."""
    report_path = Path(f".work/tasks/{task_id}/final_report.md")
    
    if not report_path.exists():
        return
    
    report = report_path.read_text()
    
    msg = MIMEText(report)
    msg['Subject'] = f'Regression Guard: Task {task_id}'
    msg['From'] = 'regression-guard@example.com'
    msg['To'] = recipient
    
    with smtplib.SMTP('localhost') as server:
        server.send_message(msg)
```
