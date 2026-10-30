"""Check new interview questions before adding them to the playbook.

For each question in the input file, reports:
- DUPLICATE: the same question already exists in the playbook (file and heading shown).
- SIMILAR:   a close match exists; review it before adding.
- NEW:       no close match. Shows the suggested section and file.

Input: a text or markdown file with one question per line. Lines starting with "- " or
"N. " are stripped of the marker. Blank lines and lines starting with "#" are skipped.

Usage:
    python tools/question_check.py questions.txt
    python tools/question_check.py questions.txt --tracker path/to/QUESTIONS_TODO.json

The script never edits the playbook. Review the report, then add the questions by hand or
ask for them to be added.
"""
import argparse
import json
import re
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = ROOT / "docs" / "interview-questions"
SKIP_FILES = {"index.md", "interview-process.md", "quick-reference.md", "how-to-approach-coding-questions.md"}
HEADING = re.compile(r"^## (?:\d+\.\s*)?(.+?)\s*$")
STOP = {"a", "an", "the", "of", "in", "on", "to", "and", "or", "is", "are", "what", "how", "why",
        "when", "does", "do", "you", "your", "explain", "describe", "between", "difference", "with",
        "for", "it", "be", "can", "that", "this", "from", "by", "as", "at"}

# Keyword scores decide the section. The company group is checked first.
SECTIONS = {
    "behavioural/": ["tell me about", "conflict", "team", "leadership", "failure", "mistake", "challenge",
                     "motivat", "strength", "weakness", "situation", "star", "deadline", "stakeholder"],
    "coding/": ["write a program", "implement", "reverse", "algorithm", "complexity", "big o", "big-o",
                "array", "linked list", "tree", "graph", "palindrome", "subarray", "stream", "lambda",
                "trace the output", "sort", "two sum", "dynamic programming", "recursion"],
    "technical/core-java": ["==", "equals", "immutable", "string", "final", "finally", "finalize", "casting",
                            "hashmap", "comparable", "comparator", "overload", "override", "abstract",
                            "interface", "checked", "exception", "generics", "iterator"],
    "technical/advanced-java-concurrency": ["thread", "synchronized", "volatile", "executor", "future",
                                            "completablefuture", "deadlock", "garbage", "gc", "jvm",
                                            "memory", "concurren", "atomic", "lock"],
    "technical/spring-and-security": ["spring", "bean", "autowired", "@", "boot", "jwt", "oauth", "security",
                                      "transactional", "dependency injection", "controller", "rest"],
    "technical/data-and-persistence": ["sql", "join", "index", "database", "jdbc", "jpa", "hibernate",
                                       "normalis", "normaliz", "isolation", "acid", "transaction", "query",
                                       "mybatis", "postgres", "mysql", "redis"],
    "technical/architecture-and-distributed": ["microservice", "kafka", "saga", "circuit", "distributed",
                                               "cap theorem", "event", "consistency", "monolith", "queue",
                                               "rabbitmq", "idempotent", "cach", "cdn"],
    "technical/devops-cloud-and-ai": ["docker", "kubernetes", "pipeline", "ci/cd", "jenkins", "aws", "cloud",
                                      "helm", "argo", "container", "observab", "prometheus", "grafana",
                                      "llm", "rag", "deploy"],
    "technical/design-patterns": ["pattern", "singleton", "factory", "builder", "observer", "strategy",
                                  "decorator", "adapter", "proxy", "facade", "command"],
    "technical/ai-and-machine-learning": ["machine learning", "overfit", "underfit", "model", "neural",
                                          "transformer", "precision", "recall", "supervised", "bias-variance",
                                          "embedding"],
}
COMPANY_NAMES = ["walmart", "costco", "equifax", "tcs", "wipro", "ibs", "uniqlo"]


def normalise(text: str) -> list[str]:
    text = text.lower().replace("`", " ")
    words = re.findall(r"[a-z0-9@#+./-]+|==|!=", text)
    return [w for w in words if w not in STOP]


def existing_questions() -> list[tuple[str, str]]:
    found = []
    for md in sorted(QUESTIONS_DIR.rglob("*.md")):
        if md.name in SKIP_FILES:
            continue
        for line in md.read_text(encoding="utf-8").splitlines():
            m = HEADING.match(line)
            if m:
                found.append((md.relative_to(ROOT).as_posix(), m.group(1)))
    return found


def similarity(a: str, b: str) -> float:
    ta, tb = set(normalise(a)), set(normalise(b))
    jaccard = len(ta & tb) / len(ta | tb) if ta | tb else 0.0
    ratio = SequenceMatcher(None, " ".join(normalise(a)), " ".join(normalise(b))).ratio()
    return max(jaccard, ratio)


def suggest_section(question: str) -> str:
    q = question.lower()
    if any(name in q for name in COMPANY_NAMES):
        return "PRIVATE: company-based (Company-Interview-Notes repo)"
    best, best_score = "REVIEW: no clear section", 0
    for section, keywords in SECTIONS.items():
        score = sum(1 for k in keywords if k in q)
        if score > best_score:
            best, best_score = section, score
    if best_score == 0:
        return "REVIEW: no clear section"
    return best


def tracker_questions(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    out = {}
    for category in data.get("categories", {}).values():
        for item in category.get("questions", []):
            out[item["id"]] = item["question"]
    return out


def load_input(path: Path) -> list[str]:
    items = []
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        s = re.sub(r"^(?:[-*]|\d+[.)])\s+", "", s)
        items.append(s)
    return items


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input", type=Path)
    parser.add_argument("--tracker", type=Path, help="optional QUESTIONS_TODO.json to check against")
    args = parser.parse_args()

    existing = existing_questions()
    print(f"Playbook questions loaded: {len(existing)}")
    questions = load_input(args.input)
    tracker = tracker_questions(args.tracker) if args.tracker else {}

    counts = {"DUPLICATE": 0, "SIMILAR": 0, "NEW": 0}
    for q in questions:
        if any(name in q.lower() for name in COMPANY_NAMES):
            counts["NEW"] += 1
            print(f"[NEW] {q}")
            print("    PRIVATE: company-based (Company-Interview-Notes repo)")
            continue
        best_file, best_title, best_score = None, None, 0.0
        for file, title in existing:
            score = similarity(q, title)
            if score > best_score:
                best_file, best_title, best_score = file, title, score
        if best_score >= 0.7:
            status, detail = "DUPLICATE", f"{best_file}: {best_title}"
        elif best_score >= 0.5:
            status, detail = "SIMILAR", f"{best_file}: {best_title}"
        else:
            status, detail = "NEW", suggest_section(q)
        counts[status] += 1
        print(f"[{status}] {q}")
        print(f"    {detail}  (score {best_score:.2f})")
        if tracker:
            hits = [i for i, t in tracker.items() if similarity(q, t) >= 0.75 and t != q]
            if hits:
                print(f"    also in tracker: {', '.join(hits)}")
    print()
    print(f"Totals: {counts}")


if __name__ == "__main__":
    main()
