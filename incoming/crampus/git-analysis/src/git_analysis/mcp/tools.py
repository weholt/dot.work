"""MCP tools for Git Analysis integration."""

import json
from typing import Any, Dict, List, Optional
from pathlib import Path

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = None
    stdio_server = None
    Tool = None
    TextContent = None

from ..models import AnalysisConfig
from ..services import GitAnalysisService
from ..utils import setup_logging


def create_git_analysis_tools() -> List[Tool]:
    """Create MCP tools for git analysis."""
    if not MCP_AVAILABLE:
        return []

    return [
        Tool(
            name="analyze_git_history",
            description="Analyze git history between two references with detailed metrics and insights",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_ref": {
                        "type": "string",
                        "description": "Source git reference (branch, tag, or commit hash)"
                    },
                    "to_ref": {
                        "type": "string",
                        "description": "Target git reference (branch, tag, or commit hash)"
                    },
                    "repo_path": {
                        "type": "string",
                        "description": "Path to git repository (default: current directory)",
                        "default": "."
                    },
                    "use_llm": {
                        "type": "boolean",
                        "description": "Use LLM for enhanced summaries (requires API keys)",
                        "default": False
                    },
                    "max_commits": {
                        "type": "integer",
                        "description": "Maximum number of commits to analyze",
                        "default": 100
                    },
                    "include_detailed_files": {
                        "type": "boolean",
                        "description": "Include detailed file analysis in results",
                        "default": False
                    }
                },
                "required": ["from_ref", "to_ref"]
            }
        ),
        Tool(
            name="compare_git_branches",
            description="Compare two git branches with comprehensive analysis and risk assessment",
            inputSchema={
                "type": "object",
                "properties": {
                    "branch_a": {
                        "type": "string",
                        "description": "First branch name"
                    },
                    "branch_b": {
                        "type": "string",
                        "description": "Second branch name"
                    },
                    "repo_path": {
                        "type": "string",
                        "description": "Path to git repository",
                        "default": "."
                    },
                    "risk_threshold": {
                        "type": "number",
                        "description": "Complexity threshold for risk assessment",
                        "default": 50.0
                    },
                    "include_contributors": {
                        "type": "boolean",
                        "description": "Include contributor statistics",
                        "default": True
                    }
                },
                "required": ["branch_a", "branch_b"]
            }
        ),
        Tool(
            name="get_commit_analysis",
            description="Get detailed analysis of a single commit including complexity and impact",
            inputSchema={
                "type": "object",
                "properties": {
                    "commit_hash": {
                        "type": "string",
                        "description": "Git commit hash to analyze"
                    },
                    "repo_path": {
                        "type": "string",
                        "description": "Path to git repository",
                        "default": "."
                    },
                    "include_file_details": {
                        "type": "boolean",
                        "description": "Include detailed file change analysis",
                        "default": True
                    },
                    "generate_summary": {
                        "type": "boolean",
                        "description": "Generate AI-powered summary (requires LLM)",
                        "default": False
                    }
                },
                "required": ["commit_hash"]
            }
        ),
        Tool(
            name="get_complexity_report",
            description="Generate complexity analysis and identify high-risk changes",
            inputSchema={
                "type": "object",
                "properties": {
                    "from_ref": {
                        "type": "string",
                        "description": "Source reference"
                    },
                    "to_ref": {
                        "type": "string",
                        "description": "Target reference"
                    },
                    "repo_path": {
                        "type": "string",
                        "description": "Path to git repository",
                        "default": "."
                    },
                    "complexity_threshold": {
                        "type": "number",
                        "description": "Complexity threshold for highlighting",
                        "default": 50.0
                    },
                    "include_file_analysis": {
                        "type": "boolean",
                        "description": "Include per-file complexity analysis",
                        "default": True
                    }
                },
                "required": ["from_ref", "to_ref"]
            }
        ),
        Tool(
            name="list_repository_tags",
            description="List all tags (releases) in the repository with basic information",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo_path": {
                        "type": "string",
                        "description": "Path to git repository",
                        "default": "."
                    },
                    "sort_by_date": {
                        "type": "boolean",
                        "description": "Sort tags by commit date (newest first)",
                        "default": True
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of tags to return",
                        "default": 50
                    }
                },
                "required": []
            }
        )
    ]


class GitAnalysisMCPServer:
    """MCP server for Git Analysis functionality."""

    def __init__(self):
        if not MCP_AVAILABLE:
            raise ImportError("MCP package not available. Install with: pip install mcp")

        self.server = Server("git-analysis")
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up MCP tool handlers."""

        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available tools."""
            return create_git_analysis_tools()

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            try:
                if name == "analyze_git_history":
                    result = await self._analyze_git_history(arguments)
                elif name == "compare_git_branches":
                    result = await self._compare_git_branches(arguments)
                elif name == "get_commit_analysis":
                    result = await self._get_commit_analysis(arguments)
                elif name == "get_complexity_report":
                    result = await self._get_complexity_report(arguments)
                elif name == "list_repository_tags":
                    result = await self._list_repository_tags(arguments)
                else:
                    raise ValueError(f"Unknown tool: {name}")

                return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

            except Exception as e:
                error_result = {
                    "error": str(e),
                    "tool": name,
                    "arguments": arguments
                }
                return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

    async def _analyze_git_history(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze git history between two references."""
        from_ref = args["from_ref"]
        to_ref = args["to_ref"]
        repo_path = Path(args.get("repo_path", "."))
        use_llm = args.get("use_llm", False)
        max_commits = args.get("max_commits", 100)
        include_detailed_files = args.get("include_detailed_files", False)

        # Create configuration
        config = AnalysisConfig(
            repo_path=repo_path,
            use_llm=use_llm,
            max_commits=max_commits
        )

        # Create service and analyze
        service = GitAnalysisService(config)
        result = service.compare_refs(from_ref, to_ref)

        # Convert to MCP-friendly format
        mcp_result = {
            "metadata": {
                "from_ref": result.metadata.from_ref,
                "to_ref": result.metadata.to_ref,
                "total_commits": result.metadata.total_commits,
                "total_files_changed": result.metadata.total_files_changed,
                "total_lines_added": result.metadata.total_lines_added,
                "total_lines_deleted": result.metadata.total_lines_deleted,
                "total_complexity": result.metadata.total_complexity,
                "time_span_days": result.metadata.time_span_days,
                "branches_involved": result.metadata.branches_involved
            },
            "aggregate_summary": result.aggregate_summary,
            "highlights": result.highlights,
            "risk_assessment": result.risk_assessment,
            "recommendations": result.recommendations,
            "file_categories": {cat.value: count for cat, count in result.file_categories.items()},
            "complexity_distribution": result.complexity_distribution,
            "contributors": {
                name: {
                    "name": stats.name,
                    "commits": stats.commits,
                    "lines_added": stats.lines_added,
                    "lines_deleted": stats.lines_deleted,
                    "files_touched": stats.files_touched,
                    "complexity_contribution": stats.complexity_contribution,
                }
                for name, stats in result.contributors.items()
            }
        }

        # Include commits (limited)
        if include_detailed_files:
            mcp_result["commits"] = [
                {
                    "hash": commit.commit_hash,
                    "author": commit.author,
                    "timestamp": commit.timestamp.isoformat(),
                    "message": commit.short_message,
                    "files_changed": len(commit.files_changed),
                    "lines_added": commit.lines_added,
                    "lines_deleted": commit.lines_deleted,
                    "complexity_score": commit.complexity_score,
                    "summary": commit.summary,
                    "tags": commit.tags,
                    "impact_areas": commit.impact_areas,
                    "breaking_change": commit.breaking_change,
                    "security_relevant": commit.security_relevant,
                    "files": [
                        {
                            "path": file.path,
                            "change_type": file.change_type.value,
                            "category": file.category.value,
                            "lines_added": file.lines_added,
                            "lines_deleted": file.lines_deleted
                        }
                        for file in commit.files_changed
                    ]
                }
                for commit in result.commits[:20]  # Limit to 20 commits
            ]
        else:
            mcp_result["commits"] = [
                {
                    "hash": commit.commit_hash[:8],
                    "author": commit.author,
                    "message": commit.short_message,
                    "complexity_score": commit.complexity_score,
                    "tags": commit.tags
                }
                for commit in result.commits
            ]

        return mcp_result

    async def _compare_git_branches(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two git branches."""
        branch_a = args["branch_a"]
        branch_b = args["branch_b"]
        repo_path = Path(args.get("repo_path", "."))
        risk_threshold = args.get("risk_threshold", 50.0)
        include_contributors = args.get("include_contributors", True)

        # Create configuration
        config = AnalysisConfig(
            repo_path=repo_path,
            complexity_threshold=risk_threshold,
            max_commits=200
        )

        # Analyze
        service = GitAnalysisService(config)
        result = service.compare_refs(branch_a, branch_b)

        # Branch-specific analysis
        high_complexity_commits = [
            c for c in result.commits if c.complexity_score >= risk_threshold
        ]

        breaking_changes = [c for c in result.commits if c.breaking_change]
        security_changes = [c for c in result.commits if c.security_relevant]

        comparison_result = {
            "comparison": {
                "branch_a": branch_a,
                "branch_b": branch_b,
                "commits_analyzed": len(result.commits),
                "files_changed": result.metadata.total_files_changed,
                "lines_added": result.metadata.total_lines_added,
                "lines_deleted": result.metadata.total_lines_deleted,
                "time_span_days": result.metadata.time_span_days
            },
            "risk_assessment": {
                "overall_risk": result.risk_assessment,
                "high_complexity_commits": len(high_complexity_commits),
                "breaking_changes": len(breaking_changes),
                "security_changes": len(security_changes),
                "average_complexity": result.metadata.total_complexity / len(result.commits)
            },
            "key_changes": {
                "high_complexity": [
                    {
                        "hash": c.commit_hash[:8],
                        "message": c.short_message,
                        "complexity": c.complexity_score,
                        "author": c.author
                    }
                    for c in sorted(high_complexity_commits, key=lambda x: x.complexity_score, reverse=True)[:5]
                ],
                "breaking": [
                    {
                        "hash": c.commit_hash[:8],
                        "message": c.short_message,
                        "author": c.author
                    }
                    for c in breaking_changes
                ],
                "security": [
                    {
                        "hash": c.commit_hash[:8],
                        "message": c.short_message,
                        "author": c.author
                    }
                    for c in security_changes
                ]
            },
            "summary": result.aggregate_summary,
            "highlights": result.highlights,
            "recommendations": result.recommendations
        }

        if include_contributors:
            comparison_result["contributors"] = {
                name: {
                    "commits": stats.commits,
                    "complexity": stats.complexity_contribution,
                    "lines_changed": stats.lines_added + stats.lines_deleted
                }
                for name, stats in result.contributors.items()
            }

        return comparison_result

    async def _get_commit_analysis(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed analysis of a single commit."""
        commit_hash = args["commit_hash"]
        repo_path = Path(args.get("repo_path", "."))
        include_file_details = args.get("include_file_details", True)
        generate_summary = args.get("generate_summary", False)

        # Create configuration
        config = AnalysisConfig(
            repo_path=repo_path,
            use_llm=generate_summary,
            detailed_file_analysis=include_file_details
        )

        # Analyze commit
        service = GitAnalysisService(config)
        analysis = service.analyze_commit(commit_hash)

        # Convert to MCP format
        result = {
            "commit": {
                "hash": analysis.commit_hash,
                "short_hash": analysis.commit_hash[:8],
                "author": analysis.author,
                "email": analysis.email,
                "timestamp": analysis.timestamp.isoformat(),
                "message": analysis.message,
                "short_message": analysis.short_message,
                "branch": analysis.branch,
                "tags": analysis.tags
            },
            "changes": {
                "files_changed": len(analysis.files_changed),
                "files_added": analysis.files_added,
                "files_deleted": analysis.files_deleted,
                "files_modified": analysis.files_modified,
                "lines_added": analysis.lines_added,
                "lines_deleted": analysis.lines_deleted
            },
            "analysis": {
                "complexity_score": analysis.complexity_score,
                "impact_areas": analysis.impact_areas,
                "summary": analysis.summary,
                "breaking_change": analysis.breaking_change,
                "security_relevant": analysis.security_relevant,
                "risk_factors": []  # Would be populated by complexity calculator
            }
        }

        if include_file_details:
            result["files"] = []
            for file_change in analysis.files_changed:
                file_info = {
                    "path": file_change.path,
                    "change_type": file_change.change_type.value,
                    "category": file_change.category.value,
                    "lines_added": file_change.lines_added,
                    "lines_deleted": file_change.lines_deleted,
                    "binary_file": file_change.binary_file
                }
                if file_change.old_path:
                    file_info["old_path"] = file_change.old_path
                result["files"].append(file_info)

        return result

    async def _get_complexity_report(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Generate complexity analysis and identify high-risk changes."""
        from_ref = args["from_ref"]
        to_ref = args["to_ref"]
        repo_path = Path(args.get("repo_path", "."))
        complexity_threshold = args.get("complexity_threshold", 50.0)
        include_file_analysis = args.get("include_file_analysis", True)

        # Create configuration
        config = AnalysisConfig(
            repo_path=repo_path,
            complexity_threshold=complexity_threshold
        )

        # Analyze
        service = GitAnalysisService(config)
        result = service.compare_refs(from_ref, to_ref)

        # Generate complexity report
        high_complexity_commits = [
            c for c in result.commits if c.complexity_score >= complexity_threshold
        ]

        # Risk assessment
        risk_levels = {
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0
        }

        for commit in result.commits:
            if commit.complexity_score < 20:
                risk_levels["low"] += 1
            elif commit.complexity_score < 40:
                risk_levels["medium"] += 1
            elif commit.complexity_score < 60:
                risk_levels["high"] += 1
            else:
                risk_levels["critical"] += 1

        complexity_report = {
            "summary": {
                "total_commits": len(result.commits),
                "average_complexity": result.metadata.total_complexity / len(result.commits),
                "max_complexity": max(c.complexity_score for c in result.commits),
                "high_complexity_count": len(high_complexity_commits),
                "complexity_threshold": complexity_threshold
            },
            "risk_distribution": risk_levels,
            "high_complexity_commits": [
                {
                    "hash": c.commit_hash[:8],
                    "author": c.author,
                    "message": c.short_message,
                    "complexity_score": c.complexity_score,
                    "files_changed": len(c.files_changed),
                    "lines_changed": c.lines_added + c.lines_deleted,
                    "tags": c.tags,
                    "impact_areas": c.impact_areas,
                    "breaking_change": c.breaking_change,
                    "security_relevant": c.security_relevant
                }
                for c in sorted(high_complexity_commits, key=lambda x: x.complexity_score, reverse=True)
            ],
            "recommendations": [
                f"Consider breaking down {len(high_complexity_commits)} high-complexity commits" if high_complexity_commits else "Complexity levels are acceptable",
                "Review breaking changes for migration requirements" if any(c.breaking_change for c in result.commits) else "No breaking changes detected",
                "Consider additional testing for security-related changes" if any(c.security_relevant for c in result.commits) else "No security concerns detected"
            ]
        }

        if include_file_analysis:
            complexity_report["file_analysis"] = {
                "most_complex_files": [
                    {
                        "path": file_info["path"],
                        "complexity_score": file_info["complexity_score"],
                        "commits": file_info["commits"],
                        "lines_changed": file_info["total_lines_added"] + file_info["total_lines_deleted"]
                    }
                    for file_info in result.top_complex_files[:10]
                ],
                "file_categories": {cat.value: count for cat, count in result.file_categories.items()},
                "complexity_distribution": result.complexity_distribution
            }

        return complexity_report

    async def _list_repository_tags(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List all tags in the repository."""
        repo_path = Path(args.get("repo_path", "."))
        sort_by_date = args.get("sort_by_date", True)
        limit = args.get("limit", 50)

        try:
            import git
            repo = git.Repo(repo_path)
            tags = list(repo.tags)

            # Get tag information
            tag_info = []
            for tag in tags:
                try:
                    commit = tag.commit
                    tag_data = {
                        "name": tag.name,
                        "commit_hash": commit.hexsha,
                        "short_hash": commit.hexsha[:8],
                        "author": commit.author.name,
                        "date": commit.committed_date.isoformat(),
                        "message": commit.message.strip().split('\n')[0] if commit.message else ""
                    }
                    tag_info.append(tag_data)
                except:
                    # Skip tags that can't be resolved
                    continue

            # Sort
            if sort_by_date:
                tag_info.sort(key=lambda x: x["date"], reverse=True)
            else:
                tag_info.sort(key=lambda x: x["name"])

            # Limit results
            if limit:
                tag_info = tag_info[:limit]

            return {
                "repository": str(repo_path),
                "total_tags": len(tag_info),
                "tags": tag_info,
                "sort_by_date": sort_by_date,
                "limit_applied": limit
            }

        except Exception as e:
            return {
                "error": f"Failed to list tags: {str(e)}",
                "repository": str(repo_path)
            }


def create_server() -> Optional[GitAnalysisMCPServer]:
    """Create and return the MCP server instance."""
    if not MCP_AVAILABLE:
        return None

    return GitAnalysisMCPServer()


def run_server():
    """Run the MCP server."""
    if not MCP_AVAILABLE:
        print("MCP package not available. Install with: pip install mcp")
        return

    server = GitAnalysisMCPServer()

    print("Git Analysis MCP Server starting...")
    print("Available tools:")
    for tool in create_git_analysis_tools():
        print(f"  - {tool.name}: {tool.description}")

    print("\nServer ready. Use Ctrl+C to stop.")

    try:
        stdio_server(server.server)
    except KeyboardInterrupt:
        print("\nServer stopped.")


if __name__ == "__main__":
    run_server()