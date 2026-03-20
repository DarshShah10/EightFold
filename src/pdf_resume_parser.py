"""
Advanced Resume Parser with Multiple Backend Support
Uses Docling (preferred), PyMuPDF, or pdfplumber for best results.
"""

import re
import json
from typing import Dict, List, Optional, Tuple
import os

DOCLING_AVAILABLE = False
PYMUPDF_AVAILABLE = False

try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    pass

try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    try:
        import pymupdf
        PYMUPDF_AVAILABLE = True
    except ImportError:
        pass


class DoclingResumeParser:
    def __init__(self):
        if not DOCLING_AVAILABLE:
            raise ImportError("Docling not installed. Run: pip install docling")
        self.converter = DocumentConverter()

    def extract_text_and_links(self, pdf_path: str) -> Tuple[str, List[Dict]]:
        doc = self.converter.convert(pdf_path)
        text_parts = []
        hyperlinks = []

        for page in doc.pages:
            page_text = page.export_to_text()
            text_parts.append(page_text)

            if hasattr(page, 'links') and page.links:
                for link in page.links:
                    if hasattr(link, 'uri') and link.uri:
                        hyperlinks.append({
                            "uri": link.uri,
                            "page": page.page_number,
                            "link_text": getattr(link, 'text', '') or '',
                            "bbox": getattr(link, 'bbox', None)
                        })

            if hasattr(doc, 'export_to_dict'):
                doc_dict = doc.export_to_dict()
                hyperlinks.extend(self._extract_links_from_dict(doc_dict, page.page_number))

        full_text = "\n".join(text_parts)
        return full_text, hyperlinks

    def _extract_links_from_dict(self, doc_dict: Dict, page_num: int) -> List[Dict]:
        links = []
        def traverse(obj):
            if isinstance(obj, dict):
                if obj.get('type') == 'link' or 'uri' in obj:
                    links.append({"uri": obj.get('uri', ''), "page": page_num, "link_text": obj.get('text', '')})
                for v in obj.values():
                    traverse(v)
            elif isinstance(obj, list):
                for item in obj:
                    traverse(item)
        traverse(doc_dict)
        return links

    def parse_resume(self, pdf_path: str) -> Dict:
        text, hyperlinks = self.extract_text_and_links(pdf_path)
        return self._create_result(pdf_path, text, hyperlinks)

    def _create_result(self, pdf_path: str, text: str, hyperlinks: List[Dict]) -> Dict:
        github_profiles = self._extract_github(hyperlinks, text)
        linkedin_profiles = self._extract_linkedin(hyperlinks)

        return {
            "filename": os.path.basename(pdf_path),
            "name": self._extract_name(text),
            "email": self._extract_email(text),
            "github_profiles": github_profiles,
            "github_handles": [gh["handle"] for gh in github_profiles],
            "linkedin_profiles": linkedin_profiles,
            "skills": self._extract_skills(text),
            "raw_text": text[:8000],
            "text_length": len(text),
            "hyperlinks_found": len(hyperlinks),
            "parser_used": "docling",
            "debug_info": {"hyperlinks": hyperlinks[:20]}
        }

    def _extract_github(self, hyperlinks: List[Dict], text: str) -> List[Dict]:
        profiles = []
        seen_handles = set()

        for link in hyperlinks:
            uri = link.get("uri", "")
            if not uri:
                continue
            uri_lower = uri.lower()
            if "github.com" in uri_lower or "github.io" in uri_lower:
                handle = self._extract_handle_from_url(uri)
                if handle and handle not in seen_handles:
                    if self._is_valid_github_profile(handle, uri):
                        seen_handles.add(handle)
                        profiles.append({"url": uri, "handle": handle, "link_text": link.get("link_text", ""), "source": "hyperlink", "is_profile": True})

        text_handles = self._extract_handles_from_text(text)
        for handle in text_handles:
            if handle not in seen_handles:
                if self._is_likely_profile(handle, text):
                    seen_handles.add(handle)
                    profiles.append({"url": f"https://github.com/{handle}", "handle": handle, "link_text": f"@{handle}", "source": "text_pattern", "is_profile": True})

        return profiles

    def _extract_handle_from_url(self, url: str) -> str:
        url = url.rstrip('/').replace('.git', '')
        parts = url.split('/')
        if 'github.com' in url or 'github.io' in url:
            for i, part in enumerate(parts):
                if 'github.com' in part.lower():
                    if i + 1 < len(parts):
                        handle = parts[i + 1]
                        if i + 2 < len(parts):
                            next_part = parts[i + 2]
                            if '.' in next_part or next_part in ['repos', 'issues', 'pulls', 'tree', 'blob']:
                                continue
                            return handle
                        return handle
        return ""

    def _is_valid_github_profile(self, handle: str, url: str) -> bool:
        if not handle:
            return False
        skip_words = {'settings', 'repositories', 'stars', 'followers', 'following', 'packages', 'projects', 'pulls', 'issues', 'wiki', 'actions', 'security', 'insights', 'notifications', 'new', 'explore', 'trending', 'collections', 'topics', 'events', 'sponsors', 'orgs', 'organizations', 'pages', 'site', 'blog'}
        if handle.lower() in skip_words:
            return False
        url_lower = url.lower()
        for skip in skip_words:
            if f'/users/{skip}' in url_lower or f'/orgs/{skip}' in url_lower:
                return False
        parsed = re.sub(r'https?://', '', url)
        segments = [s for s in parsed.split('/') if s and s.lower() not in ['github.com', 'www.github.com']]
        if len(segments) > 1:
            if len(segments) >= 2:
                second = segments[1].lower()
                if second in skip_words or '.' in second:
                    return False
        return True

    def _is_likely_profile(self, handle: str, text: str) -> bool:
        text_lower = text.lower()
        pos = text_lower.find(handle.lower())
        if pos >= 0:
            context = text_lower[max(0, pos-50):pos+50]
            if 'github' in context or '@' in context:
                return True
        return False

    def _extract_handles_from_text(self, text: str) -> List[str]:
        handles = []
        pattern = r'github\.com/([a-zA-Z0-9][a-zA-Z0-9_-]{0,38})(?:\s|/|,|$|\))'
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if self._is_valid_username(match):
                handles.append(match)
        return handles

    def _is_valid_username(self, username: str) -> bool:
        if not username:
            return False
        if username[0] == '-' or username[-1] == '-':
            return False
        if len(username) < 2 or len(username) > 39:
            return False
        return True

    def _extract_linkedin(self, hyperlinks: List[Dict]) -> List[Dict]:
        profiles = []
        for link in hyperlinks:
            uri = link.get("uri", "")
            if "linkedin.com" in uri.lower():
                match = re.search(r'linkedin\.com/in/([a-zA-Z0-9_-]+)', uri, re.IGNORECASE)
                if match:
                    profiles.append({"url": uri, "handle": match.group(1), "link_text": link.get("link_text", "")})
        return profiles

    def _extract_name(self, text: str) -> Optional[str]:
        lines = text.strip().split('\n')
        for line in lines[:8]:
            line = line.strip()
            if not line or len(line) < 3 or len(line) > 60:
                continue
            if re.search(r'(resume|cv|curriculum|vitae|http|@|\+|portfolio|email|phone|address)', line.lower()):
                continue
            if re.match(r'^[\d\s\-\(\)\.\*\#]+$', line):
                continue
            return line
        return None

    def _extract_email(self, text: str) -> Optional[str]:
        pattern = r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    def _extract_skills(self, text: str) -> List[str]:
        skills = {"Python", "Java", "JavaScript", "TypeScript", "C++", "C#", "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R",
            "React", "Angular", "Vue", "Node.js", "HTML", "CSS", "SASS", "Tailwind", "Next.js", "Nuxt", "Express", "Django", "Flask", "FastAPI",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "DynamoDB", "SQL", "NoSQL", "Firebase", "Cassandra",
            "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform", "Jenkins", "CI/CD", "GitHub Actions", "Linux", "Nginx",
            "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Keras", "NLP", "Computer Vision", "AI", "Scikit-learn", "OpenCV",
            "Spark", "Hadoop", "Kafka", "Airflow", "Snowflake", "ETL", "Git", "GraphQL", "REST", "Agile", "Scrum"}
        found = [s for s in skills if re.search(r'\b' + re.escape(s) + r'\b', text, re.IGNORECASE)]
        return list(set(found))

    def parse_multiple(self, pdf_paths: List[str]) -> List[Dict]:
        results = []
        for path in pdf_paths:
            try:
                result = self.parse_resume(path)
                result["parse_status"] = "success"
                results.append(result)
            except Exception as e:
                results.append({"filename": os.path.basename(path), "parse_status": "error", "error": str(e), "github_profiles": [], "github_handles": [], "skills": []})
        return results


class PyMuPDFParser:
    def __init__(self):
        if not PYMUPDF_AVAILABLE:
            raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")

    def extract_text_and_links(self, pdf_path: str) -> Tuple[str, List[Dict]]:
        doc = fitz.open(pdf_path)
        full_text = ""
        hyperlinks = []

        for page_num, page in enumerate(doc):
            page_text = page.get_text()
            full_text += page_text + "\n"

            link_list = page.get_links()
            for link in link_list:
                if "uri" in link and link["uri"]:
                    bbox = link.get("bbox")
                    link_text = ""
                    if bbox:
                        link_rect = fitz.Rect(bbox)
                        expanded_rect = fitz.Rect(max(0, bbox[0] - 50), max(0, bbox[1] - 10), bbox[2] + 50, bbox[3] + 10)
                        nearby_text = page.get_text("text", clip=expanded_rect)
                        lines = nearby_text.strip().split('\n')
                        if lines:
                            link_text = lines[0].strip()
                    hyperlinks.append({"uri": link["uri"], "page": page_num + 1, "link_text": link_text, "bbox": bbox})

            text_urls = self._extract_urls_from_text(page_text)
            for url_info in text_urls:
                if not any(h.get("uri") == url_info["url"] for h in hyperlinks):
                    hyperlinks.append({"uri": url_info["url"], "page": page_num + 1, "link_text": url_info.get("context", ""), "source": "text_pattern"})

        doc.close()
        return full_text, hyperlinks

    def _extract_urls_from_text(self, text: str) -> List[Dict]:
        urls = []
        gh_pattern = r'(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9][a-zA-Z0-9_-]{0,38})(?:/[\w.-]*)?(?:\s|$|,|\))'
        for match in re.finditer(gh_pattern, text, re.IGNORECASE):
            handle = match.group(1)
            if self._is_valid_username(handle):
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()
                urls.append({"url": f"https://github.com/{handle}", "context": context})
        return urls

    def _is_valid_username(self, username: str) -> bool:
        if not username or len(username) < 2 or len(username) > 39:
            return False
        if username[0] in '-_' or username[-1] in '-_':
            return False
        skip = {'repos', 'issues', 'pulls', 'wiki', 'actions', 'settings', 'explore', 'trending'}
        if username.lower() in skip:
            return False
        return True

    def parse_resume(self, pdf_path: str) -> Dict:
        text, hyperlinks = self.extract_text_and_links(pdf_path)
        return self._create_result(pdf_path, text, hyperlinks)

    def _create_result(self, pdf_path: str, text: str, hyperlinks: List[Dict]) -> Dict:
        github_profiles = self._extract_github(hyperlinks, text)
        linkedin_profiles = self._extract_linkedin(hyperlinks)

        return {
            "filename": os.path.basename(pdf_path),
            "name": self._extract_name(text),
            "email": self._extract_email(text),
            "github_profiles": github_profiles,
            "github_handles": [gh["handle"] for gh in github_profiles],
            "linkedin_profiles": linkedin_profiles,
            "skills": self._extract_skills(text),
            "raw_text": text[:8000],
            "text_length": len(text),
            "hyperlinks_found": len(hyperlinks),
            "parser_used": "pymupdf",
            "debug_info": {"hyperlinks": hyperlinks[:20]}
        }

    def _extract_github(self, hyperlinks: List[Dict], text: str) -> List[Dict]:
        profiles = []
        seen = set()

        for link in hyperlinks:
            uri = link.get("uri", "")
            if not uri:
                continue
            if "github.com" not in uri.lower():
                continue
            handle = self._extract_handle_from_url(uri)
            if handle and handle not in seen:
                if self._is_valid_username(handle):
                    seen.add(handle)
                    profiles.append({"url": uri if uri.startswith('http') else f"https://{uri}", "handle": handle, "link_text": link.get("link_text", ""), "source": "hyperlink"})

        text_handles = self._extract_handles_from_text(text)
        for handle in text_handles:
            if handle not in seen:
                seen.add(handle)
                profiles.append({"url": f"https://github.com/{handle}", "handle": handle, "link_text": f"@{handle}", "source": "text"})

        return profiles

    def _extract_handle_from_url(self, url: str) -> str:
        url = re.sub(r'^https?://(www\.)?', '', url.lower())
        url = url.rstrip('/').replace('.git', '')
        parts = url.split('/')
        for i, part in enumerate(parts):
            if 'github' in part:
                if i + 1 < len(parts):
                    next_part = parts[i + 1]
                    if next_part and not any(s in next_part.lower() for s in ['repos', 'issues', 'pulls', 'wiki']):
                        return next_part
        return ""

    def _extract_handles_from_text(self, text: str) -> List[str]:
        pattern = r'github\.com/([a-zA-Z0-9][a-zA-Z0-9_-]{0,38})(?:\s|$|,|\))'
        handles = []
        for match in re.findall(pattern, text, re.IGNORECASE):
            if self._is_valid_username(match):
                handles.append(match)
        return handles

    def _extract_linkedin(self, hyperlinks: List[Dict]) -> List[Dict]:
        profiles = []
        for link in hyperlinks:
            uri = link.get("uri", "")
            match = re.search(r'linkedin\.com/in/([a-zA-Z0-9_-]+)', uri, re.IGNORECASE)
            if match:
                profiles.append({"url": uri, "handle": match.group(1), "link_text": link.get("link_text", "")})
        return profiles

    def _extract_name(self, text: str) -> Optional[str]:
        lines = text.strip().split('\n')
        for line in lines[:8]:
            line = line.strip()
            if line and 3 < len(line) < 60:
                if not re.search(r'(resume|cv|http|@|\+|email|phone)', line.lower()):
                    if not re.match(r'^[\d\s\-\(\)\.]+$', line):
                        return line
        return None

    def _extract_email(self, text: str) -> Optional[str]:
        match = re.search(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', text)
        return match.group(0) if match else None

    def _extract_skills(self, text: str) -> List[str]:
        skills = {"Python", "Java", "JavaScript", "TypeScript", "C++", "Go", "Rust", "React", "Angular", "Vue", "Node.js", "Django", "Flask",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQL", "AWS", "Azure", "GCP", "Docker", "Kubernetes", "Terraform",
            "Machine Learning", "TensorFlow", "PyTorch", "Deep Learning", "Git", "GraphQL", "REST", "Linux"}
        found = [s for s in skills if re.search(r'\b' + re.escape(s) + r'\b', text, re.IGNORECASE)]
        return list(set(found))

    def parse_multiple(self, pdf_paths: List[str]) -> List[Dict]:
        results = []
        for path in pdf_paths:
            try:
                result = self.parse_resume(path)
                result["parse_status"] = "success"
                results.append(result)
            except Exception as e:
                results.append({"filename": os.path.basename(path), "parse_status": "error", "error": str(e), "github_profiles": [], "github_handles": [], "skills": []})
        return results


def get_resume_parser():
    """Get the best available resume parser."""
    if DOCLING_AVAILABLE:
        return DoclingResumeParser()
    elif PYMUPDF_AVAILABLE:
        return PyMuPDFParser()
    else:
        raise ImportError("No suitable PDF parser available. Install: pip install pymupdf")


class AdvancedResumeParser:
    """Main parser class - automatically uses best available backend."""

    def __init__(self):
        self.parser = get_resume_parser()

    def parse_resume(self, pdf_path: str) -> Dict:
        return self.parser.parse_resume(pdf_path)

    def parse_multiple_resumes(self, pdf_paths: List[str]) -> List[Dict]:
        return self.parser.parse_multiple(pdf_paths)


if __name__ == "__main__":
    print("Available backends:")
    print(f"  Docling: {DOCLING_AVAILABLE}")
    print(f"  PyMuPDF: {PYMUPDF_AVAILABLE}")
    try:
        parser = get_resume_parser()
        print(f"\nUsing parser: {type(parser).__name__}")
    except ImportError as e:
        print(f"\nError: {e}")
