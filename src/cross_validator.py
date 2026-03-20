"""
Innovative Cross-Validation Engine
Validates resume claims against GitHub reality - THE KEY DIFFERENTIATOR!
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of cross-validating resume claims against GitHub reality."""
    skill: str
    claimed: bool
    verified: bool
    confidence: float
    evidence: List[str]
    gap_explanation: str


class CrossValidator:
    """
    Cross-validates resume claims against GitHub profile data.
    """

    SKILL_CATEGORIES = {
        "languages": ["python", "javascript", "java", "go", "rust", "typescript", "ruby", "php", "c++", "c#"],
        "frameworks": ["react", "vue", "angular", "django", "flask", "fastapi", "spring", "express", "next"],
        "ml_ai": ["machine learning", "tensorflow", "pytorch", "keras", "deep learning", "nlp", "computer vision", "scikit"],
        "databases": ["postgresql", "mysql", "mongodb", "redis", "elasticsearch", "dynamodb", "sql"],
        "cloud_devops": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins", "github actions"],
        "data_engineering": ["spark", "hadoop", "kafka", "airflow", "etl", "snowflake", "databricks"],
    }

    def __init__(self):
        self.skill_categories = self.SKILL_CATEGORIES

    def categorize_skill(self, skill: str) -> str:
        """Categorize a skill into a category."""
        skill_lower = skill.lower()
        for category, patterns in self.skill_categories.items():
            for pattern in patterns:
                if pattern in skill_lower or skill_lower in pattern:
                    return category
        return "other"

    def validate_skill_on_github(
        self,
        skill: str,
        github_profile: Dict,
        repositories: List[Dict]
    ) -> ValidationResult:
        """Validate if a claimed skill is actually demonstrated on GitHub."""
        skill_lower = skill.lower()
        category = self.categorize_skill(skill)

        evidence = []
        confidence = 0.0

        languages_used = set()
        for repo in repositories:
            lang = repo.get("language", "")
            if lang:
                languages_used.add(lang.lower())

        if category == "languages":
            if skill_lower in languages_used or skill in languages_used:
                evidence.append(f"Repositories use {skill}")
                confidence += 0.4

        repo_topics = set()
        for repo in repositories:
            topics = repo.get("topics", [])
            if topics:
                repo_topics.update([t.lower() for t in topics])

        if skill_lower in repo_topics or any(skill_lower in t for t in repo_topics):
            evidence.append(f"Repository topics mention {skill}")
            confidence += 0.25

        skill_in_descriptions = 0
        for repo in repositories:
            desc = repo.get("description", "") or ""
            readme = repo.get("readme_preview", "") or ""
            combined = (desc + " " + readme).lower()
            if skill_lower in combined or skill in combined:
                skill_in_descriptions += 1

        if skill_in_descriptions > 0:
            evidence.append(f"{skill} mentioned in {skill_in_descriptions} repo descriptions")
            confidence += 0.2 * min(skill_in_descriptions, 3) / 3

        total_stars = github_profile.get("metrics", {}).get("total_stars", 0)
        if total_stars > 50:
            confidence += 0.1
            evidence.append(f"Established profile with {total_stars} total stars")

        recent_repos = github_profile.get("metrics", {}).get("recent_activity_count", 0)
        if recent_repos > 5:
            confidence += 0.05
            evidence.append("Active contributor recently")

        confidence = min(confidence, 1.0)

        return ValidationResult(
            skill=skill,
            claimed=True,
            verified=confidence >= 0.4,
            confidence=confidence,
            evidence=evidence,
            gap_explanation=self._generate_gap_explanation(skill, confidence, evidence)
        )

    def _generate_gap_explanation(self, skill: str, confidence: float, evidence: List[str]) -> str:
        if confidence >= 0.7:
            return f"Strong evidence of {skill} usage on GitHub"
        elif confidence >= 0.4:
            return f"Some evidence of {skill}, but verification could be stronger"
        elif confidence >= 0.2:
            return f"Limited evidence of {skill}. May be secondary skill or learning phase"
        else:
            return f"No clear evidence of {skill} on GitHub. Claim unverified."

    def cross_validate_resume(
        self,
        claimed_skills: List[str],
        github_profile: Dict
    ) -> Dict:
        """Cross-validate all claimed skills against GitHub data."""
        repositories = github_profile.get("repositories", [])

        validated_skills = []
        verified_count = 0
        unverified_count = 0
        total_confidence = 0.0

        for skill in claimed_skills:
            result = self.validate_skill_on_github(skill, github_profile, repositories)
            validated_skills.append({
                "skill": skill,
                "verified": result.verified,
                "confidence": result.confidence,
                "evidence": result.evidence,
                "gap_explanation": result.gap_explanation
            })

            if result.verified:
                verified_count += 1
            else:
                unverified_count += 1

            total_confidence += result.confidence

        avg_confidence = total_confidence / len(claimed_skills) if claimed_skills else 0
        authenticity_score = (verified_count * 1.0 + unverified_count * avg_confidence * 0.3) / len(claimed_skills) if claimed_skills else 0

        return {
            "total_skills_claimed": len(claimed_skills),
            "verified_skills": verified_count,
            "unverified_skills": unverified_count,
            "verification_rate": verified_count / len(claimed_skills) if claimed_skills else 0,
            "average_confidence": avg_confidence,
            "authenticity_score": authenticity_score,
            "authenticity_rating": self._rate_authenticity(authenticity_score),
            "validated_skills": validated_skills,
            "summary": self._generate_validation_summary(verified_count, unverified_count, claimed_skills)
        }

    def _rate_authenticity(self, score: float) -> str:
        if score >= 0.8:
            return "Highly Authentic"
        elif score >= 0.6:
            return "Likely Authentic"
        elif score >= 0.4:
            return "Partially Authentic"
        elif score >= 0.2:
            return "Needs Verification"
        else:
            return "Unverified"

    def _generate_validation_summary(self, verified: int, unverified: int, skills: List[str]) -> str:
        if verified == len(skills):
            return f"All {verified} claimed skills verified on GitHub. Profile appears highly authentic."
        elif verified >= len(skills) * 0.7:
            unverified_list = [s for s in skills[:3]]
            return f"{verified}/{len(skills)} skills verified. Unverified: {', '.join(unverified_list)}"
        elif verified >= len(skills) * 0.4:
            return f"Only {verified}/{len(skills)} skills verified. Significant claims unverified."
        else:
            return f"Most claims ({unverified}/{len(skills)}) unverified on GitHub. Exercise caution."


class SkillTrajectoryAnalyzer:
    """Analyzes skill growth trajectory from GitHub activity."""

    def analyze_trajectory(self, github_profile: Dict, job_requirements: List[str]) -> Dict:
        repos = github_profile.get("repositories", [])
        metrics = github_profile.get("metrics", {})

        total_repos = metrics.get("total_repos", 0)
        recent_activity = metrics.get("recent_activity_count", 0)
        activity_consistency = metrics.get("activity_consistency", 0)

        recent_skills = set()
        for repo in repos[:10]:
            if repo.get("language"):
                recent_skills.add(repo["language"].lower())
            topics = repo.get("topics", [])
            if topics:
                recent_skills.update([t.lower() for t in topics])

        job_skill_coverage = {}
        for req_skill in job_requirements:
            req_lower = req_skill.lower()
            if req_lower in recent_skills:
                job_skill_coverage[req_skill] = {"status": "actively_using", "confidence": 0.9}
            elif self._has_adjacent_skill(req_lower, recent_skills):
                job_skill_coverage[req_skill] = {"status": "adjacent_skill", "confidence": 0.6, "note": "Has related technologies"}
            else:
                job_skill_coverage[req_skill] = {"status": "no_recent_evidence", "confidence": 0.1}

        velocity_score = self._calculate_learning_velocity(recent_activity, activity_consistency, total_repos, job_skill_coverage)

        return {
            "skills_actively_using": list(recent_skills),
            "job_skill_coverage": job_skill_coverage,
            "learning_velocity_score": velocity_score,
            "velocity_rating": self._rate_velocity(velocity_score),
            "trajectory_insight": self._generate_trajectory_insight(velocity_score, job_skill_coverage),
            "time_to_productivity_estimate": self._estimate_time_to_productivity(job_skill_coverage)
        }

    def _has_adjacent_skill(self, skill: str, available_skills: set) -> bool:
        adjacencies = {
            "python": ["python", "django", "flask", "fastapi"],
            "javascript": ["javascript", "typescript", "node.js"],
            "react": ["react", "react native", "next.js"],
            "machine learning": ["python", "data science", "tensorflow"],
            "kubernetes": ["docker", "containers"],
            "aws": ["cloud", "ec2", "s3"],
        }
        skill_lower = skill.lower()
        for key, adj_list in adjacencies.items():
            if skill_lower in adj_list:
                for adj in adj_list:
                    if adj in available_skills:
                        return True
        return False

    def _calculate_learning_velocity(self, recent_activity: int, consistency: float, total_repos: int, coverage: Dict) -> float:
        activity_score = min(recent_activity / 10, 1.0) * 0.3
        consistency_score = consistency * 0.2
        coverage_score = len([c for c in coverage.values() if c["status"] != "no_recent_evidence"]) / max(len(coverage), 1)
        breadth_score = coverage_score * 0.3
        gaps_exist = any(c["status"] == "adjacent_skill" for c in coverage.values())
        growth_score = 0.2 if gaps_exist else 0.1
        return min(activity_score + consistency_score + breadth_score + growth_score, 1.0)

    def _rate_velocity(self, score: float) -> str:
        if score >= 0.8:
            return "Rapid Learner"
        elif score >= 0.6:
            return "Steady Learner"
        elif score >= 0.4:
            return "Moderate Learner"
        else:
            return "Slow Adapter"

    def _generate_trajectory_insight(self, velocity: float, coverage: Dict) -> str:
        actively_using = sum(1 for c in coverage.values() if c["status"] == "actively_using")
        adjacent = sum(1 for c in coverage.values() if c["status"] == "adjacent_skill")
        total = len(coverage)

        if actively_using >= total * 0.7:
            return f"Strong match. Candidate actively uses {actively_using}/{total} required skills."
        elif adjacent >= total * 0.5:
            return f"Potential match. {actively_using} skills verified, {adjacent} have adjacent experience."
        else:
            return f"Limited recent activity in required areas. May need significant ramp-up time."

    def _estimate_time_to_productivity(self, coverage: Dict) -> str:
        gaps = [k for k, v in coverage.items() if v["status"] in ["adjacent_skill", "no_recent_evidence"]]
        if not gaps:
            return "1-2 weeks"
        elif len(gaps) <= 2:
            return "2-4 weeks"
        elif len(gaps) <= 4:
            return "1-2 months"
        else:
            return "2-3 months"


class ProjectComplexityAnalyzer:
    """Analyzes project complexity beyond just star counts."""

    def analyze_complexity(self, repositories: List[Dict]) -> Dict:
        if not repositories:
            return {"complexity_score": 0, "rating": "No projects", "insights": []}

        complexity_factors = []

        for repo in repositories:
            score = 0
            factors = []

            size = repo.get("size", 0)
            if size > 10000:
                score += 0.2
                factors.append("Large codebase")
            elif size > 1000:
                score += 0.1
                factors.append("Medium codebase")

            stars = repo.get("stars", 0)
            if stars > 100:
                score += 0.2
                factors.append("Highly starred")
            elif stars > 10:
                score += 0.1
                factors.append("Some community interest")

            forks = repo.get("forks", 0)
            if forks > 20:
                score += 0.15
                factors.append("Actively forked/contributed")
            elif forks > 5:
                score += 0.05

            has_topics = len(repo.get("topics", [])) > 2
            has_description = bool(repo.get("description"))
            if has_topics and has_description:
                score += 0.15
                factors.append("Well-documented")
            elif has_description:
                score += 0.05

            if not repo.get("is_fork", False):
                score += 0.1
                factors.append("Original work")

            if not repo.get("is_archived", False):
                score += 0.1
                factors.append("Actively maintained")

            complexity_factors.append({
                "repo": repo.get("name"),
                "score": min(score, 1.0),
                "factors": factors
            })

        avg_complexity = np.mean([c["score"] for c in complexity_factors]) if complexity_factors else 0

        return {
            "complexity_score": round(avg_complexity, 2),
            "rating": self._rate_complexity(avg_complexity),
            "project_details": complexity_factors[:5],
            "insights": self._generate_complexity_insights(complexity_factors)
        }

    def _rate_complexity(self, score: float) -> str:
        if score >= 0.7:
            return "Highly Complex"
        elif score >= 0.5:
            return "Moderately Complex"
        elif score >= 0.3:
            return "Simple Projects"
        else:
            return "Basic Projects"

    def _generate_complexity_insights(self, projects: List[Dict]) -> List[str]:
        insights = []
        high_complexity = sum(1 for p in projects if p["score"] >= 0.6)
        if high_complexity >= 3:
            insights.append(f"{high_complexity} projects show high technical complexity")
        elif high_complexity >= 1:
            insights.append(f"{high_complexity} project(s) demonstrate advanced skills")

        original_work = sum(1 for p in projects if "Original work" in p["factors"])
        if original_work >= 3:
            insights.append("Strong track record of original contributions")

        maintained = sum(1 for p in projects if "Actively maintained" in p["factors"])
        if maintained >= 3:
            insights.append("Consistently maintains projects over time")

        return insights


if __name__ == "__main__":
    from .github_fetcher import generate_synthetic_profile

    profile = generate_synthetic_profile("test_dev", ["Python", "React", "AWS", "Docker", "TensorFlow"])

    validator = CrossValidator()
    result = validator.cross_validate_resume(
        claimed_skills=["Python", "React", "Machine Learning", "AWS", "Docker"],
        github_profile=profile
    )

    print("=== CROSS VALIDATION RESULT ===")
    print(json.dumps(result, indent=2))
