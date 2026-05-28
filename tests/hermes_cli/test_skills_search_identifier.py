"""Test that `hermes skills search` table does not truncate identifiers.

Regression test for https://github.com/NousResearch/hermes-agent/issues/33674

The Identifier column in the search results table must use overflow="fold"
so that long slugs are wrapped rather than truncated. Additionally, a
copyable identifier list must be printed below the table so users can
easily copy the full identifier for `hermes skills install`.
"""

import io
from unittest.mock import MagicMock, patch

from rich.console import Console

from hermes_cli.skills_hub import do_search


class _FakeResult:
    """Minimal SkillMeta-like object for testing table rendering."""
    def __init__(self, name, identifier, description="A skill.", source="browse-sh",
                 trust_level="community"):
        self.name = name
        self.identifier = identifier
        self.description = description
        self.source = source
        self.trust_level = trust_level


def _render_search_table(results, width=80):
    """Run do_search with mocked dependencies and capture the rendered output."""
    buf = io.StringIO()
    console = Console(file=buf, width=width)

    with patch("tools.skills_hub.GitHubAuth"), \
         patch("tools.skills_hub.create_source_router"), \
         patch("tools.skills_hub.unified_search", return_value=results):
        do_search("weather", console=console)

    return buf.getvalue()


class TestSearchIdentifierCopyableList:
    """Verify that full identifiers are printed in a copyable list below the table."""

    def test_long_browse_sh_slug_in_copyable_list(self):
        """browse.sh slugs like browse-sh/weather.gov/get-forecast-1uezib
        must appear in the copyable identifier list."""
        long_id = "browse-sh/weather.gov/get-forecast-1uezib"
        results = [_FakeResult("get-forecast", long_id)]
        output = _render_search_table(results, width=80)

        # The full identifier must appear in the copyable list
        assert long_id in output, (
            f"Expected full identifier '{long_id}' in output, but it was missing.\n"
            f"Output:\n{output}"
        )

    def test_long_slug_visible_in_narrow_terminal(self):
        """Even in a 60-char terminal the full identifier should be present
        in the copyable list below the table."""
        long_id = "browse-sh/weather.gov/get-forecast-1uezib"
        results = [_FakeResult("get-forecast", long_id)]
        output = _render_search_table(results, width=60)

        assert long_id in output, (
            f"Expected full identifier '{long_id}' in narrow output, but it was missing.\n"
            f"Output:\n{output}"
        )

    def test_multiple_results_all_identifiers_in_list(self):
        """All identifiers in a multi-result table must appear in the copyable list."""
        ids = [
            "browse-sh/weather.gov/get-forecast-1uezib",
            "browse-sh/airbnb.com/search-listings-abc123",
            "official/hello-world",
        ]
        results = [_FakeResult(f"skill-{i}", id_) for i, id_ in enumerate(ids)]
        output = _render_search_table(results, width=90)

        for id_ in ids:
            assert id_ in output, (
                f"Expected identifier '{id_}' in output but it was missing.\n"
                f"Output:\n{output}"
            )

    def test_copyable_list_header_present(self):
        """The copyable list should have a helpful header."""
        results = [_FakeResult("test", "official/test-skill")]
        output = _render_search_table(results, width=80)

        assert "Full identifiers" in output, (
            f"Expected 'Full identifiers' header in output.\nOutput:\n{output}"
        )

    def test_table_still_rendered(self):
        """The table itself should still be rendered above the identifier list."""
        results = [_FakeResult("test", "official/test-skill")]
        output = _render_search_table(results, width=80)

        # Table header should be present
        assert "Identifier" in output
        assert "Skills Hub" in output
