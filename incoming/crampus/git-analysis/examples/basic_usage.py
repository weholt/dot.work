#!/usr/bin/env python3
"""
Basic usage example for Git Analysis Tool.

This example demonstrates how to use the Git Analysis system programmatically
without using the CLI.
"""

import asyncio
from datetime import datetime
from pathlib import Path

from git_analysis import GitAnalysisService, AnalysisConfig
from git_analysis.models import ChangeAnalysis, ComparisonResult


def basic_example():
    """Demonstrate basic usage of the Git Analysis system."""
    print("🔍 Starting Git Analysis Basic Example\n")

    # Create configuration
    config = AnalysisConfig(
        repo_path=Path.cwd(),
        use_llm=False,  # Set to True if you have LLM API keys
        max_commits=50,
        output_format="json"
    )

    print(f"📂 Analyzing repository: {config.repo_path}")
    print(f"🤖 LLM enabled: {config.use_llm}")
    print(f"📊 Max commits: {config.max_commits}")
    print()

    try:
        # Create the service
        service = GitAnalysisService(config)

        # Example 1: Compare two branches
        print("1️⃣ Comparing branches...")
        try:
            result = service.compare_refs("main~10", "HEAD")
            print(f"✅ Found {result.metadata.total_commits} commits")
            print(f"📁 Files changed: {result.metadata.total_files_changed}")
            print(f"📝 Lines: +{result.metadata.total_lines_added} -{result.metadata.total_lines_deleted}")
            print(f"⚡ Total complexity: {result.metadata.total_complexity:.1f}")

            # Show top commits by complexity
            top_commits = sorted(result.commits, key=lambda x: x.complexity_score, reverse=True)[:3]
            print(f"\n🔥 Top 3 commits by complexity:")
            for i, commit in enumerate(top_commits, 1):
                print(f"   {i}. {commit.short_message} ({commit.complexity_score:.1f})")

        except Exception as e:
            print(f"❌ Branch comparison failed: {e}")

        print()

        # Example 2: Analyze a single commit
        print("2️⃣ Analyzing single commit...")
        try:
            # Get the most recent commit
            recent_commit = service.repo.head.commit
            analysis = service.analyze_commit(recent_commit.hexsha)

            print(f"✅ Analyzed commit: {analysis.commit_hash[:8]}")
            print(f"👤 Author: {analysis.author} <{analysis.email}>")
            print(f"📅 Date: {analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📝 Message: {analysis.short_message}")
            print(f"📁 Files: {len(analysis.files_changed)}")
            print(f"📊 Complexity: {analysis.complexity_score:.1f}")

            if analysis.tags:
                print(f"🏷️  Tags: {', '.join(analysis.tags)}")

            if analysis.impact_areas:
                print(f"🎯 Impact areas: {', '.join(analysis.impact_areas)}")

            if analysis.breaking_change:
                print("⚠️  Breaking change detected")

            if analysis.security_relevant:
                print("🔒 Security-relevant changes")

        except Exception as e:
            print(f"❌ Single commit analysis failed: {e}")

        print()

        # Example 3: Compare two commits
        print("3️⃣ Comparing two commits...")
        try:
            # Get recent commits
            commits = list(service.repo.iter_commits('HEAD~10..HEAD'))
            if len(commits) >= 2:
                commit_a = commits[-2]
                commit_b = commits[-1]

                comparison = service.compare_commits(commit_a.hexsha, commit_b.hexsha)

                print(f"✅ Compared commits:")
                print(f"   A: {commit_a.hexsha[:8]} - {commit_a.message.split()[0]}")
                print(f"   B: {commit_b.hexsha[:8]} - {commit_b.message.split()[0]}")
                print(f"🔗 Similarity: {comparison.similarity_score:.2f}")

                if comparison.differences:
                    print(f"🔍 Differences:")
                    for diff in comparison.differences:
                        print(f"   • {diff}")

                if comparison.common_themes:
                    print(f"🎯 Common themes:")
                    for theme in comparison.common_themes:
                        print(f"   • {theme}")

                print(f"💥 Impact: {comparison.impact_description}")
                print(f"⚠️  Regression risk: {comparison.regression_risk}")

        except Exception as e:
            print(f"❌ Commit comparison failed: {e}")

    except Exception as e:
        print(f"❌ Service initialization failed: {e}")
        print("Make sure you're in a git repository with commit history")

    print("\n✅ Basic example completed!")


def complexity_analysis_example():
    """Demonstrate complexity analysis features."""
    print("\n" + "="*60)
    print("📊 COMPLEXITY ANALYSIS EXAMPLE")
    print("="*60)

    try:
        from git_analysis.services.complexity import ComplexityCalculator
        from git_analysis.models import ChangeAnalysis, FileChange, FileCategory, ChangeType

        # Create complexity calculator
        calculator = ComplexityCalculator()

        # Example file changes
        file_changes = [
            FileChange(
                path="src/main.py",
                change_type=ChangeType.MODIFIED,
                category=FileCategory.CODE,
                lines_added=50,
                lines_deleted=10
            ),
            FileChange(
                path="tests/test_main.py",
                change_type=ChangeType.ADDED,
                category=FileCategory.TESTS,
                lines_added=30,
                lines_deleted=0
            ),
            FileChange(
                path="config/database.yaml",
                change_type=ChangeType.MODIFIED,
                category=FileCategory.CONFIG,
                lines_added=5,
                lines_deleted=2
            ),
            FileChange(
                path="README.md",
                change_type=ChangeType.MODIFIED,
                category=FileCategory.DOCUMENTATION,
                lines_added=20,
                lines_deleted=5
            ),
        ]

        # Create a mock analysis
        analysis = ChangeAnalysis(
            commit_hash="abc123def456",
            author="John Doe",
            email="john@example.com",
            timestamp=datetime.now(),
            branch="feature-branch",
            message="Add new feature with comprehensive tests",
            short_message="Add new feature with tests",
            files_changed=file_changes,
            lines_added=sum(f.lines_added for f in file_changes),
            lines_deleted=sum(f.lines_deleted for f in file_changes),
            files_added=sum(1 for f in file_changes if f.change_type == ChangeType.ADDED),
            files_deleted=sum(1 for f in file_changes if f.change_type == ChangeType.DELETED),
            files_modified=sum(1 for f in file_changes if f.change_type == ChangeType.MODIFIED),
            complexity_score=0.0,  # Will be calculated
            summary="",  # Will be generated
            tags=[],
            impact_areas=[]
        )

        # Calculate complexity
        complexity_score = calculator.calculate_complexity(analysis)
        analysis.complexity_score = complexity_score

        print(f"📊 Complexity Analysis Results:")
        print(f"   Total files changed: {len(file_changes)}")
        print(f"   Total lines added: {analysis.lines_added}")
        print(f"   Total lines deleted: {analysis.lines_deleted}")
        print(f"   Overall complexity score: {complexity_score:.1f}")

        # Calculate file-level complexity
        print(f"\n📁 File-level Complexity:")
        for file_change in file_changes:
            file_complexity = calculator.calculate_file_complexity(file_change)
            level = file_complexity['complexity_level']
            score = file_complexity['total_score']

            print(f"   {file_change.path}: {score:.1f} ({level})")
            print(f"      Category: {file_change.category.value}")
            print(f"      Change type: {file_change.change_type.value}")
            print(f"      Lines: +{file_change.lines_added} -{file_change.lines_deleted}")

        # Identify risk factors
        risk_factors = calculator.identify_risk_factors(analysis)
        if risk_factors:
            print(f"\n⚠️  Risk Factors:")
            for risk in risk_factors:
                print(f"   • {risk}")
        else:
            print(f"\n✅ No significant risk factors identified")

    except Exception as e:
        print(f"❌ Complexity analysis failed: {e}")


def demonstrate_configuration():
    """Show different configuration options."""
    print("\n" + "="*60)
    print("⚙️  CONFIGURATION EXAMPLES")
    print("="*60)

    # Example 1: Basic configuration
    basic_config = AnalysisConfig()
    print("1️⃣ Basic Configuration:")
    print(f"   Repository path: {basic_config.repo_path}")
    print(f"   LLM enabled: {basic_config.use_llm}")
    print(f"   Max commits: {basic_config.max_commits}")
    print(f"   Output format: {basic_config.output_format}")

    # Example 2: LLM-enabled configuration
    llm_config = AnalysisConfig(
        use_llm=True,
        llm_provider="anthropic",
        llm_model="claude-3-sonnet",
        llm_temperature=0.3,
        llm_max_tokens=1000
    )
    print(f"\n2️⃣ LLM Configuration:")
    print(f"   LLM enabled: {llm_config.use_llm}")
    print(f"   Provider: {llm_config.llm_provider}")
    print(f"   Model: {llm_config.llm_model}")
    print(f"   Temperature: {llm_config.llm_temperature}")
    print(f"   Max tokens: {llm_config.llm_max_tokens}")

    # Example 3: Performance configuration
    perf_config = AnalysisConfig(
        max_commits=500,
        complexity_threshold=30.0,
        parallel_processing=True,
        max_workers=8,
        timeout_seconds=600,
        cache_ttl_hours=12
    )
    print(f"\n3️⃣ Performance Configuration:")
    print(f"   Max commits: {perf_config.max_commits}")
    print(f"   Complexity threshold: {perf_config.complexity_threshold}")
    print(f"   Parallel processing: {perf_config.parallel_processing}")
    print(f"   Max workers: {perf_config.max_workers}")
    print(f"   Timeout: {perf_config.timeout_seconds}s")
    print(f"   Cache TTL: {perf_config.cache_ttl_hours}h")

    # Example 4: Filtering configuration
    filter_config = AnalysisConfig(
        file_ignore_patterns=["*.log", "*.tmp", "node_modules/*"],
        author_ignore_patterns=["bot@", "ci@", "automation@"],
        commit_message_ignore_patterns=["^Merge pull request", "^Auto-matic"],
        include_binary_files=False
    )
    print(f"\n4️⃣ Filtering Configuration:")
    print(f"   File ignore patterns: {filter_config.file_ignore_patterns}")
    print(f"   Author ignore patterns: {filter_config.author_ignore_patterns}")
    print(f"   Message ignore patterns: {filter_config.commit_message_ignore_patterns}")
    print(f"   Include binary files: {filter_config.include_binary_files}")


def show_output_formats():
    """Show different output format examples."""
    print("\n" + "="*60)
    print("📄 OUTPUT FORMAT EXAMPLES")
    print("="*60)

    # Create mock data for demonstration
    mock_analysis = ChangeAnalysis(
        commit_hash="abc123def456",
        author="John Doe",
        email="john@example.com",
        timestamp=datetime.now(),
        branch="feature-branch",
        message="Add user authentication system with JWT tokens",
        short_message="Add user authentication with JWT",
        files_changed=[],
        lines_added=150,
        lines_deleted=20,
        files_added=3,
        files_deleted=0,
        files_modified=5,
        complexity_score=65.5,
        summary="Implements comprehensive user authentication with JWT tokens, including login, registration, and password reset functionality.",
        tags=["feature", "auth", "security", "jwt"],
        impact_areas=["authentication", "security", "api"],
        breaking_change=False,
        security_relevant=True
    )

    # Table format (simulated)
    print("1️⃣ Table Format:")
    print(f"   Hash: {mock_analysis.commit_hash[:8]}")
    print(f"   Author: {mock_analysis.author}")
    print(f"   Date: {mock_analysis.timestamp.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Message: {mock_analysis.short_message}")
    print(f"   Files: {len(mock_analysis.files_changed)} (+{mock_analysis.files_added} -{mock_analysis.files_deleted})")
    print(f"   Complexity: {mock_analysis.complexity_score:.1f}")
    print(f"   Tags: {', '.join(mock_analysis.tags)}")
    print(f"   Impact: {', '.join(mock_analysis.impact_areas)}")
    print(f"   Security: {'🔒 Yes' if mock_analysis.security_relevant else 'No'}")
    print(f"   Breaking: {'⚠️ Yes' if mock_analysis.breaking_change else 'No'}")

    # JSON format
    print(f"\n2️⃣ JSON Format:")
    import json
    json_data = {
        "commit_hash": mock_analysis.commit_hash,
        "author": mock_analysis.author,
        "timestamp": mock_analysis.timestamp.isoformat(),
        "message": mock_analysis.short_message,
        "files_changed": len(mock_analysis.files_changed),
        "lines_added": mock_analysis.lines_added,
        "lines_deleted": mock_analysis.lines_deleted,
        "complexity_score": mock_analysis.complexity_score,
        "tags": mock_analysis.tags,
        "impact_areas": mock_analysis.impact_areas,
        "security_relevant": mock_analysis.security_relevant,
        "breaking_change": mock_analysis.breaking_change
    }
    print(json.dumps(json_data, indent=2)[:500] + "...")  # Truncated for display

    # YAML format
    print(f"\n3️⃣ YAML Format:")
    yaml_data = f"""commit_hash: {mock_analysis.commit_hash[:8]}
author: {mock_analysis.author}
timestamp: {mock_analysis.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
message: {mock_analysis.short_message}
files_changed: {len(mock_analysis.files_changed)}
complexity_score: {mock_analysis.complexity_score}
tags: [{', '.join(mock_analysis.tags)}]
impact_areas: [{', '.join(mock_analysis.impact_areas)}]
security_relevant: {mock_analysis.security_relevant}
breaking_change: {mock_analysis.breaking_change}"""
    print(yaml_data)


def show_use_cases():
    """Show practical use cases."""
    print("\n" + "="*60)
    print("🎯 PRACTICAL USE CASES")
    print("="*60)

    use_cases = [
        {
            "title": "Release Notes Generation",
            "description": "Automatically generate comprehensive release notes",
            "command": "git-analysis compare v1.2.0 v1.3.0 --llm --output release-notes.json",
            "benefits": ["Human-readable summaries", "Highlight breaking changes", "Contributor attribution"]
        },
        {
            "title": "Code Review Preparation",
            "description": "Summarize branch changes before code review",
            "command": "git-analysis diff-commits main feature-branch --verbose",
            "benefits": ["Risk assessment", "Change impact analysis", "Testing recommendations"]
        },
        {
            "title": "Project Timeline Analysis",
            "description": "Visualize project evolution and contributor activity",
            "command": "git-analysis contributors v1.0.0 v2.0.0 --format json",
            "benefits": ["Contributor statistics", "Velocity metrics", "Complexity trends"]
        },
        {
            "title": "Risk Assessment",
            "description": "Evaluate risk before merging changes",
            "command": "git-analysis complexity main feature-branch --threshold 40",
            "benefits": ["Identify high-risk commits", "Complexity warnings", "Change impact scoring"]
        },
        {
            "title": "Impact Analysis",
            "description": "Understand scope and impact of changes",
            "command": "git-analysis analyze abc123def456 --llm",
            "benefits": ["Affected system areas", "Dependency analysis", "Migration guidance"]
        },
        {
            "title": "Performance Monitoring",
            "description": "Track project health and development patterns",
            "command": "git-analysis releases --count 10 --llm",
            "benefits": ["Release summaries", "Trend analysis", "Quality metrics"]
        }
    ]

    for i, use_case in enumerate(use_cases, 1):
        print(f"\n{i}. {use_case['title']}")
        print(f"   Description: {use_case['description']}")
        print(f"   Command: {use_case['command']}")
        print(f"   Benefits: {', '.join(use_case['benefits'])}")


async def main():
    """Run all examples."""
    print("🎯 Git Analysis - Usage Examples")
    print("="*60)

    # Show basic usage
    basic_example()

    # Show complexity analysis
    complexity_analysis_example()

    # Show configuration options
    demonstrate_configuration()

    # Show output formats
    show_output_formats()

    # Show use cases
    show_use_cases()

    print("\n" + "="*60)
    print("🎉 ALL EXAMPLES COMPLETED!")
    print("="*60)

    print("\n💡 Next steps:")
    print("   1. Run in your repository: git-analysis compare main feature-branch")
    print("   2. Try LLM analysis: git-analysis compare main feature --llm")
    print("   3. Export results: git-analysis compare main feature --format json --output results.json")
    print("   4. Set up configuration: git-analysis --help")
    print("   5. Check complexity: git-analysis complexity main feature --threshold 30")


if __name__ == "__main__":
    asyncio.run(main())