"""Small, deterministic clean-up of skill names so the same skill always gets the same name."""
import re

# lowercase variant -> standard name
ALIASES = {
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "ai": "Artificial Intelligence",
    "dl": "Deep Learning",
    "nlp": "Natural Language Processing",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",
    "reactjs": "React",
    "react.js": "React",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "ci/cd": "CI/CD",
    "ci cd": "CI/CD",
    "cicd": "CI/CD",
    "ci/cd pipelines": "CI/CD",
    "rest": "REST APIs",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "restful api": "REST APIs",
    "restful apis": "REST APIs",
    "restful services": "REST APIs",
    "rest api design": "REST APIs",
    "git and version control": "Git",
    "amazon web services": "AWS",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "python 3": "Python",
    "c plus plus": "C++",
    "dsa": "Data Structures and Algorithms",
    "oop": "Object-Oriented Programming",
    "object oriented programming": "Object-Oriented Programming",
}


def _one(part: str) -> str:
    cleaned = re.sub(r"\s+", " ", part).strip().strip(".,;:")
    return ALIASES.get(cleaned.lower(), cleaned)


def canonical_name(name: str) -> str:
    """Return the standard name. Handles simple alternatives such as 'AWS or Google Cloud'."""
    name = re.sub(r"\s+", " ", name).strip()
    if "(" not in name and re.search(r"\s+or\s+", name, flags=re.I):
        parts = re.split(r"\s+or\s+", name, flags=re.I)
        return " or ".join(_one(p) for p in parts)
    return _one(name)
