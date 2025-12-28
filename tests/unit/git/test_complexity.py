"""Tests for complexity calculator service."""

from datetime import datetime

from dot_work.git.models import (
    ChangeAnalysis,
    ChangeType,
    FileCategory,
    FileChange,
)
from dot_work.git.services.complexity import ComplexityCalculator


class TestComplexityCalculator:
    """Test the ComplexityCalculator service."""

    def test_calculator_initialization(self):
        """Test calculator initialization."""
        calculator = ComplexityCalculator()

        assert calculator is not None
        assert hasattr(calculator, "weights")
        assert "files_changed" in calculator.weights
        assert "lines_added" in calculator.weights

    def test_calculate_commit_complexity_simple(self):
        """Test calculating complexity for a simple commit."""
        calculator = ComplexityCalculator()

        commit = ChangeAnalysis(
            commit_hash="abc123",
            author="John Doe",
            email="john@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="Add new feature",
            short_message="Add new feature",
            files_changed=[
                FileChange(
                    path="src/main.py",
                    change_type=ChangeType.MODIFIED,
                    category=FileCategory.CODE,
                    lines_added=10,
                    lines_deleted=5,
                )
            ],
            lines_added=10,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=0.0,
            summary="Add feature",
            tags=[],
            impact_areas=[],
        )

        complexity = calculator.calculate_complexity(commit)

        # Should have some complexity
        assert 0 <= complexity <= 100

    def test_calculate_commit_complexity_large(self):
        """Test calculating complexity for a large commit."""
        calculator = ComplexityCalculator()

        commit = ChangeAnalysis(
            commit_hash="def456",
            author="Jane Doe",
            email="jane@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="Add large feature with many files",
            short_message="Add large feature",
            files_changed=[
                FileChange(
                    path=f"src/file_{i}.py",
                    change_type=ChangeType.ADDED,
                    category=FileCategory.CODE,
                    lines_added=100,
                    lines_deleted=0,
                )
                for i in range(25)
            ],
            lines_added=2500,
            lines_deleted=0,
            files_added=25,
            files_deleted=0,
            files_modified=0,
            complexity_score=0.0,
            summary="Add large feature",
            tags=[],
            impact_areas=[],
        )

        complexity = calculator.calculate_complexity(commit)

        # Large commit should have higher complexity
        assert complexity > 20

    def test_calculate_commit_complexity_breaking(self):
        """Test that breaking changes have higher complexity."""
        calculator = ComplexityCalculator()

        commit = ChangeAnalysis(
            commit_hash="ghi789",
            author="Dev",
            email="dev@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="BREAKING: Remove deprecated API",
            short_message="BREAKING: Remove deprecated API",
            files_changed=[
                FileChange(
                    path="src/api.py",
                    change_type=ChangeType.DELETED,
                    category=FileCategory.CODE,
                    lines_added=0,
                    lines_deleted=200,
                )
            ],
            lines_added=0,
            lines_deleted=200,
            files_added=0,
            files_deleted=1,
            files_modified=0,
            complexity_score=0.0,
            summary="Remove deprecated API",
            tags=[],
            impact_areas=[],
            breaking_change=True,
        )

        complexity = calculator.calculate_complexity(commit)

        # Breaking change should increase complexity significantly
        assert complexity > 30

    def test_calculate_commit_complexity_security(self):
        """Test that security changes have higher complexity."""
        calculator = ComplexityCalculator()

        commit = ChangeAnalysis(
            commit_hash="jkl012",
            author="Security",
            email="security@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="security: patch vulnerability",
            short_message="security: patch vulnerability",
            files_changed=[
                FileChange(
                    path="src/auth.py",
                    change_type=ChangeType.MODIFIED,
                    category=FileCategory.CODE,
                    lines_added=15,
                    lines_deleted=5,
                )
            ],
            lines_added=15,
            lines_deleted=5,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=0.0,
            summary="Patch vulnerability",
            tags=[],
            impact_areas=[],
            security_relevant=True,
        )

        complexity = calculator.calculate_complexity(commit)

        # Security change should increase complexity
        assert complexity > 20

    def test_calculate_file_complexity_returns_dict(self):
        """Test that file complexity calculation returns a dict."""
        calculator = ComplexityCalculator()

        file_change = FileChange(
            path="src/main.py",
            change_type=ChangeType.MODIFIED,
            category=FileCategory.CODE,
            lines_added=50,
            lines_deleted=25,
        )

        complexity = calculator.calculate_file_complexity(file_change)

        # Should return a dict
        assert isinstance(complexity, dict)
        assert "base_score" in complexity
        assert "lines_score" in complexity
        assert "file_type_multiplier" in complexity
        assert "change_type_multiplier" in complexity
        assert "pattern_multiplier" in complexity
        assert "total_score" in complexity
        assert "complexity_level" in complexity

    def test_calculate_file_complexity_code_file(self):
        """Test file complexity for code file."""
        calculator = ComplexityCalculator()

        file_change = FileChange(
            path="src/main.py",
            change_type=ChangeType.MODIFIED,
            category=FileCategory.CODE,
            lines_added=50,
            lines_deleted=25,
        )

        complexity = calculator.calculate_file_complexity(file_change)

        # Code file should have multiplier
        assert complexity["file_type_multiplier"] == 1.0

    def test_calculate_file_complexity_config_file(self):
        """Test file complexity for config file."""
        calculator = ComplexityCalculator()

        file_change = FileChange(
            path="config.yaml",
            change_type=ChangeType.MODIFIED,
            category=FileCategory.CONFIG,
            lines_added=20,
            lines_deleted=10,
        )

        complexity = calculator.calculate_file_complexity(file_change)

        # Config file should have higher multiplier
        assert complexity["file_type_multiplier"] == 1.2

    def test_calculate_file_complexity_binary_file(self):
        """Test file complexity for binary file."""
        calculator = ComplexityCalculator()

        file_change = FileChange(
            path="image.png",
            change_type=ChangeType.ADDED,
            binary_file=True,
            lines_added=0,
            lines_deleted=0,
        )

        complexity = calculator.calculate_file_complexity(file_change)

        # Binary files should still get some complexity
        assert complexity["total_score"] >= 0

    def test_get_complexity_level_low(self):
        """Test complexity level for low score."""
        calculator = ComplexityCalculator()

        level = calculator._get_complexity_level(10.0)

        assert level == "low"

    def test_get_complexity_level_medium(self):
        """Test complexity level for medium score."""
        calculator = ComplexityCalculator()

        level = calculator._get_complexity_level(30.0)

        assert level == "medium"

    def test_get_complexity_level_high(self):
        """Test complexity level for high score."""
        calculator = ComplexityCalculator()

        level = calculator._get_complexity_level(50.0)

        assert level == "high"

    def test_get_complexity_level_very_high(self):
        """Test complexity level for very high score."""
        calculator = ComplexityCalculator()

        level = calculator._get_complexity_level(70.0)

        assert level == "very_high"

    def test_get_complexity_level_critical(self):
        """Test complexity level for critical score."""
        calculator = ComplexityCalculator()

        level = calculator._get_complexity_level(90.0)

        assert level == "critical"

    def test_analyze_commit_complexity_distribution(self):
        """Test analyzing complexity distribution across commits."""
        calculator = ComplexityCalculator()

        commits = [
            ChangeAnalysis(
                commit_hash="abc123",
                author="Dev1",
                email="dev1@example.com",
                timestamp=datetime.now(),
                branch="main",
                message="Simple commit",
                short_message="Simple",
                files_changed=[],
                lines_added=10,
                lines_deleted=5,
                files_added=0,
                files_deleted=0,
                files_modified=1,
                complexity_score=15.0,
                summary="Simple",
                tags=[],
                impact_areas=[],
            ),
            ChangeAnalysis(
                commit_hash="def456",
                author="Dev2",
                email="dev2@example.com",
                timestamp=datetime.now(),
                branch="main",
                message="Complex commit",
                short_message="Complex",
                files_changed=[],
                lines_added=100,
                lines_deleted=50,
                files_added=5,
                files_deleted=0,
                files_modified=3,
                complexity_score=50.0,
                summary="Complex",
                tags=[],
                impact_areas=[],
            ),
        ]

        distribution = calculator.analyze_commit_complexity_distribution(commits)

        assert distribution["0-20"] == 1
        assert distribution["40-60"] == 1
        assert distribution["20-40"] == 0
        assert distribution["60-80"] == 0
        assert distribution["80-100"] == 0

    def test_identify_risk_factors_low_risk(self):
        """Test risk identification for low-risk commit."""
        calculator = ComplexityCalculator()

        commit = ChangeAnalysis(
            commit_hash="low123",
            author="Dev",
            email="dev@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="Simple fix",
            short_message="Simple fix",
            files_changed=[
                FileChange(
                    path="src/utils.py",
                    change_type=ChangeType.MODIFIED,
                    category=FileCategory.CODE,
                    lines_added=5,
                    lines_deleted=2,
                )
            ],
            lines_added=5,
            lines_deleted=2,
            files_added=0,
            files_deleted=0,
            files_modified=1,
            complexity_score=10.0,
            summary="Simple fix",
            tags=[],
            impact_areas=[],
        )

        risks = calculator.identify_risk_factors(commit)

        # Low risk commit should have minimal risks
        assert len(risks) == 0

    def test_identify_risk_factors_high_risk(self):
        """Test risk identification for high-risk commit."""
        calculator = ComplexityCalculator()

        commit = ChangeAnalysis(
            commit_hash="risk123",
            author="Dev",
            email="dev@example.com",
            timestamp=datetime.now(),
            branch="main",
            message="breaking: security patch with migration",
            short_message="Breaking security",
            files_changed=[
                FileChange(
                    path="migrations/002_add_auth.sql",
                    change_type=ChangeType.ADDED,
                    category=FileCategory.DATA,
                    lines_added=50,
                    lines_deleted=0,
                )
            ],
            lines_added=500,
            lines_deleted=100,
            files_added=10,
            files_deleted=0,
            files_modified=5,
            complexity_score=85.0,
            summary="Breaking security migration",
            tags=[],
            impact_areas=[],
            breaking_change=True,
            security_relevant=True,
        )

        risks = calculator.identify_risk_factors(commit)

        # High risk commit should have multiple risk factors
        assert len(risks) > 0
        assert any("breaking" in r.lower() for r in risks)
        assert any("security" in r.lower() for r in risks)
