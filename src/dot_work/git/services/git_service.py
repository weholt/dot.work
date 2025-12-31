"""Main Git Analysis Service for comparing and analyzing git history."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import git as gitpython
from tqdm import tqdm  # type: ignore[import-untyped]

from dot_work.git.models import (
    AnalysisConfig,
    AnalysisProgress,
    ChangeAnalysis,
    ChangeType,
    CommitInfo,
    ComparisonDiff,
    ComparisonMetadata,
    ComparisonResult,
    ContributorStats,
    FileCategory,
    FileChange,
)

from .cache import AnalysisCache
from .complexity import ComplexityCalculator
from .file_analyzer import FileAnalyzer
from .llm_summarizer import LLMSummarizer
from .tag_generator import TagGenerator


class GitAnalysisService:
    """Main service for git history analysis and comparison."""

    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.repo: gitpython.Repo | None = None
        self.complexity_calculator = ComplexityCalculator()
        self.llm_summarizer = LLMSummarizer(config) if config.use_llm else None
        self.cache = AnalysisCache(
            config.cache_dir or Path(config.repo_path) / ".git" / "git-analysis"
        )
        self.file_analyzer = FileAnalyzer(config)
        self.tag_generator = TagGenerator()
        self.logger = logging.getLogger(__name__)
        self._commit_to_branch_cache: dict[str, str] = {}
        self._tag_to_commit_cache: dict[str, list[str]] = {}

        # Initialize git repository
        self._initialize_repo()

    def _initialize_repo(self):
        """Initialize the git repository."""
        try:
            self.repo = gitpython.Repo(self.config.repo_path)
            self.logger.info(f"Initialized git repository at {self.config.repo_path}")
        except Exception as e:
            raise ValueError(f"Invalid git repository at {self.config.repo_path}: {e}") from e

    def compare_refs(self, from_ref: str, to_ref: str) -> ComparisonResult:
        """
        Compare two git references with detailed analysis.

        Args:
            from_ref: Source git reference (branch, tag, or commit hash)
            to_ref: Target git reference (branch, tag, or commit hash)

        Returns:
            ComparisonResult with detailed analysis
        """
        self.logger.info(f"Comparing {from_ref} -> {to_ref}")

        # Try to get cached result
        cache_key = f"compare_{from_ref}_{to_ref}"
        cached_result = self.cache.get(cache_key)
        if cached_result and not self.config.force_refresh:
            self.logger.info("Using cached comparison result")
            return cached_result

        # Build commit-to-branch mapping cache once for all commits
        self._commit_to_branch_cache = self._build_commit_branch_mapping()

        # Build tag-to-commit mapping cache once for all commits
        self._tag_to_commit_cache = self._build_tag_commit_mapping()

        # Get commits between references
        commits = self._get_commits_between_refs(from_ref, to_ref)

        if not commits:
            raise ValueError(f"No commits found between {from_ref} and {to_ref}")

        # Analyze each commit
        # Note: estimated_remaining_seconds is a rough estimate (~2s per commit)
        # for progress display purposes only, not based on actual timing.
        progress = AnalysisProgress(
            total_commits=len(commits),
            processed_commits=0,
            current_step="Analyzing commits",
            estimated_remaining_seconds=len(commits) * 2,
            stage="processing",
        )

        analyzed_commits = []
        failed_commits: list[tuple[str, str]] = []  # (commit_hash, error_message)

        for commit in tqdm(commits, desc="Analyzing commits"):
            try:
                analysis = self.analyze_commit(commit.hexsha)
                analyzed_commits.append(analysis)
                progress.processed_commits += 1
            except Exception as e:
                error_msg = f"Failed to analyze commit {commit.hexsha}: {e}"
                self.logger.error(error_msg)
                failed_commits.append((commit.hexsha, str(e)))
                continue

        # Log failure summary if any commits failed
        if failed_commits:
            success_rate = len(analyzed_commits) / len(commits)
            self.logger.warning(
                f"Commit analysis completed with {len(failed_commits)} failures "
                f"out of {len(commits)} total commits ({success_rate:.1%} success rate)"
            )
            for commit_hash, error in failed_commits[:5]:  # Log first 5 failures
                self.logger.warning(f"  - {commit_hash[:8]}: {error}")
            if len(failed_commits) > 5:
                self.logger.warning(f"  ... and {len(failed_commits) - 5} more failures")

            # Check if success rate is below minimum threshold
            if success_rate < self.config.min_success_rate:
                if self.config.continue_on_failure:
                    self.logger.warning(
                        f"Success rate {success_rate:.1%} is below threshold "
                        f"{self.config.min_success_rate:.1%}, but continuing due to "
                        f"continue_on_failure=True"
                    )
                else:
                    raise ValueError(
                        f"Analysis failed: only {success_rate:.1%} of commits succeeded "
                        f"(minimum: {self.config.min_success_rate:.1%}). "
                        f"Use continue_on_failure=True to proceed with partial results."
                    )

        # Calculate comparison metadata
        metadata = self._calculate_comparison_metadata(
            from_ref, to_ref, analyzed_commits, failed_commits
        )

        # Calculate contributor statistics
        contributors = self._calculate_contributor_stats(analyzed_commits)

        # Generate aggregate summary
        aggregate_summary = self._generate_aggregate_summary(analyzed_commits)

        # Generate highlights
        highlights = self._generate_highlights(analyzed_commits)

        # Risk assessment
        risk_assessment = self._assess_risk(analyzed_commits)

        # Generate recommendations
        recommendations = self._generate_recommendations(analyzed_commits)

        # File category distribution
        file_categories = self._calculate_file_categories(analyzed_commits)

        # Complexity distribution
        complexity_distribution = self.complexity_calculator.analyze_commit_complexity_distribution(
            analyzed_commits
        )

        # Top complex files
        top_complex_files = self.complexity_calculator.get_top_complex_files(analyzed_commits)

        # Create comparison result
        result = ComparisonResult(
            metadata=metadata,
            commits=analyzed_commits,
            contributors=contributors,
            aggregate_summary=aggregate_summary,
            highlights=highlights,
            risk_assessment=risk_assessment,
            recommendations=recommendations,
            file_categories=file_categories,
            complexity_distribution=complexity_distribution,
            top_complex_files=top_complex_files,
        )

        # Cache the result
        self.cache.set(cache_key, result)

        return result

    def analyze_commit(self, commit_hash: str) -> ChangeAnalysis:
        """
        Analyze a single commit with detailed metrics.

        Args:
            commit_hash: Git commit hash

        Returns:
            ChangeAnalysis with detailed commit information
        """
        if self.repo is None:
            raise RuntimeError("Repository not initialized")
        # Check cache first
        cache_key = f"commit_{commit_hash}"
        cached_analysis = self.cache.get(cache_key)
        if cached_analysis and not self.config.force_refresh:
            return cached_analysis

        try:
            commit = self.repo.commit(commit_hash)
        except Exception as e:
            raise ValueError(f"Invalid commit hash {commit_hash}: {e}") from e

        # Get basic commit info with proper type handling
        author_name = commit.author.name or "Unknown"
        author_email = commit.author.email or "unknown@example.com"

        # Handle message being bytes or str
        message = commit.message
        if isinstance(message, bytes):
            message = message.decode("utf-8", errors="replace")
        message_str = message.strip()

        commit_info = CommitInfo(
            hash=commit.hexsha,
            short_hash=commit.hexsha[:8],
            author=author_name,
            email=author_email,
            timestamp=datetime.fromtimestamp(commit.committed_date),
            message=message_str,
            branch=self._get_commit_branch(commit),
            tags=self._get_commit_tags(commit),
        )

        # Analyze file changes
        files_changed = self._analyze_commit_files(commit)

        # Calculate basic metrics
        lines_added = sum(f.lines_added for f in files_changed)
        lines_deleted = sum(f.lines_deleted for f in files_changed)
        files_added = sum(1 for f in files_changed if f.change_type == ChangeType.ADDED)
        files_deleted = sum(1 for f in files_changed if f.change_type == ChangeType.DELETED)
        files_modified = sum(1 for f in files_changed if f.change_type == ChangeType.MODIFIED)

        # Calculate complexity
        base_analysis = ChangeAnalysis(
            commit_hash=commit.hexsha,
            author=author_name,
            email=author_email,
            timestamp=datetime.fromtimestamp(commit.committed_date),
            branch=commit_info.branch,
            message=message_str,
            short_message=self._extract_short_message(message_str),
            files_changed=files_changed,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            files_added=files_added,
            files_deleted=files_deleted,
            files_modified=files_modified,
            complexity_score=0.0,  # Will be calculated
            summary="",  # Will be generated
            tags=[],  # Will be generated
            impact_areas=[],  # Will be generated
        )

        # Calculate complexity score
        complexity_score = self.complexity_calculator.calculate_complexity(base_analysis)
        base_analysis.complexity_score = complexity_score

        # Generate tags
        tags = self.tag_generator.generate_tags(base_analysis)
        base_analysis.tags = tags

        # Identify impact areas
        impact_areas = self._identify_impact_areas(files_changed)
        base_analysis.impact_areas = impact_areas

        # Check for breaking changes
        breaking_change = self._is_breaking_change(message_str, files_changed)
        base_analysis.breaking_change = breaking_change

        # Security relevance
        security_relevant = self._is_security_relevant(message_str, files_changed)
        base_analysis.security_relevant = security_relevant

        # Generate summary
        if self.llm_summarizer:
            summary = self.llm_summarizer.summarize_commit_sync(base_analysis)
        else:
            summary = self._generate_basic_summary(base_analysis)
        base_analysis.summary = summary

        # Cache the analysis
        self.cache.set(cache_key, base_analysis)

        return base_analysis

    def compare_commits(self, commit_a_hash: str, commit_b_hash: str) -> ComparisonDiff:
        """
        Compare two commits and describe their differences.

        Args:
            commit_a_hash: First commit hash
            commit_b_hash: Second commit hash

        Returns:
            ComparisonDiff with natural language differences
        """
        analysis_a = self.analyze_commit(commit_a_hash)
        analysis_b = self.analyze_commit(commit_b_hash)

        # Calculate similarity score
        similarity_score = self._calculate_commit_similarity(analysis_a, analysis_b)

        # Find differences
        differences = self._find_commit_differences(analysis_a, analysis_b)

        # Find common themes
        common_themes = self._find_common_themes(analysis_a, analysis_b)

        # Impact description
        impact_description = self._describe_impact(analysis_a, analysis_b)

        # Regression risk
        regression_risk = self._assess_regression_risk(analysis_a, analysis_b)

        # Migration notes
        migration_notes = self._generate_migration_notes(analysis_a, analysis_b)

        return ComparisonDiff(
            commit_a_hash=commit_a_hash,
            commit_b_hash=commit_b_hash,
            similarity_score=similarity_score,
            differences=differences,
            common_themes=common_themes,
            impact_description=impact_description,
            regression_risk=regression_risk,
            migration_notes=migration_notes,
        )

    def _get_commits_between_refs(self, from_ref: str, to_ref: str) -> list[gitpython.Commit]:
        """Get commits between two git references."""
        if self.repo is None:
            raise RuntimeError("Repository not initialized")
        try:
            commits = list(self.repo.iter_commits(f"{from_ref}..{to_ref}"))

            # Limit number of commits if specified
            if self.config.max_commits and len(commits) > self.config.max_commits:
                commits = commits[-self.config.max_commits :]

            return commits

        except Exception as e:
            raise ValueError(f"Failed to get commits between {from_ref} and {to_ref}: {e}") from e

    def _build_commit_branch_mapping(self) -> dict[str, str]:
        """Build a mapping of commit SHAs to branch names.

        This pre-computes the mapping once, avoiding O(n²) repeated lookups.
        For a repo with B branches and C commits per branch, this is O(B*C) once,
        versus O(B*C) per commit without caching.

        Returns:
            Dictionary mapping commit SHA to branch name
        """
        if self.repo is None:
            return {}

        mapping: dict[str, str] = {}
        try:
            for branch in self.repo.branches:
                for commit in self.repo.iter_commits(branch.name):
                    mapping[commit.hexsha] = branch.name
            self.logger.debug(f"Built commit-to-branch mapping with {len(mapping)} entries")
        except Exception as e:
            self.logger.warning(f"Failed to build commit-to-branch mapping: {e}")

        return mapping

    def _build_tag_commit_mapping(self) -> dict[str, list[str]]:
        """Build a mapping of commit SHAs to tag names.

        This pre-computes the mapping once, avoiding O(n*m) repeated lookups.
        For a repo with T tags and C commits, this is O(T) once versus O(T)
        per commit without caching.

        Returns:
            Dictionary mapping commit SHA to list of tag names
        """
        if self.repo is None:
            return {}

        mapping: dict[str, list[str]] = {}
        try:
            for tag in self.repo.tags:
                sha = tag.commit.hexsha
                if sha not in mapping:
                    mapping[sha] = []
                mapping[sha].append(tag.name)
            self.logger.debug(f"Built tag-to-commit mapping with {len(mapping)} entries")
        except Exception as e:
            self.logger.warning(f"Failed to build tag-to-commit mapping: {e}")

        return mapping

    def _analyze_commit_files(self, commit: gitpython.Commit) -> list[FileChange]:
        """Analyze file changes in a commit."""
        if self.repo is None:
            raise RuntimeError("Repository not initialized")
        files_changed = []

        try:
            # Get diff between commit and parent
            if commit.parents:
                parent = commit.parents[0]
                diffs = parent.diff(commit, create_patch=True)
            else:
                # First commit - diff against empty tree
                empty_tree = self.repo.git.hash_object("-t", "tree", "/dev/null")
                diffs = commit.diff(empty_tree, create_patch=True)

            for diff in diffs:
                file_change = self._analyze_file_diff(diff)
                files_changed.append(file_change)

        except Exception as e:
            self.logger.error(f"Failed to analyze files for commit {commit.hexsha}: {e}")

        return files_changed

    def _analyze_file_diff(self, diff) -> FileChange:
        """Analyze a single file diff."""
        # Determine change type
        if diff.new_file:
            change_type = ChangeType.ADDED
        elif diff.deleted_file:
            change_type = ChangeType.DELETED
        elif diff.renamed_file:
            change_type = ChangeType.RENAMED
        elif diff.copied_file:
            change_type = ChangeType.COPIED
        else:
            change_type = ChangeType.MODIFIED

        # Get file paths
        path = diff.b_path if diff.b_path else diff.a_path
        old_path = diff.a_path if diff.a_path != diff.b_path else None

        # Determine file category
        category = self.file_analyzer.categorize_file(path)

        # Get line counts
        lines_added = 0
        lines_deleted = 0

        if hasattr(diff, "diff") and diff.diff:
            # Parse diff for line counts
            diff_text = diff.diff.decode("utf-8", errors="ignore")
            for line in diff_text.split("\n"):
                if line.startswith("+") and not line.startswith("+++"):
                    lines_added += 1
                elif line.startswith("-") and not line.startswith("---"):
                    lines_deleted += 1

        # Check if binary file
        binary_file = hasattr(diff, "diff") and diff.diff is None

        return FileChange(
            path=path,
            old_path=old_path,
            change_type=change_type,
            category=category,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            binary_file=binary_file,
        )

    def _calculate_comparison_metadata(
        self,
        from_ref: str,
        to_ref: str,
        commits: list[ChangeAnalysis],
        failed_commits: list[tuple[str, str]] | None = None,
    ) -> ComparisonMetadata:
        """Calculate metadata for the comparison."""
        if self.repo is None:
            raise RuntimeError("Repository not initialized")
        if not commits:
            raise ValueError("No commits provided")

        from_commit = self.repo.commit(from_ref)
        to_commit = self.repo.commit(to_ref)

        # Get date range
        dates = [commit.timestamp for commit in commits]
        date_range = (min(dates), max(dates))

        # Calculate totals
        total_files_changed = len(
            {file.path for commit in commits for file in commit.files_changed}
        )
        total_lines_added = sum(commit.lines_added for commit in commits)
        total_lines_deleted = sum(commit.lines_deleted for commit in commits)
        total_complexity = sum(commit.complexity_score for commit in commits)

        # Calculate time span
        time_span_days = (date_range[1] - date_range[0]).days

        # Get branches involved
        branches_involved = list({commit.branch for commit in commits})

        # Calculate success rate
        total_commits_attempted = len(commits) + len(failed_commits or [])
        success_rate = (
            len(commits) / total_commits_attempted if total_commits_attempted > 0 else 1.0
        )

        return ComparisonMetadata(
            from_ref=from_ref,
            to_ref=to_ref,
            from_commit_hash=from_commit.hexsha,
            to_commit_hash=to_commit.hexsha,
            date_range=date_range,
            total_commits=len(commits),
            total_files_changed=total_files_changed,
            total_lines_added=total_lines_added,
            total_lines_deleted=total_lines_deleted,
            total_complexity=total_complexity,
            time_span_days=time_span_days,
            branches_involved=branches_involved,
            analysis_success_rate=success_rate,
            failed_commits_count=len(failed_commits or []),
        )

    def _calculate_contributor_stats(
        self, commits: list[ChangeAnalysis]
    ) -> dict[str, ContributorStats]:
        """Calculate statistics for each contributor."""
        contributors = {}

        for commit in commits:
            key = commit.author
            if key not in contributors:
                contributors[key] = ContributorStats(
                    name=commit.author,
                    email=commit.email,
                    commits=0,
                    lines_added=0,
                    lines_deleted=0,
                    files_touched=0,
                    complexity_contribution=0.0,
                    first_commit=commit.timestamp,
                    last_commit=commit.timestamp,
                )

            stats = contributors[key]
            stats.commits += 1
            stats.lines_added += commit.lines_added
            stats.lines_deleted += commit.lines_deleted
            stats.files_touched += len(commit.files_changed)
            stats.complexity_contribution += commit.complexity_score

            # Update date range
            if commit.timestamp < stats.first_commit:
                stats.first_commit = commit.timestamp
            if commit.timestamp > stats.last_commit:
                stats.last_commit = commit.timestamp

        return contributors

    def _generate_aggregate_summary(self, commits: list[ChangeAnalysis]) -> str:
        """Generate aggregate summary for all commits."""
        if not commits:
            return "No commits to summarize"

        total_complexity = sum(c.complexity_score for c in commits)
        avg_complexity = total_complexity / len(commits)

        # Find main themes
        all_tags = []
        for commit in commits:
            all_tags.extend(commit.tags)

        tag_counts: dict[str, int] = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        summary_parts = [
            f"Analyzed {len(commits)} commits with average complexity of {avg_complexity:.1f}.",
            f"Total changes: {sum(c.lines_added for c in commits)} lines added, "
            f"{sum(c.lines_deleted for c in commits)} lines deleted.",
        ]

        if top_tags:
            summary_parts.append(
                f"Main themes: {', '.join(f'{tag} ({count})' for tag, count in top_tags)}"
            )

        # Check for breaking changes
        breaking_changes = [c for c in commits if c.breaking_change]
        if breaking_changes:
            summary_parts.append(f"⚠️  {len(breaking_changes)} breaking changes detected")

        return " ".join(summary_parts)

    def _generate_highlights(self, commits: list[ChangeAnalysis]) -> list[str]:
        """Generate highlights from commits."""
        highlights = []

        # Most complex commits
        top_complex = sorted(commits, key=lambda x: x.complexity_score, reverse=True)[:3]
        for commit in top_complex:
            highlights.append(
                f"High complexity: {commit.short_message} ({commit.complexity_score:.1f})"
            )

        # Breaking changes
        breaking_commits = [c for c in commits if c.breaking_change]
        for commit in breaking_commits:
            highlights.append(f"🔴 Breaking: {commit.short_message}")

        # Security changes
        security_commits = [c for c in commits if c.security_relevant]
        for commit in security_commits:
            highlights.append(f"🔒 Security: {commit.short_message}")

        # Large file changes
        large_file_commits = [
            c for c in commits if len(c.files_changed) > 20 or c.lines_added + c.lines_deleted > 500
        ]
        for commit in large_file_commits:
            highlights.append(f"📊 Large changes: {commit.short_message}")

        return highlights[:10]  # Limit to 10 highlights

    def _assess_risk(self, commits: list[ChangeAnalysis]) -> str:
        """Assess overall risk of the changes."""
        if not commits:
            return "No risk assessment available"

        total_complexity = sum(c.complexity_score for c in commits)
        avg_complexity = total_complexity / len(commits)

        breaking_count = sum(1 for c in commits if c.breaking_change)
        security_count = sum(1 for c in commits if c.security_relevant)

        risk_factors = []
        if avg_complexity > 60:
            risk_factors.append("high average complexity")
        if breaking_count > 0:
            risk_factors.append(f"{breaking_count} breaking changes")
        if security_count > 0:
            risk_factors.append(f"{security_count} security-related changes")
        if len(commits) > 50:
            risk_factors.append("large number of commits")

        if not risk_factors:
            return "Low risk - changes appear to be routine"
        elif len(risk_factors) == 1:
            return f"Medium risk - {risk_factors[0]}"
        else:
            return f"High risk - {', '.join(risk_factors)}"

    def _generate_recommendations(self, commits: list[ChangeAnalysis]) -> list[str]:
        """Generate recommendations based on analysis."""
        recommendations = []

        # Check for missing tests
        test_commits = sum(
            1 for c in commits if any(f.category == FileCategory.TESTS for f in c.files_changed)
        )
        code_commits = sum(
            1 for c in commits if any(f.category == FileCategory.CODE for f in c.files_changed)
        )

        if code_commits > test_commits * 2:
            recommendations.append(
                "Consider adding more tests - many code changes without corresponding test updates"
            )

        # Check for documentation
        doc_commits = sum(
            1
            for c in commits
            if any(f.category == FileCategory.DOCUMENTATION for f in c.files_changed)
        )
        if doc_commits == 0 and code_commits > 5:
            recommendations.append("Consider updating documentation for the new features")

        # High complexity warnings
        high_complexity = [c for c in commits if c.complexity_score > 70]
        if high_complexity:
            recommendations.append(
                f"Consider breaking down the {len(high_complexity)} high-complexity commits into smaller changes"
            )

        # Breaking change recommendations
        breaking_commits = [c for c in commits if c.breaking_change]
        if breaking_commits:
            recommendations.append("Ensure migration guides are available for breaking changes")

        return recommendations

    def _calculate_file_categories(self, commits: list[ChangeAnalysis]) -> dict[FileCategory, int]:
        """Calculate distribution of file categories."""
        categories: dict[FileCategory, int] = {}
        for commit in commits:
            for file_change in commit.files_changed:
                categories[file_change.category] = categories.get(file_change.category, 0) + 1
        return categories

    # Helper methods
    def _get_commit_branch(self, commit: gitpython.Commit) -> str:
        """Get the branch name for a commit using pre-built cache.

        This is O(1) lookup instead of O(n*m) nested loop through branches and commits.
        The cache is built once per comparison in compare_refs().
        """
        if self.repo is None:
            return "unknown"
        return self._commit_to_branch_cache.get(commit.hexsha, "unknown")

    def _get_commit_tags(self, commit: gitpython.Commit) -> list[str]:
        """Get tags pointing to this commit using cache.

        This is O(1) lookup instead of O(T) iteration through all tags.
        The cache is built once per comparison in compare_refs().

        If cache is empty (e.g., in tests or direct calls), falls back to O(T) lookup.
        """
        if self.repo is None:
            return []

        # Use cache if available (built by compare_refs)
        if self._tag_to_commit_cache:
            return self._tag_to_commit_cache.get(commit.hexsha, [])

        # Fallback for direct calls or tests (O(T) iteration)
        try:
            tags = []
            for tag in self.repo.tags:
                if tag.commit.hexsha == commit.hexsha:
                    tags.append(tag.name)
            return tags
        except Exception:
            return []

    def _extract_short_message(self, message: str) -> str:
        """Extract short message from full commit message."""
        lines = message.strip().split("\n")
        return lines[0] if lines else ""

    def _identify_impact_areas(self, files_changed: list[FileChange]) -> list[str]:
        """Identify areas of impact based on file changes."""
        areas = set()
        for file_change in files_changed:
            # Extract area from file path
            path_parts = file_change.path.split("/")
            if len(path_parts) > 1:
                areas.add(path_parts[0])

            # Check for specific patterns
            if any(
                pattern in file_change.path.lower()
                for pattern in ["auth", "security", "permission", "role"]
            ):
                areas.add("security")
            elif any(
                pattern in file_change.path.lower()
                for pattern in ["api", "endpoint", "route", "controller"]
            ):
                areas.add("api")
            elif any(
                pattern in file_change.path.lower()
                for pattern in ["ui", "frontend", "component", "view"]
            ):
                areas.add("frontend")
            elif any(
                pattern in file_change.path.lower()
                for pattern in ["model", "schema", "database", "migration"]
            ):
                areas.add("data")

        return list(areas)

    def _is_breaking_change(self, message: str, files_changed: list[FileChange]) -> bool:
        """Check if commit represents a breaking change."""
        message_lower = message.lower()
        breaking_indicators = [
            "breaking",
            "breaking change",
            "break:",
            "⚠️",
            "deprecat",
            "remove",
            "delete",
            "replace",
            "migration",
        ]

        if any(indicator in message_lower for indicator in breaking_indicators):
            return True

        # Check file patterns
        for file_change in files_changed:
            if any(
                pattern in file_change.path.lower()
                for pattern in ["migration", "schema", "proto", "interface", "api"]
            ):
                return True

        return False

    def _is_security_relevant(self, message: str, files_changed: list[FileChange]) -> bool:
        """Check if commit is security-relevant."""
        message_lower = message.lower()
        security_indicators = [
            "security",
            "vulnerability",
            "cve",
            "exploit",
            "patch",
            "auth",
            "permission",
            "access",
            "token",
            "secret",
            "key",
        ]

        if any(indicator in message_lower for indicator in security_indicators):
            return True

        # Check file patterns
        for file_change in files_changed:
            if any(
                pattern in file_change.path.lower()
                for pattern in ["auth", "security", "permission", "cert", "key", "secret"]
            ):
                return True

        return False

    def _generate_basic_summary(self, analysis: ChangeAnalysis) -> str:
        """Generate basic summary without LLM."""
        parts = [
            f"Changed {len(analysis.files_changed)} files",
            f"added {analysis.lines_added} lines, deleted {analysis.lines_deleted} lines",
        ]

        if analysis.impact_areas:
            parts.append(f"affecting {', '.join(analysis.impact_areas)}")

        if analysis.tags:
            parts.append(f"({', '.join(analysis.tags)})")

        return ". ".join(parts) + "."

    def _calculate_commit_similarity(self, a: ChangeAnalysis, b: ChangeAnalysis) -> float:
        """Calculate similarity score between two commits (0-1)."""
        # Simple similarity based on common tags and files
        common_tags = set(a.tags) & set(b.tags)
        all_tags = set(a.tags) | set(b.tags)
        tag_similarity = len(common_tags) / len(all_tags) if all_tags else 0

        common_files = {f.path for f in a.files_changed} & {f.path for f in b.files_changed}
        all_files = {f.path for f in a.files_changed} | {f.path for f in b.files_changed}
        file_similarity = len(common_files) / len(all_files) if all_files else 0

        return (tag_similarity + file_similarity) / 2

    def _find_commit_differences(self, a: ChangeAnalysis, b: ChangeAnalysis) -> list[str]:
        """Find differences between two commits."""
        differences = []

        if a.complexity_score > b.complexity_score + 20:
            differences.append(
                f"First commit is significantly more complex ({a.complexity_score:.1f} vs {b.complexity_score:.1f})"
            )
        elif b.complexity_score > a.complexity_score + 20:
            differences.append(
                f"Second commit is significantly more complex ({b.complexity_score:.1f} vs {a.complexity_score:.1f})"
            )

        tags_a = set(a.tags)
        tags_b = set(b.tags)
        unique_a = tags_a - tags_b
        unique_b = tags_b - tags_a

        if unique_a:
            differences.append(f"First commit has unique themes: {', '.join(unique_a)}")
        if unique_b:
            differences.append(f"Second commit has unique themes: {', '.join(unique_b)}")

        return differences

    def _find_common_themes(self, a: ChangeAnalysis, b: ChangeAnalysis) -> list[str]:
        """Find common themes between two commits."""
        common_tags = set(a.tags) & set(b.tags)
        common_areas = set(a.impact_areas) & set(b.impact_areas)

        themes: list[str] = []
        if common_tags:
            themes.append(f"Tags: {', '.join(common_tags)}")
        if common_areas:
            themes.append(f"Areas: {', '.join(common_areas)}")

        return themes

    def _describe_impact(self, a: ChangeAnalysis, b: ChangeAnalysis) -> str:
        """Describe the combined impact of two commits."""
        total_complexity = a.complexity_score + b.complexity_score
        total_files = len(a.files_changed) + len(b.files_changed)
        total_lines = a.lines_added + b.lines_deleted + b.lines_added + b.lines_deleted

        impact_level = (
            "low" if total_complexity < 40 else "medium" if total_complexity < 80 else "high"
        )

        return f"Combined {impact_level} impact: {total_files} files, {total_lines} lines changed, complexity {total_complexity:.1f}"

    def _assess_regression_risk(self, a: ChangeAnalysis, b: ChangeAnalysis) -> str:
        """Assess regression risk between two commits."""
        risk_factors = []

        total_complexity = a.complexity_score + b.complexity_score
        if total_complexity > 100:
            risk_factors.append("high complexity")

        if a.breaking_change or b.breaking_change:
            risk_factors.append("breaking changes")

        if a.security_relevant or b.security_relevant:
            risk_factors.append("security changes")

        if len(risk_factors) == 0:
            return "Low regression risk"
        elif len(risk_factors) == 1:
            return f"Medium regression risk ({risk_factors[0]})"
        else:
            return f"High regression risk ({', '.join(risk_factors)})"

    def _generate_migration_notes(self, a: ChangeAnalysis, b: ChangeAnalysis) -> list[str]:
        """Generate migration notes for transitioning between commits."""
        notes = []

        if a.breaking_change or b.breaking_change:
            notes.append("Review breaking changes and update dependent code")

        if any("migration" in tag for tag in a.tags + b.tags):
            notes.append("Database or data migration may be required")

        if any("api" in tag for tag in a.tags + b.tags):
            notes.append("API contracts may have changed - update clients")

        if any("security" in tag for tag in a.tags + b.tags):
            notes.append("Review security implications and update configurations")

        return notes
