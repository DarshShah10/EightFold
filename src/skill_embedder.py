"""
Semantic Skill Matcher - Uses sentence-transformers + FAISS for embedding-based skill matching.
Handles synonyms: "ML" matches "machine learning", "k8s" matches "kubernetes".
"""

import numpy as np
from typing import List, Dict, Tuple
import re

# Lazy import for heavy dependencies
_sentence_transformer = None
_faiss = None


def _get_transformer():
    global _sentence_transformer
    if _sentence_transformer is None:
        from sentence_transformers import SentenceTransformer
        _sentence_transformer = SentenceTransformer("all-MiniLM-L6-v2")
    return _sentence_transformer


def _get_faiss():
    global _faiss
    if _faiss is None:
        try:
            import faiss
            _faiss = faiss
        except ImportError:
            _faiss = None  # Signal fallback mode
    return _faiss


class SkillEmbedder:
    """Semantic skill matcher using sentence-transformers and FAISS."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        print(f"Loading model: {model_name}...")
        self.model_name = model_name
        self.model = None
        self.index = None
        self.skill_embeddings = None
        self.skill_labels = None
        self.dimension = 384  # all-MiniLM-L6-v2 dimension

    @property
    def transformer(self):
        if self.model is None:
            self.model = _get_transformer()
        return self.model

    def embed_skills(self, skills: List[str]) -> np.ndarray:
        """Convert skills to embeddings."""
        if not skills:
            return np.array([])

        normalized_skills = [s.strip().lower() for s in skills if s.strip()]
        if not normalized_skills:
            return np.array([])

        embeddings = self.transformer.encode(normalized_skills, convert_to_numpy=True)
        return embeddings

    def build_index(self, skills: List[str]):
        """Build a FAISS index for fast similarity search (or fallback to text-based)."""
        if not skills:
            self.index = None
            self.skill_embeddings = None
            self.skill_labels = []
            return

        faiss_lib = _get_faiss()

        if faiss_lib is None:
            # Fallback: store skills as-is, use text matching
            self.index = None
            self.skill_embeddings = None
            self.skill_labels = [s.strip().lower() for s in skills if s.strip()]
            print(f"FAISS not available - using text-based matching with {len(self.skill_labels)} skills")
            return

        embeddings = self.embed_skills(skills)
        faiss_lib.normalize_L2(embeddings)

        self.index = faiss_lib.IndexFlatIP(self.dimension)
        self.index.add(embeddings)

        self.skill_embeddings = embeddings
        self.skill_labels = skills

        print(f"Built FAISS index with {len(skills)} skills")

    def find_matches(self, query_skills: List[str], threshold: float = 0.5, top_k: int = None) -> List[Dict]:
        """Find matches between query skills and indexed skills."""
        if not self.skill_labels or not query_skills:
            return []

        if self.index is None:
            # Fallback: text-based matching using aliases
            return self._text_based_match(query_skills, threshold)

        query_embeddings = self.embed_skills(query_skills)
        faiss_lib = _get_faiss()
        faiss_lib.normalize_L2(query_embeddings)

        k = min(len(self.skill_labels), query_embeddings.shape[0])
        if top_k:
            k = min(k, top_k)

        scores, indices = self.index.search(query_embeddings, k)

        matches = []
        for i, (query_skill, score_row, idx_row) in enumerate(zip(query_skills, scores, indices)):
            for score, idx in zip(score_row, idx_row):
                if idx == -1:
                    continue
                if score >= threshold:
                    matched_skill = self.skill_labels[idx]
                    matches.append({
                        "query_skill": query_skill,
                        "matched_skill": matched_skill,
                        "similarity": float(score),
                        "is_exact": matched_skill.lower() == query_skill.lower()
                    })

        return matches

    def _text_based_match(self, query_skills: List[str], threshold: float = 0.5) -> List[Dict]:
        """Fallback text-based matching using skill aliases and normalization."""
        matches = []
        for query_skill in query_skills:
            query_norm = normalize_skill(query_skill)
            best_match = None
            best_score = 0.0

            for label in self.skill_labels:
                label_norm = normalize_skill(label)
                if query_norm == label_norm:
                    best_score = 1.0
                    best_match = label
                    break
                # Check if one contains the other
                if query_norm in label_norm or label_norm in query_norm:
                    if len(query_norm) >= 4 and len(label_norm) >= 4:
                        if best_score < 0.7:
                            best_score = 0.7
                            best_match = label

            if best_match and best_score >= threshold:
                matches.append({
                    "query_skill": query_skill,
                    "matched_skill": best_match,
                    "similarity": best_score,
                    "is_exact": best_score == 1.0
                })

        return matches

    def match_skill_lists(self, jd_skills: List[str], candidate_skills: List[str], threshold: float = 0.45) -> Dict:
        """Match two skill lists bidirectionally."""
        self.build_index(candidate_skills)
        jd_to_candidate = self.find_matches(jd_skills, threshold)

        self.build_index(jd_skills)
        candidate_to_jd = self.find_matches(candidate_skills, threshold)

        matched_pairs = {}
        for match in jd_to_candidate + candidate_to_jd:
            key = (match["query_skill"], match["matched_skill"])
            if key not in matched_pairs or match["similarity"] > matched_pairs[key]["similarity"]:
                matched_pairs[key] = match

        results = {"matched": [], "synonyms": [], "missing": [], "extra": []}
        matched_jd_skills = set()
        matched_candidate_skills = set()

        for pair_key, match_data in matched_pairs.items():
            jd_skill, cand_skill = pair_key
            score = match_data["similarity"]

            if score >= 0.85:
                results["matched"].append({"jd_skill": jd_skill, "candidate_skill": cand_skill, "similarity": score})
                matched_jd_skills.add(jd_skill.lower())
                matched_candidate_skills.add(cand_skill.lower())
            elif score >= threshold:
                results["synonyms"].append({"jd_skill": jd_skill, "candidate_skill": cand_skill, "similarity": score})
                matched_jd_skills.add(jd_skill.lower())
                matched_candidate_skills.add(cand_skill.lower())

        for skill in jd_skills:
            if skill.lower() not in matched_jd_skills:
                results["missing"].append(skill)

        for skill in candidate_skills:
            if skill.lower() not in matched_candidate_skills:
                results["extra"].append(skill)

        return results

    def compute_skill_match_score(self, jd_skills: List[str], candidate_skills: List[str]) -> Tuple[float, Dict]:
        """Compute weighted skill match score."""
        matches = self.match_skill_lists(jd_skills, candidate_skills)

        if not jd_skills:
            return 0.0, {"error": "No JD skills provided"}

        total_jd_skills = len(jd_skills)
        exact_matches = len(matches["matched"])
        synonym_matches = len(matches["synonyms"])

        weighted_score = (exact_matches + (synonym_matches * 0.7)) / total_jd_skills

        breakdown = {
            "total_jd_skills": total_jd_skills,
            "exact_matches": exact_matches,
            "synonym_matches": synonym_matches,
            "missing_skills": len(matches["missing"]),
            "matched_skills": [m["jd_skill"] for m in matches["matched"]],
            "synonym_skills": [s["jd_skill"] for s in matches["synonyms"]],
            "missing_skills_list": matches["missing"]
        }

        return min(weighted_score, 1.0), breakdown


# Skill normalization utilities
SKILL_ALIASES = {
    "ml": "machine learning", "ai": "artificial intelligence", "k8s": "kubernetes",
    "react.js": "react", "vue.js": "vue", "nodejs": "node.js", "ts": "typescript",
    "pyspark": "spark", "tf": "tensorflow", "postgres": "postgresql", "py": "python",
}


def normalize_skill(skill: str) -> str:
    """Normalize skill names to handle common variations."""
    skill_lower = skill.lower().strip()
    return SKILL_ALIASES.get(skill_lower, skill_lower)


def batch_normalize_skills(skills: List[str]) -> List[str]:
    """Normalize a list of skills."""
    return [normalize_skill(s) for s in skills]


if __name__ == "__main__":
    import json
    embedder = SkillEmbedder()

    jd_skills = ["Machine Learning", "Python", "Kubernetes", "SQL", "AWS"]
    candidate_skills = ["Python", "ML", "k8s", "PostgreSQL", "AWS", "Docker"]

    score, breakdown = embedder.compute_skill_match_score(jd_skills, candidate_skills)

    print(f"Skill Match Score: {score:.2%}")
    print(json.dumps(breakdown, indent=2))
