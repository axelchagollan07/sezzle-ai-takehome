import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PolicyDocument:
    """A loaded Sezzle policy document."""

    filename: str
    title: str
    content: str
    tokens: frozenset[str]


class PolicyRepository:
    """Loads and retrieves relevant policy documents."""

    def __init__(self, policies_dir: str | None = None) -> None:
        if policies_dir is None:
            policies_dir = "data/policies"

        self.policies_dir = Path(policies_dir)

        if not self.policies_dir.exists():
            raise FileNotFoundError(
                f"Policies directory not found: {self.policies_dir}"
            )

        self.documents = self._load_documents()

        if not self.documents:
            raise RuntimeError("No policy documents were found.")

    def _load_documents(self) -> list[PolicyDocument]:
        documents = []

        for path in sorted(self.policies_dir.glob("*.md")):
            content = path.read_text(encoding="utf-8").strip()

            if not content:
                continue

            title = self._extract_title(path, content)
            tokens = frozenset(self._tokenize(content))

            documents.append(
                PolicyDocument(
                    filename=path.name,
                    title=title,
                    content=content,
                    tokens=tokens,
                )
            )

        return documents

    @staticmethod
    def _extract_title(path: Path, content: str) -> str:
        for line in content.splitlines():
            line = line.strip()

            if line.startswith("#"):
                return line.lstrip("#").strip()

        return path.stem

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def search(
        self,
        query: str,
        top_k: int = 3,
    ) -> list[PolicyDocument]:
        """
        Return the most relevant policy documents for a query.

        Retrieval is intentionally lightweight for the take-home:
        token overlap provides deterministic, dependency-free retrieval.
        """
        query_tokens = set(self._tokenize(query))

        if not query_tokens:
            return []

        scored_documents = []

        for document in self.documents:
            overlap = query_tokens.intersection(document.tokens)

            if not overlap:
                continue

            score = len(overlap)

            scored_documents.append(
                (score, document)
            )

        scored_documents.sort(
            key=lambda item: item[0],
            reverse=True,
        )

        return [
            document
            for _, document in scored_documents[:top_k]
        ]

    def get_all(self) -> list[PolicyDocument]:
        """Return all loaded policy documents."""
        return list(self.documents)