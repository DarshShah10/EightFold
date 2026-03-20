"""
ADAPTIVE Multi-Signal Scoring Engine
Simplified: repo-based evidence, dependency analysis, skill matching.
No unreliable commit intelligence heuristics.
"""

import json
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from .skill_embedder import SkillEmbedder, batch_normalize_skills
from .jd_extractor import extract_skills_from_jd, extract_skills_fallback, get_skill_adjacent
from .jd_context_analyzer import JDContextAnalyzer


@dataclass
class AdaptiveWeights:
    """Adaptive weights calculated from JD context."""
    verified_skill_match: float = 0.40  # Primary signal
    technical_depth: float = 0.25       # Repo count + language depth
    learning_velocity: float = 0.15     # Recent activity
    soft_skills_match: float = 0.05    # Keep small - unreliable from GitHub
    project_complexity: float = 0.10    # Stars/forks as proxy
    cultural_fit: float = 0.05          # Account age
    technical_breadth: float = 0.00     # Don't weight breadth separately

    def to_dict(self) -> Dict:
        return asdict(self)


class AdaptiveScoringEngine:
    """
    Adaptive scoring engine that adjusts weights based on JD context.
    Enhanced to use deep signals from EightFold's harvester + analyzers.
    """

    def __init__(self):
        self.embedder = SkillEmbedder()
        self.jd_analyzer = JDContextAnalyzer()

    def analyze_and_score(
        self,
        candidate_profile: Dict,
        job_description: str,
        use_llm: bool = True,
        deep_signals: Optional[Dict] = None
    ) -> Dict:
        """
        Main entry point: Analyze JD context, then score candidate.

        Args:
            candidate_profile: Standard profile dict with repos, metrics, skills
            job_description: JD text
            use_llm: Use LLM for skill extraction
            deep_signals: Optional dict with EightFold-specific signals:
                - skill_intelligence: result from SkillAnalyzer
                - commit_intelligence: result from CommitIntelligenceEngine
                - aggregates: result from compute_all_aggregates
        """
        # Step 1: Analyze JD context
        jd_context = self.jd_analyzer.analyze_jd_context(job_description)
        adaptive_weights = AdaptiveWeights(**jd_context["adaptive_weights"])

        # Step 2: Extract skills from JD
        if use_llm:
            try:
                jd_skills = extract_skills_from_jd(job_description)
            except Exception:
                jd_skills = extract_skills_fallback(job_description)
        else:
            jd_skills = extract_skills_fallback(job_description)

        # Step 3: Get candidate skills
        candidate_skills = candidate_profile.get("raw_skills_list", [])

        # If deep signals available, use enhanced skill extraction
        if deep_signals and deep_signals.get("skill_intelligence"):
            si = deep_signals["skill_intelligence"]
            # Merge skill intelligence skills with raw_skills_list
            inferred_skills = si.get("inferred_skills", [])
            if inferred_skills:
                existing = set(s.lower() for s in candidate_skills)
                for skill in inferred_skills:
                    if skill.lower() not in existing:
                        candidate_skills.append(skill)

        # Step 4: Calculate all signal scores (with deep signal enhancement)
        signals = self._calculate_signals(
            jd_skills, candidate_skills, candidate_profile, adaptive_weights, deep_signals
        )

        # Step 5: Calculate composite score
        composite_score = self._calculate_composite_score(signals, adaptive_weights)

        # Step 6: Gap analysis
        gap_analysis = self._perform_gap_analysis(
            jd_skills, candidate_skills, signals, deep_signals
        )

        # Step 7: Generate reasoning
        reasoning = self._generate_reasoning(
            candidate_profile, composite_score, signals,
            gap_analysis, jd_context, adaptive_weights
        )

        # Step 8: Build result
        result = {
            "username": candidate_profile.get("username"),
            "name": candidate_profile.get("name", candidate_profile.get("resume_name", "")),

            "match_score": round(composite_score, 3),
            "match_percentage": f"{composite_score * 100:.1f}%",
            "match_rating": self._rate_match(composite_score),

            "jd_context": {
                "detected_industry": jd_context["detected_industry"],
                "detected_seniority": jd_context["detected_seniority"],
                "detected_role_type": jd_context["detected_role_type"],
                "weight_explanation": jd_context["explanation"]
            },
            "adaptive_weights": adaptive_weights.to_dict(),

            "signal_breakdown": signals,

            "gap_analysis": gap_analysis,

            "matched_skills": gap_analysis.get("matched_skills", []),
            "missing_skills": gap_analysis.get("missing_skills", []),
            "adjacent_skills": gap_analysis.get("adjacent_skills", []),
            "partial_matches": gap_analysis.get("partial_matches", []),

            "reasoning": reasoning,
            "hiring_recommendation": self._get_hiring_recommendation(composite_score, gap_analysis),

            "jd_skills_extracted": jd_skills
        }

        # Add deep signals if available
        if deep_signals:
            if deep_signals.get("commit_intelligence"):
                ci = deep_signals["commit_intelligence"]
                result["commit_intelligence"] = {
                    "intelligence_score": ci.get("commit_intelligence_score", 0),
                    "developer_archetype": ci.get("profile", {}).get("archetype", "Unknown") if ci.get("profile") else "Unknown",
                    "archetype_tagline": ci.get("profile", {}).get("tagline", "") if ci.get("profile") else "",
                    "dimension_scores": ci.get("dimensions", {}),
                    "top_citations": ci.get("citations", [])[:3] if ci.get("citations") else []
                }
            if deep_signals.get("skill_intelligence"):
                si = deep_signals["skill_intelligence"]
                result["skill_intelligence"] = {
                    "skill_level": si.get("skill_profile", {}).get("skill_level", "Unknown") if si.get("skill_profile") else "Unknown",
                    "primary_domains": si.get("skill_profile", {}).get("primary_domains", []) if si.get("skill_profile") else [],
                    "depth_category": si.get("skill_profile", {}).get("depth_index", {}).get("depth_category", "") if si.get("skill_profile") else ""
                }

        return result

    def _calculate_signals(
        self,
        jd_skills: Dict,
        candidate_skills: List[str],
        profile: Dict,
        weights: AdaptiveWeights,
        deep_signals: Optional[Dict] = None
    ) -> Dict:
        """Calculate all scoring signals, enhanced with deep EightFold signals."""
        signals = {}

        # Signal 1: Verified Skill Match
        signals["verified_skill_match"] = self._calc_skill_match(jd_skills, candidate_skills)

        # Signal 2: Technical Depth (ENHANCED with commit intelligence)
        signals["technical_depth"] = self._calc_technical_depth(candidate_skills, jd_skills, deep_signals)

        # Signal 3: Learning Velocity (ENHANCED with commit intelligence)
        signals["learning_velocity"] = self._calc_learning_velocity(profile, deep_signals)

        # NOTE: Dimension scores from commit_intelligence are 0-100.
        # We normalize them to 0-1 when storing in signal_breakdown
        # so all signals use the same scale (0-1) for consistent UI display.

        # Signal 4: Soft Skills Match
        signals["soft_skills_match"] = self._calc_soft_skills_match(
            jd_skills.get("soft_skills", []),
            profile.get("seniority_indicators", [])
        )

        # Signal 5: Project Complexity
        signals["project_complexity"] = self._calc_project_complexity(profile)

        # Signal 6: Cultural Fit
        signals["cultural_fit"] = self._calc_cultural_fit(profile)

        # Signal 7: Technical Breadth
        signals["technical_breadth"] = self._calc_technical_breadth(candidate_skills)

        return signals

    def _calc_skill_match(self, jd_skills: Dict, candidate_skills: List[str]) -> float:
        must_have = jd_skills.get("must_have", [])
        nice_to_have = jd_skills.get("nice_to_have", [])
        all_jd_skills = must_have + nice_to_have

        if not all_jd_skills:
            return 0.5

        # Use lower threshold (0.45) to catch semantic matches like "python" ≈ "machine learning"
        score, breakdown = self.embedder.compute_skill_match_score(all_jd_skills, candidate_skills)

        must_have_matched = sum(1 for s in breakdown.get("matched_skills", []) if s in must_have)
        must_have_rate = must_have_matched / len(must_have) if must_have else 0.5

        # Boost: if primary language is Python and JD has ML-related skills → partial credit
        cand_lower = [s.lower() for s in candidate_skills]
        python_covers_ml = {"machine learning", "deep learning", "nlp", "computer vision",
                            "data science", "tensorflow", "pytorch", "scikit-learn"}
        ml_covered_by_python = sum(1 for s in must_have if s.lower() in python_covers_ml)
        python_bonus = 0.0
        if "python" in cand_lower and ml_covered_by_python > 0:
            python_bonus = min(ml_covered_by_python / max(len(must_have), 1) * 0.25, 0.25)

        weighted_score = (0.7 * must_have_rate) + (0.3 * score) + python_bonus
        return min(weighted_score, 1.0)

    def _calc_technical_depth(self, candidate_skills: List[str], jd_skills: Dict, deep_signals: Optional[Dict]) -> float:
        """
        Score technical depth using real GitHub signals:
        - Number of repos with JD-relevant languages
        - Dependency analysis (requirements.txt, package.json, etc.)
        - Primary language match with JD skills
        """
        must_have = [s.lower() for s in jd_skills.get("must_have", [])]
        nice_to_have = [s.lower() for s in jd_skills.get("nice_to_have", [])]
        all_jd_skills = set(must_have + nice_to_have)
        candidate_lower = [s.lower() for s in candidate_skills]

        # Signal 1: Primary language match with JD (biggest signal)
        jd_lang_boost = 0.0
        if deep_signals and deep_signals.get("skill_intelligence"):
            si = deep_signals["skill_intelligence"]
            lang_depth = si.get("language_depth", {})
            if not isinstance(lang_depth, dict) or not lang_depth:
                lang_depth = si.get("primary_language", {})
            if isinstance(lang_depth, dict) and lang_depth:
                top_langs = sorted(lang_depth.items(), key=lambda x: float(x[1]) if not isinstance(x[1], str) else 0, reverse=True)[:3]
                for lang_name, _ in top_langs:
                    lang_lower = lang_name.lower()
                    if len(lang_lower) < 3:
                        continue
                    for jd_skill in all_jd_skills:
                        jd_skill_lower = jd_skill.lower()
                        if lang_lower == jd_skill_lower or lang_lower in jd_skill_lower:
                            jd_lang_boost = 0.35
                            break
                    if jd_lang_boost:
                        break

        # Signal 2: Repo count with primary language
        repo_depth = 0.0
        if deep_signals and deep_signals.get("aggregates"):
            agg = deep_signals["aggregates"]
            total_repos = agg.get("total_repos", 0)
            # More repos = deeper experience
            if total_repos >= 10:
                repo_depth = 0.30
            elif total_repos >= 5:
                repo_depth = 0.20
            elif total_repos >= 2:
                repo_depth = 0.10

        # Signal 3: Dependency evidence (shows real libraries/frameworks used)
        dep_depth = 0.0
        if deep_signals and deep_signals.get("skill_intelligence"):
            si = deep_signals["skill_intelligence"]
            # Check if any inferred skills match JD requirements
            inferred = si.get("inferred_skills", [])
            if isinstance(inferred, list):
                matched_deps = sum(1 for s in inferred if any(dep.lower() in s.lower() or s.lower() in dep.lower() for dep in all_jd_skills))
                dep_depth = min(matched_deps / max(len(all_jd_skills), 1) * 0.35, 0.35)

        # Signal 4: Skill diversity (advanced tools)
        skill_depth = 0.0
        advanced_indicators = {
            "ml": ["tensorflow", "pytorch", "keras", "scikit", "ml", "nlp", "computer vision"],
            "cloud": ["aws", "gcp", "azure", "kubernetes", "docker", "terraform"],
            "web": ["react", "vue", "angular", "django", "flask", "fastapi", "express"],
            "data": ["pandas", "numpy", "spark", "kafka", "airflow", "etl"],
        }
        covered_categories = set()
        for cat, indicators in advanced_indicators.items():
            if any(any(ind in s for s in candidate_lower for ind in indicators) for _ in [1]):
                covered_categories.add(cat)
        skill_depth = min(len(covered_categories) * 0.08, 0.24)

        return min(jd_lang_boost + repo_depth + dep_depth + skill_depth, 1.0)

    def _calc_learning_velocity(self, profile: Dict, deep_signals: Optional[Dict]) -> float:
        """
        Score based on GitHub activity signals — not commit intelligence heuristics.
        Uses: recent commits, repo creation rate, issue/PR activity.
        """
        metrics = profile.get("metrics", {})
        aggregates = {}

        if deep_signals and deep_signals.get("aggregates"):
            aggregates = deep_signals["aggregates"]

        # Recent commits (from aggregates)
        total_commits = aggregates.get("total_commits", 0)
        recent_repos = aggregates.get("total_repos", 0)

        # Score based on activity volume
        if total_commits >= 50:
            activity = 0.50
        elif total_commits >= 20:
            activity = 0.35
        elif total_commits >= 5:
            activity = 0.20
        elif total_commits >= 1:
            activity = 0.10
        else:
            activity = 0.0

        # Diversity bonus (works across multiple repos)
        diversity = min(recent_repos / 10 * 0.20, 0.20)

        # Consistency from metrics
        consistency = metrics.get("activity_consistency", 0.5) * 0.30

        return min(activity + diversity + consistency, 1.0)

    def _calc_soft_skills_match(self, jd_soft_skills: List[str], candidate_signals: List[str]) -> float:
        if not jd_soft_skills:
            return 0.7

        signal_map = {
            "communication": ["readme", "docs", "blog"],
            "leadership": ["mentoring", "team lead"],
            "teamwork": ["community"],
            "problem_solving": ["high_quality_repos"],
        }

        matched = 0
        for skill in jd_soft_skills:
            skill_lower = skill.lower()
            for soft_key, indicators in signal_map.items():
                if soft_key in skill_lower or any(ind in skill_lower for ind in [soft_key]):
                    if any(ind in candidate_signals for ind in indicators):
                        matched += 1
                        break

        return min(matched / len(jd_soft_skills), 1.0) if jd_soft_skills else 0.7

    def _calc_project_complexity(self, profile: Dict) -> float:
        metrics = profile.get("metrics", {})
        repos = profile.get("repositories", [])

        stars = metrics.get("total_stars", 0)
        forks = metrics.get("total_forks", 0)
        avg_stars = metrics.get("avg_stars_per_repo", 0)

        score = 0.3

        if stars > 100:
            score += 0.2
        elif stars > 50:
            score += 0.1

        if forks > 20:
            score += 0.2
        elif forks > 5:
            score += 0.1

        if avg_stars > 20:
            score += 0.3
        elif avg_stars > 10:
            score += 0.15

        return min(score, 1.0)

    def _calc_cultural_fit(self, profile: Dict) -> float:
        score = 0.5

        account_age = profile.get("account_metrics", {}).get("account_age_days", 0)
        if account_age > 365:
            score += 0.15
        if account_age > 1000:
            score += 0.1

        consistency = profile.get("metrics", {}).get("activity_consistency", 0)
        if consistency > 0.7:
            score += 0.15

        followers = profile.get("account_metrics", {}).get("followers", 0)
        following = profile.get("account_metrics", {}).get("following", 1)
        if followers > following:
            score += 0.1

        return min(score, 1.0)

    def _calc_technical_breadth(self, candidate_skills: List[str]) -> float:
        if not candidate_skills:
            return 0.0

        categories = {
            "languages": ["python", "java", "javascript", "typescript", "go", "rust", "c++"],
            "frontend": ["react", "vue", "angular", "html", "css"],
            "backend": ["node.js", "django", "flask", "express", "spring"],
            "databases": ["sql", "postgresql", "mysql", "mongodb", "redis"],
            "cloud": ["aws", "azure", "gcp", "docker", "kubernetes"]
        }

        categories_covered = 0
        for category, techs in categories.items():
            if any(any(tech in skill.lower() for tech in techs) for skill in candidate_skills):
                categories_covered += 1

        return min(categories_covered / len(categories), 1.0)

    def _calculate_composite_score(self, signals: Dict, weights: AdaptiveWeights) -> float:
        score = (
            weights.verified_skill_match * signals.get("verified_skill_match", 0) +
            weights.technical_depth * signals.get("technical_depth", 0) +
            weights.learning_velocity * signals.get("learning_velocity", 0) +
            weights.soft_skills_match * signals.get("soft_skills_match", 0) +
            weights.project_complexity * signals.get("project_complexity", 0) +
            weights.cultural_fit * signals.get("cultural_fit", 0) +
            weights.technical_breadth * signals.get("technical_breadth", 0)
        )
        return min(score, 1.0)

    def _perform_gap_analysis(self, jd_skills: Dict, candidate_skills: List[str], signals: Dict, deep_signals: Optional[Dict] = None) -> Dict:
        must_have = [s.lower() for s in jd_skills.get("must_have", [])]
        nice_to_have = [s.lower() for s in jd_skills.get("nice_to_have", [])]
        candidate_lower = [s.lower() for s in candidate_skills]

        # Get candidate's primary language(s) from SkillAnalyzer for ML adjacency
        primary_langs = set()
        if deep_signals and deep_signals.get("skill_intelligence"):
            lang_depth = deep_signals["skill_intelligence"].get("language_depth", {})
            if isinstance(lang_depth, dict):
                for lang_name in lang_depth.keys():
                    primary_langs.add(lang_name.lower())

        matched = []
        missing = []
        adjacent = []
        partial = []

        # ML-related skills that Python covers automatically
        python_covers_ml = {"machine learning", "deep learning", "nlp", "computer vision", "data science"}

        for skill in must_have:
            if skill in candidate_lower:
                matched.append({"skill": skill, "status": "matched"})
            else:
                adjacents = get_skill_adjacent(skill)
                found_adjacent = False

                # Check if primary language covers this skill (ML domain knowledge)
                if not found_adjacent and primary_langs:
                    for lang in primary_langs:
                        # Python covers ML-related skills
                        if lang == "python" and skill in python_covers_ml:
                            adjacent.append({
                                "required": skill,
                                "candidate_has": "Python (primary language — ML is done in Python)",
                                "learning_time": "0 (already applicable)"
                            })
                            found_adjacent = True
                            break
                        # Any primary language matches adjacent skill
                        for adj in adjacents:
                            if adj.lower() == lang:
                                adjacent.append({
                                    "required": skill,
                                    "candidate_has": adj,
                                    "learning_time": self._estimate_learning_time(skill)
                                })
                                found_adjacent = True
                                break
                        if found_adjacent:
                            break

                # Standard adjacency check
                if not found_adjacent:
                    for adj in adjacents:
                        if adj.lower() in candidate_lower:
                            adjacent.append({
                                "required": skill,
                                "candidate_has": adj,
                                "learning_time": self._estimate_learning_time(skill)
                            })
                            found_adjacent = True
                            break

                if not found_adjacent:
                    missing.append({
                        "skill": skill,
                        "gap_severity": "high",
                        "learning_time": self._estimate_learning_time(skill)
                    })

        for skill in nice_to_have:
            if skill in candidate_lower:
                matched.append({"skill": skill, "status": "matched"})
            else:
                partial.append({"skill": skill, "status": "partial"})

        time_to_productivity = self._estimate_time_to_productivity(missing, adjacent)

        return {
            "matched_skills": matched,
            "missing_skills": missing,
            "adjacent_skills": adjacent,
            "partial_matches": partial,
            "match_rate": len(matched) / max(len(must_have) + len(nice_to_have), 1),
            "time_to_productivity": time_to_productivity,
            "gap_summary": self._summarize_gaps(matched, missing, adjacent)
        }

    def _estimate_learning_time(self, skill: str) -> str:
        skill_lower = skill.lower()
        fast = ["python", "javascript", "sql", "docker", "git"]
        medium = ["react", "node.js", "aws", "postgresql", "typescript"]
        slow = ["kubernetes", "tensorflow", "golang", "rust", "mlops"]

        if any(s in skill_lower for s in fast):
            return "2-4 weeks"
        elif any(s in skill_lower for s in medium):
            return "4-8 weeks"
        elif any(s in skill_lower for s in slow):
            return "8-12 weeks"
        else:
            return "4-8 weeks"

    def _estimate_time_to_productivity(self, missing: List, adjacent: List) -> str:
        total_skills = len(missing) + len(adjacent)
        if total_skills == 0:
            return "1-2 weeks"
        elif total_skills <= 2:
            return "3-4 weeks"
        elif total_skills <= 4:
            return "1-2 months"
        else:
            return "2-3 months"

    def _summarize_gaps(self, matched: List, missing: List, adjacent: List) -> str:
        if not missing and not adjacent:
            return "All required skills matched. Ready to onboard."

        parts = []
        if missing:
            parts.append(f"{len(missing)} skills need training ({', '.join([m['skill'] for m in missing[:3]])}{'...' if len(missing) > 3 else ''})")
        if adjacent:
            parts.append(f"{len(adjacent)} skills have adjacent experience")

        return "; ".join(parts)

    def _generate_reasoning(self, profile: Dict, score: float, signals: Dict, gap_analysis: Dict, jd_context: Dict, weights: AdaptiveWeights) -> str:
        parts = []

        top_weight_key = max(weights.to_dict().items(), key=lambda x: x[1])[0]
        top_weight_val = weights.to_dict()[top_weight_key]

        parts.append(f"Scored for {jd_context['detected_industry'].replace('_', ' ')} role ({top_weight_key.replace('_', ' ')} weighted at {top_weight_val:.0%})")

        skill_score = signals.get("verified_skill_match", 0)
        if skill_score >= 0.7:
            parts.append(f"Strong skill alignment ({skill_score:.0%})")
        elif skill_score >= 0.4:
            parts.append(f"Partial skill match ({skill_score:.0%})")
        else:
            parts.append(f"Limited skill overlap ({skill_score:.0%})")

        velocity = signals.get("learning_velocity", 0)
        if velocity >= 0.7:
            parts.append("Fast learner - can close skill gaps quickly")
        elif velocity >= 0.4:
            parts.append("Moderate learning speed")

        gap_summary = gap_analysis.get("gap_summary", "")
        if gap_summary:
            parts.append(gap_summary)

        return ". ".join(parts) + "."

    def _get_hiring_recommendation(self, score: float, gap_analysis: Dict) -> str:
        if score >= 0.75:
            return "STRONG HIRE"
        elif score >= 0.60:
            return "CONSIDER"
        elif score >= 0.45:
            return "MAYBE"
        else:
            return "PASS"

    def _rate_match(self, score: float) -> str:
        if score >= 0.75:
            return "Excellent Match"
        elif score >= 0.60:
            return "Good Match"
        elif score >= 0.45:
            return "Moderate Match"
        elif score >= 0.30:
            return "Weak Match"
        else:
            return "Poor Match"

    def score_multiple(
        self,
        candidates: List[Dict],
        job_description: str,
        use_llm: bool = True,
        deep_signals_list: Optional[List[Dict]] = None
    ) -> List[Dict]:
        """Score multiple candidates and rank them."""
        results = []

        jd_context = self.jd_analyzer.analyze_jd_context(job_description)

        for i, candidate in enumerate(candidates):
            deep_signals = deep_signals_list[i] if deep_signals_list and i < len(deep_signals_list) else None
            result = self.analyze_and_score(candidate, job_description, use_llm, deep_signals)
            result["jd_context"] = jd_context
            results.append(result)

        results.sort(key=lambda x: x["match_score"], reverse=True)

        for i, result in enumerate(results):
            result["ranking_position"] = i + 1
            if i > 0:
                prev_score = results[i - 1]["match_score"]
                result["score_delta"] = round(prev_score - result["match_score"], 3)
                result["ranking_reasoning"] = self._explain_rank_diff(result, results[i - 1])
            else:
                result["score_delta"] = 0
                result["ranking_reasoning"] = "Top candidate based on adaptive scoring"

        return results

    def _explain_rank_diff(self, current: Dict, previous: Dict) -> str:
        reasons = []
        curr_signals = current["signal_breakdown"]
        prev_signals = previous["signal_breakdown"]

        comparisons = [
            ("verified_skill_match", "skill match"),
            ("learning_velocity", "learning velocity"),
            ("technical_depth", "technical depth"),
        ]

        for key, label in comparisons:
            diff = prev_signals.get(key, 0) - curr_signals.get(key, 0)
            if diff > 0.1:
                reasons.append(f"{label} {diff:.0%} lower")

        if reasons:
            return f"Ranked lower because " + ", ".join(reasons)
        return "Close overall score"
