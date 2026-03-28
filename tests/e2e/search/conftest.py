import pytest
import os

def load_search_terms() -> list[str]:
    """Load search terms from data file."""
    # Try current task plan specified path
    path = os.path.join("tests", "e2e", "data", "search_terms.txt")
    if not os.path.exists(path):
        # Fallback to common search terms if task-specific one is missing
        path = os.path.join("tests", "e2e", "data", "common", "search_terms.txt")

    with open(path) as f:
        terms = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return terms

@pytest.fixture(params=load_search_terms())
def search_term(request) -> str:
    """Parametrized fixture providing search terms."""
    return request.param
