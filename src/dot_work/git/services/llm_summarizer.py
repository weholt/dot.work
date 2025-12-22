"""LLM integration for generating enhanced summaries and insights."""

import asyncio
import logging
from typing import Any

from dot_work.git.models import AnalysisConfig, ChangeAnalysis, ComparisonResult


class LLMSummarizer:
    """LLM-powered summarizer for git analysis."""

    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the LLM client based on provider."""
        try:
            if self.config.llm_provider == "openai":
                self._initialize_openai()
            elif self.config.llm_provider == "anthropic":
                self._initialize_anthropic()
            else:
                self.logger.warning(f"Unsupported LLM provider: {self.config.llm_provider}")
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM client: {e}")

    def _initialize_openai(self):
        """Initialize OpenAI client."""
        try:
            import openai
            from openai import OpenAI

            api_key = self._get_api_key("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found")

            self._client = OpenAI(api_key=api_key)
            self._provider = "openai"
            self.logger.info("Initialized OpenAI client")

        except ImportError:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
        except Exception as e:
            raise Exception(f"Failed to initialize OpenAI: {e}")

    def _initialize_anthropic(self):
        """Initialize Anthropic client."""
        try:
            import anthropic

            api_key = self._get_api_key("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Anthropic API key not found")

            self._client = anthropic.Anthropic(api_key=api_key)
            self._provider = "anthropic"
            self.logger.info("Initialized Anthropic client")

        except ImportError:
            raise ImportError("Anthropic package not installed. Install with: pip install anthropic")
        except Exception as e:
            raise Exception(f"Failed to initialize Anthropic: {e}")

    def _get_api_key(self, env_var: str) -> str | None:
        """Get API key from environment variables."""
        import os
        return os.getenv(env_var)

    def is_available(self) -> bool:
        """Check if LLM client is available."""
        return self._client is not None

    async def summarize_commit(self, analysis: ChangeAnalysis) -> str:
        """
        Generate enhanced summary for a single commit.

        Args:
            analysis: ChangeAnalysis object

        Returns:
            Enhanced summary string
        """
        if not self.is_available():
            return self._generate_basic_summary(analysis)

        try:
            prompt = self._build_commit_summary_prompt(analysis)
            response = await self._call_llm(prompt)
            return self._process_response(response)

        except Exception as e:
            self.logger.error(f"Failed to generate commit summary: {e}")
            return self._generate_basic_summary(analysis)

    async def summarize_comparison(self, result: ComparisonResult) -> str:
        """
        Generate enhanced summary for a comparison result.

        Args:
            result: ComparisonResult object

        Returns:
            Enhanced summary string
        """
        if not self.is_available():
            return result.aggregate_summary

        try:
            prompt = self._build_comparison_summary_prompt(result)
            response = await self._call_llm(prompt)
            return self._process_response(response)

        except Exception as e:
            self.logger.error(f"Failed to generate comparison summary: {e}")
            return result.aggregate_summary

    async def analyze_impact(self, analysis: ChangeAnalysis) -> list[str]:
        """
        Analyze impact areas using LLM.

        Args:
            analysis: ChangeAnalysis object

        Returns:
            List of impact areas
        """
        if not self.is_available():
            return analysis.impact_areas

        try:
            prompt = self._build_impact_analysis_prompt(analysis)
            response = await self._call_llm(prompt)
            return self._parse_impact_areas(response)

        except Exception as e:
            self.logger.error(f"Failed to analyze impact: {e}")
            return analysis.impact_areas

    async def suggest_testing_strategy(self, analysis: ChangeAnalysis) -> list[str]:
        """
        Suggest testing strategy for the changes.

        Args:
            analysis: ChangeAnalysis object

        Returns:
            List of testing suggestions
        """
        if not self.is_available():
            return self._generate_basic_testing_suggestions(analysis)

        try:
            prompt = self._build_testing_strategy_prompt(analysis)
            response = await self._call_llm(prompt)
            return self._parse_testing_suggestions(response)

        except Exception as e:
            self.logger.error(f"Failed to generate testing suggestions: {e}")
            return self._generate_basic_testing_suggestions(analysis)

    async def assess_migration_complexity(self, analysis: ChangeAnalysis) -> dict[str, Any]:
        """
        Assess migration complexity and requirements.

        Args:
            analysis: ChangeAnalysis object

        Returns:
            Dictionary with migration assessment
        """
        if not self.is_available():
            return self._generate_basic_migration_assessment(analysis)

        try:
            prompt = self._build_migration_assessment_prompt(analysis)
            response = await self._call_llm(prompt)
            return self._parse_migration_assessment(response)

        except Exception as e:
            self.logger.error(f"Failed to assess migration complexity: {e}")
            return self._generate_basic_migration_assessment(analysis)

    def _build_commit_summary_prompt(self, analysis: ChangeAnalysis) -> str:
        """Build prompt for commit summarization."""
        files_info = []
        for file_change in analysis.files_changed[:10]:  # Limit to 10 files
            files_info.append(
                f"- {file_change.path} ({file_change.change_type.value}, "
                f"+{file_change.lines_added}/-{file_change.lines_deleted} lines)"
            )

        prompt = f"""
Please analyze the following git commit and provide a concise, human-readable summary:

Commit Details:
- Hash: {analysis.commit_hash[:8]}
- Author: {analysis.author}
- Date: {analysis.timestamp.strftime('%Y-%m-%d %H:%M')}
- Message: {analysis.message}
- Files changed: {len(analysis.files_changed)}
- Lines changed: +{analysis.lines_added}/-{analysis.lines_deleted}
- Complexity score: {analysis.complexity_score:.1f}
- Tags: {', '.join(analysis.tags) if analysis.tags else 'None'}

Files changed:
{chr(10).join(files_info)}

Please provide:
1. A concise 2-3 sentence summary of what this commit does
2. The primary impact areas or components affected
3. Any notable characteristics (breaking change, security, performance, etc.)
4. Key business value or user impact (if applicable)

Format your response as a clear, professional summary.
"""
        return prompt

    def _build_comparison_summary_prompt(self, result: ComparisonResult) -> str:
        """Build prompt for comparison summarization."""
        top_commits = []
        for commit in result.commits[:5]:  # Top 5 commits by complexity
            top_commits.append(
                f"- {commit.short_message} (complexity: {commit.complexity_score:.1f}, "
                f"author: {commit.author})"
            )

        prompt = f"""
Please analyze this git comparison and provide a comprehensive summary:

Comparison Details:
- From: {result.metadata.from_ref} to {result.metadata.to_ref}
- Total commits: {result.metadata.total_commits}
- Files changed: {result.metadata.total_files_changed}
- Lines changed: +{result.metadata.total_lines_added}/-{result.metadata.total_lines_deleted}
- Total complexity: {result.metadata.total_complexity:.1f}
- Time span: {result.metadata.time_span_days} days
- Contributors: {len(result.contributors)}

Highlights:
{chr(10).join(f"- {highlight}" for highlight in result.highlights[:5])}

Top commits by complexity:
{chr(10).join(top_commits)}

Please provide:
1. A high-level overview of what changed in this range
2. The main themes or categories of changes
3. Notable risks or breaking changes
4. Overall impact on the system
5. Key achievements or improvements

Format your response as a clear, professional summary suitable for release notes or stakeholder communication.
"""
        return prompt

    def _build_impact_analysis_prompt(self, analysis: ChangeAnalysis) -> str:
        """Build prompt for impact analysis."""
        prompt = f"""
Analyze the impact areas for this commit:

Commit: {analysis.short_message}
Files: {', '.join(f.path for f in analysis.files_changed[:10])}
Changes: +{analysis.lines_added}/-{analysis.lines_deleted} lines
Complexity: {analysis.complexity_score:.1f}

Please identify the primary areas of impact, such as:
- Core functionality components
- User interface elements
- Database schema or data structures
- API endpoints or interfaces
- Configuration or infrastructure
- Security or authentication systems
- Performance or reliability aspects
- Testing or build systems

Provide a list of 3-7 key impact areas as single words or short phrases.
"""
        return prompt

    def _build_testing_strategy_prompt(self, analysis: ChangeAnalysis) -> str:
        """Build prompt for testing strategy suggestions."""
        prompt = f"""
Suggest a testing strategy for this commit:

Commit: {analysis.short_message}
Files changed: {len(analysis.files_changed)}
File types: {', '.join(set(f.category.value for f in analysis.files_changed))}
Impact areas: {', '.join(analysis.impact_areas)}
Breaking change: {analysis.breaking_change}
Security relevant: {analysis.security_relevant}

Please suggest specific testing approaches, such as:
- Unit testing recommendations
- Integration testing needs
- End-to-end testing scenarios
- Performance testing considerations
- Security testing requirements
- Regression testing scope
- Manual testing focus areas

Provide 3-6 specific, actionable testing suggestions.
"""
        return prompt

    def _build_migration_assessment_prompt(self, analysis: ChangeAnalysis) -> str:
        """Build prompt for migration complexity assessment."""
        prompt = f"""
Assess the migration complexity for this commit:

Commit: {analysis.short_message}
Files: {len(analysis.files_changed)}
Changes: +{analysis.lines_added}/-{analysis.lines_deleted} lines
Complexity: {analysis.complexity_score:.1f}
Impact areas: {', '.join(analysis.impact_areas)}
Breaking change: {analysis.breaking_change}

Please assess:
1. Migration complexity level (Low/Medium/High/Critical)
2. Estimated migration effort (in hours/days)
3. Risk factors that could complicate migration
4. Prerequisites or dependencies for successful migration
5. Rollback strategy considerations
6. Downtime or service disruption expectations

Provide specific, actionable assessment.
"""
        return prompt

    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM with the given prompt."""
        if not self._client:
            raise Exception("LLM client not initialized")

        if self._provider == "openai":
            return await self._call_openai(prompt)
        elif self._provider == "anthropic":
            return await self._call_anthropic(prompt)
        else:
            raise Exception(f"Unknown LLM provider: {self._provider}")

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        try:
            response = await asyncio.to_thread(
                self._client.chat.completions.create,
                model=self.config.llm_model or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes git changes and provides clear, professional summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.config.llm_max_tokens or 1000,
                temperature=self.config.llm_temperature or 0.3
            )
            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"OpenAI API call failed: {e}")

    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API."""
        try:
            response = await asyncio.to_thread(
                self._client.messages.create,
                model=self.config.llm_model or "claude-3-sonnet-20240229",
                max_tokens=self.config.llm_max_tokens or 1000,
                temperature=self.config.llm_temperature or 0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text

        except Exception as e:
            raise Exception(f"Anthropic API call failed: {e}")

    def _process_response(self, response: str) -> str:
        """Process and clean LLM response."""
        if not response:
            return "No response available"

        # Clean up the response
        cleaned = response.strip()

        # Remove any markdown formatting that might interfere
        if cleaned.startswith('```'):
            lines = cleaned.split('\n')
            if lines[-1].strip() == '```':
                cleaned = '\n'.join(lines[1:-1])
            else:
                cleaned = '\n'.join(lines[1:])

        return cleaned.strip()

    def _parse_impact_areas(self, response: str) -> list[str]:
        """Parse impact areas from LLM response."""
        # Simple parsing - split by common delimiters
        areas = []

        # Split by lines and clean up
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            # Remove common prefixes
            for prefix in ['-', '•', '*', '1.', '2.', '3.', '4.', '5.', '6.', '7.']:
                if line.startswith(prefix):
                    line = line[len(prefix):].strip()
                    break

            # Add if not empty and not too long
            if line and len(line) < 50 and not line.lower().startswith(('please', 'here', 'the')):
                areas.append(line)

        return areas[:7]  # Limit to 7 areas

    def _parse_testing_suggestions(self, response: str) -> list[str]:
        """Parse testing suggestions from LLM response."""
        suggestions = []

        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            # Remove common prefixes and clean up
            for prefix in ['-', '•', '*', 'Test', 'Consider', 'Run', 'Add', 'Verify']:
                if line.startswith(prefix):
                    line = line[len(prefix):].strip()
                    break

            if line and len(line) < 100 and not line.lower().startswith(('please', 'here', 'you should')):
                suggestions.append(line)

        return suggestions[:6]  # Limit to 6 suggestions

    def _parse_migration_assessment(self, response: str) -> dict[str, Any]:
        """Parse migration assessment from LLM response."""
        assessment = {
            "complexity_level": "Medium",
            "estimated_effort": "Unknown",
            "risk_factors": [],
            "prerequisites": [],
            "rollback_strategy": "Standard",
            "downtime_expected": "None"
        }

        # Simple keyword-based parsing
        response_lower = response.lower()

        # Complexity level
        if any(word in response_lower for word in ['critical', 'very high', 'extremely complex']):
            assessment["complexity_level"] = "Critical"
        elif any(word in response_lower for word in ['high', 'complex']):
            assessment["complexity_level"] = "High"
        elif any(word in response_lower for word in ['low', 'simple', 'straightforward']):
            assessment["complexity_level"] = "Low"

        # Extract lines for detailed info
        lines = response.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(word in line_lower for word in ['hours', 'days', 'effort']):
                if 'hours' in line_lower or 'day' in line_lower:
                    assessment["estimated_effort"] = line.strip()
            elif any(word in line_lower for word in ['risk', 'factor', 'concern']):
                if len(line.strip()) < 100:
                    assessment["risk_factors"].append(line.strip())
            elif any(word in line_lower for word in ['prerequisite', 'requirement', 'depend']):
                if len(line.strip()) < 100:
                    assessment["prerequisites"].append(line.strip())
            elif any(word in line_lower for word in ['rollback', 'backout', 'revert']):
                assessment["rollback_strategy"] = line.strip()
            elif any(word in line_lower for word in ['downtime', 'disruption', 'outage']):
                assessment["downtime_expected"] = line.strip()

        # Limit lists
        assessment["risk_factors"] = assessment["risk_factors"][:3]
        assessment["prerequisites"] = assessment["prerequisites"][:3]

        return assessment

    # Fallback methods when LLM is not available
    def _generate_basic_summary(self, analysis: ChangeAnalysis) -> str:
        """Generate basic summary without LLM."""
        parts = [
            f"Changed {len(analysis.files_changed)} files",
            f"added {analysis.lines_added} lines, deleted {analysis.lines_deleted} lines"
        ]

        if analysis.impact_areas:
            parts.append(f"affecting {', '.join(analysis.impact_areas)}")

        if analysis.tags:
            parts.append(f"({', '.join(analysis.tags)})")

        if analysis.breaking_change:
            parts.append("⚠️ Breaking change")

        if analysis.security_relevant:
            parts.append("🔒 Security-related")

        return ". ".join(parts) + "."

    def _generate_basic_testing_suggestions(self, analysis: ChangeAnalysis) -> list[str]:
        """Generate basic testing suggestions without LLM."""
        suggestions = []

        # Based on file categories
        categories = set(f.category for f in analysis.files_changed)

        if analysis.breaking_change:
            suggestions.append("Comprehensive regression testing required")
            suggestions.append("Test backward compatibility")

        if analysis.security_relevant:
            suggestions.append("Security testing and penetration testing")
            suggestions.append("Authentication and authorization testing")

        if any(cat in categories for cat in [FileCategory.CODE, FileCategory.API]):
            suggestions.append("Unit testing for modified functions")
            suggestions.append("Integration testing for affected components")

        if FileCategory.DATABASE in categories:
            suggestions.append("Database migration testing")
            suggestions.append("Data integrity verification")

        if FileCategory.FRONTEND in categories:
            suggestions.append("UI/UX testing across browsers")
            suggestions.append("Component testing for changed UI elements")

        if analysis.complexity_score > 50:
            suggestions.append("Performance testing for high-complexity changes")

        return suggestions[:5]

    def _generate_basic_migration_assessment(self, analysis: ChangeAnalysis) -> dict[str, Any]:
        """Generate basic migration assessment without LLM."""
        if analysis.breaking_change:
            return {
                "complexity_level": "High" if analysis.complexity_score > 60 else "Medium",
                "estimated_effort": "2-4 hours" if analysis.complexity_score < 50 else "4-8 hours",
                "risk_factors": ["Breaking changes require careful coordination"],
                "prerequisites": ["Backup current state", "Prepare rollback plan"],
                "rollback_strategy": "Use version control to revert if needed",
                "downtime_expected": "Possible brief service interruption"
            }
        else:
            return {
                "complexity_level": "Low" if analysis.complexity_score < 30 else "Medium",
                "estimated_effort": "Less than 1 hour",
                "risk_factors": [],
                "prerequisites": [],
                "rollback_strategy": "Standard revert procedures",
                "downtime_expected": "None"
            }