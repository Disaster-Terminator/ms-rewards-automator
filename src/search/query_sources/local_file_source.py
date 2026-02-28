"""
Local file query source - loads queries from a text file
"""

import random
from pathlib import Path

from .query_source import QuerySource


class LocalFileSource(QuerySource):
    """Query source that loads queries from a local text file"""

    # Phrase templates for generating meaningful searches
    PHRASE_TEMPLATES = [
        "how to {}",
        "what is {}",
        "best {}",
        "top {}",
        "guide to {}",
        "tips for {}",
        "learn {}",
        "{} tutorial",
        "{} review",
        "{} explained",
        "why {}",
        "when to {}",
        "where to find {}",
        "benefits of {}",
        "history of {}",
    ]

    # Connectors for combining terms
    CONNECTORS = ["and", "or", "vs", "versus", "with", "for", "in"]

    def __init__(self, config):
        """
        Initialize local file source

        Args:
            config: ConfigManager instance
        """
        super().__init__(config)
        self.base_terms: list[str] = []
        self.generated_phrases: list[str] = []
        self.used_terms: set[str] = set()

        # Load search terms file
        terms_file = config.get("search.search_terms_file", "tools/search_terms.txt")
        self._load_terms_from_file(terms_file)

        # Generate phrase combinations
        self._generate_phrase_combinations()

        self.logger.info(
            f"LocalFileSource initialized: {len(self.base_terms)} base terms, "
            f"{len(self.generated_phrases)} generated phrases"
        )

    def _load_terms_from_file(self, file_path: str) -> None:
        """Load search terms from file"""
        try:
            if not Path(file_path).exists():
                self.logger.error(f"Search terms file not found: {file_path}")
                self.base_terms = self._get_default_terms()
                return

            with open(file_path, encoding="utf-8") as f:
                terms = [line.strip() for line in f if line.strip()]

            # Filter out single-character terms
            terms = [t for t in terms if len(t) > 1]

            if not terms:
                self.logger.warning(f"Search terms file is empty: {file_path}")
                self.base_terms = self._get_default_terms()
                return

            self.base_terms = terms
            self.logger.info(f"Loaded {len(terms)} search terms from file")

        except Exception as e:
            self.logger.error(f"Failed to load search terms file: {e}")
            self.base_terms = self._get_default_terms()

    def _get_default_terms(self) -> list[str]:
        """Get default search terms"""
        return [
            "python programming",
            "machine learning",
            "web development",
            "data science",
            "artificial intelligence",
            "cloud computing",
            "cybersecurity",
            "mobile apps",
            "blockchain",
            "digital marketing",
        ]

    def _generate_phrase_combinations(self) -> None:
        """Generate phrase combinations from base terms"""
        phrases = []

        # 1. Use templates to generate phrases
        for term in self.base_terms[:50]:  # Limit to avoid too many
            for template in self.PHRASE_TEMPLATES:
                phrase = template.format(term)
                phrases.append(phrase)

        # 2. Generate "term + connector + term" combinations
        for i, term1 in enumerate(self.base_terms[:30]):
            for term2 in self.base_terms[i + 1 : i + 6]:  # Limit combinations
                if self._are_related(term1, term2):
                    # Direct combination
                    phrases.append(f"{term1} {term2}")

                    # With connector
                    connector = random.choice(self.CONNECTORS)
                    phrases.append(f"{term1} {connector} {term2}")

        self.generated_phrases = phrases
        self.logger.info(f"Generated {len(phrases)} phrase combinations")

    def _are_related(self, term1: str, term2: str) -> bool:
        """Simple relatedness check"""
        words1 = set(term1.lower().split())
        words2 = set(term2.lower().split())

        # If they share words, consider them related
        if words1 & words2:
            return True

        # Or randomly consider them related (for diversity)
        return random.random() < 0.3

    async def fetch_queries(self, count: int) -> list[str]:
        """
        Fetch queries from local file

        Args:
            count: Number of queries to fetch

        Returns:
            List of query strings
        """
        queries = []
        candidates = []

        # Build candidate pool
        # 40% probability to use generated phrases
        if self.generated_phrases and random.random() < 0.4:
            candidates.extend(self.generated_phrases)

        # 60% probability to use base terms
        candidates.extend(self.base_terms)

        # Filter out recently used terms
        available = [t for t in candidates if t not in self.used_terms]

        if not available:
            self.logger.debug("All search terms used, resetting usage record")
            self.used_terms.clear()
            available = candidates

        selected = random.sample(available, min(count, len(available)))
        queries.extend(selected)
        self.used_terms.update(selected)

        # If usage record exceeds 70% of candidates, clear half
        if len(self.used_terms) > len(candidates) * 0.7:
            old_size = len(self.used_terms)
            self.used_terms = set(list(self.used_terms)[old_size // 2 :])
            self.logger.debug(
                f"Usage record too large, cleared {old_size - len(self.used_terms)} entries"
            )

        self.logger.debug(f"Fetched {len(queries)} queries from local file")
        return queries

    def get_source_name(self) -> str:
        """Return the name of this source"""
        return "local_file"

    def get_priority(self) -> int:
        """Return priority (lower = higher priority)"""
        return 100

    def is_available(self) -> bool:
        """Check if this source is available"""
        return len(self.base_terms) > 0
