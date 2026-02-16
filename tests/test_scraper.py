"""Tests for website scraper module."""

from unittest.mock import Mock, patch

import pytest

from tpc_reporter.scraper import (
    ScrapeResult,
    Session,
    Speaker,
    _csv_escape,
    _detect_session_type,
    _parse_speaker_description,
    fetch_page,
    parse_sessions_page,
    parse_speakers_page,
    scrape_sessions,
    scrape_site,
    scrape_speakers,
    sessions_to_csv,
    speakers_to_csv,
)

# Sample HTML for testing
SAMPLE_SPEAKERS_HTML = """
<html>
<body>
<div class="elementor-image-box-wrapper">
    <div class="elementor-image-box-img">
        <img src="https://example.com/speaker1.jpg" />
    </div>
    <div class="elementor-image-box-content">
        <h3 class="elementor-image-box-title">Jane Doe</h3>
        <p class="elementor-image-box-description">Director, AI Research Institute</p>
    </div>
</div>
<div class="elementor-image-box-wrapper">
    <div class="elementor-image-box-content">
        <h3 class="elementor-image-box-title">John Smith</h3>
        <p class="elementor-image-box-description">Professor | University of Science</p>
    </div>
</div>
<div class="elementor-image-box-wrapper">
    <div class="elementor-image-box-content">
        <h3 class="elementor-image-box-title">Alice Johnson</h3>
    </div>
</div>
</body>
</html>
"""

SAMPLE_SESSIONS_HTML = """
<html>
<body>
<h2 class="elementor-heading-title">Sessions</h2>
<h2 class="elementor-heading-title">Plenary Sessions</h2>
<h2 class="elementor-heading-title">Opening Plenary: AI and HPC</h2>
<h4 class="elementor-heading-title">Tuesday, July 29, 14:00</h4>
<h2 class="elementor-heading-title">Breakout Groups</h2>
<h3 class="elementor-heading-title">BOF: Data Science Applications</h3>
<h3 class="elementor-heading-title">Workshop on Machine Learning</h3>
<h2 class="elementor-heading-title">Tutorials</h2>
<h3 class="elementor-heading-title">Tutorial: Getting Started with LLMs</h3>
<h2 class="elementor-heading-title">Countdown to Conference</h2>
</body>
</html>
"""


class TestSpeakerDataclass:
    """Tests for Speaker dataclass."""

    def test_speaker_creation(self):
        """Create a speaker with all fields."""
        speaker = Speaker(
            name="Jane Doe",
            title="Director",
            institution="AI Institute",
            bio="Full bio text",
            image_url="https://example.com/image.jpg",
        )
        assert speaker.name == "Jane Doe"
        assert speaker.title == "Director"
        assert speaker.institution == "AI Institute"

    def test_speaker_defaults(self):
        """Speaker has sensible defaults."""
        speaker = Speaker(name="Test")
        assert speaker.title == ""
        assert speaker.institution == ""
        assert speaker.bio == ""
        assert speaker.image_url == ""


class TestSessionDataclass:
    """Tests for Session dataclass."""

    def test_session_creation(self):
        """Create a session with all fields."""
        session = Session(
            title="Opening Session",
            session_type="plenary",
            datetime="Monday 9:00",
            description="Welcome address",
            speakers=["Speaker 1", "Speaker 2"],
            track="Main",
        )
        assert session.title == "Opening Session"
        assert session.session_type == "plenary"
        assert len(session.speakers) == 2

    def test_session_defaults(self):
        """Session has sensible defaults."""
        session = Session(title="Test")
        assert session.session_type == ""
        assert session.speakers == []


class TestParseDescription:
    """Tests for _parse_speaker_description function."""

    def test_pipe_delimiter(self):
        """Parse description with pipe delimiter."""
        title, inst = _parse_speaker_description("Director | Research Institute")
        assert title == "Director"
        assert inst == "Research Institute"

    def test_comma_delimiter(self):
        """Parse description with comma delimiter."""
        title, inst = _parse_speaker_description("Professor, University of Science")
        assert title == "Professor"
        assert inst == "University of Science"

    def test_dash_delimiter(self):
        """Parse description with dash delimiter."""
        title, inst = _parse_speaker_description("CEO - Tech Company")
        assert title == "CEO"
        assert inst == "Tech Company"

    def test_no_delimiter(self):
        """Parse description without delimiter."""
        title, inst = _parse_speaker_description("Senior Researcher")
        assert title == "Senior Researcher"
        assert inst == ""

    def test_empty_description(self):
        """Handle empty description."""
        title, inst = _parse_speaker_description("")
        assert title == ""
        assert inst == ""


class TestDetectSessionType:
    """Tests for _detect_session_type function."""

    def test_plenary_in_title(self):
        """Detect plenary from title."""
        assert _detect_session_type("Opening Plenary Session", "") == "plenary"

    def test_plenary_in_section(self):
        """Detect plenary from section."""
        assert _detect_session_type("Some Session", "Plenary Sessions") == "plenary"

    def test_breakout(self):
        """Detect breakout session."""
        assert _detect_session_type("BOF: Topic Discussion", "") == "breakout"

    def test_tutorial(self):
        """Detect tutorial session."""
        assert _detect_session_type("Tutorial: Getting Started", "") == "tutorial"

    def test_hackathon(self):
        """Detect hackathon session."""
        assert _detect_session_type("AI Hackathon", "") == "hackathon"

    def test_panel(self):
        """Detect panel session."""
        assert _detect_session_type("Panel Discussion", "") == "panel"

    def test_break(self):
        """Detect lunch/break."""
        assert _detect_session_type("Lunch and Networking", "") == "break"

    def test_default(self):
        """Default to session type."""
        assert _detect_session_type("Some Topic", "") == "session"


class TestParseSpeakersPage:
    """Tests for parse_speakers_page function."""

    def test_parse_speakers(self):
        """Parse speakers from HTML."""
        speakers = parse_speakers_page(SAMPLE_SPEAKERS_HTML)
        assert len(speakers) == 3

        # First speaker
        assert speakers[0].name == "Jane Doe"
        assert speakers[0].title == "Director"
        assert speakers[0].institution == "AI Research Institute"
        assert speakers[0].image_url == "https://example.com/speaker1.jpg"

        # Second speaker with pipe delimiter
        assert speakers[1].name == "John Smith"
        assert speakers[1].title == "Professor"
        assert speakers[1].institution == "University of Science"

        # Third speaker without description
        assert speakers[2].name == "Alice Johnson"
        assert speakers[2].title == ""

    def test_parse_empty_html(self):
        """Handle empty HTML."""
        speakers = parse_speakers_page("<html><body></body></html>")
        assert speakers == []

    def test_deduplicates_speakers(self):
        """Duplicate speakers are removed."""
        html = """
        <html><body>
        <div class="elementor-image-box-wrapper">
            <h3 class="elementor-image-box-title">Same Person</h3>
        </div>
        <div class="elementor-image-box-wrapper">
            <h3 class="elementor-image-box-title">Same Person</h3>
        </div>
        </body></html>
        """
        speakers = parse_speakers_page(html)
        assert len(speakers) == 1


class TestParseSessionsPage:
    """Tests for parse_sessions_page function."""

    def test_parse_sessions(self):
        """Parse sessions from HTML."""
        sessions = parse_sessions_page(SAMPLE_SESSIONS_HTML)

        # Should have actual sessions, not section headers
        session_titles = [s.title for s in sessions]
        assert "Opening Plenary: AI and HPC" in session_titles
        assert "BOF: Data Science Applications" in session_titles
        assert "Workshop on Machine Learning" in session_titles
        assert "Tutorial: Getting Started with LLMs" in session_titles

        # Section headers should be filtered
        assert "Sessions" not in session_titles
        assert "Plenary Sessions" not in session_titles
        assert "Breakout Groups" not in session_titles

        # Countdown should be filtered
        assert "Countdown to Conference" not in session_titles

    def test_session_types_detected(self):
        """Session types are correctly detected."""
        sessions = parse_sessions_page(SAMPLE_SESSIONS_HTML)

        plenary = [s for s in sessions if s.session_type == "plenary"]
        assert len(plenary) >= 1

        breakout = [s for s in sessions if s.session_type == "breakout"]
        assert len(breakout) >= 1

        tutorial = [s for s in sessions if s.session_type == "tutorial"]
        assert len(tutorial) >= 1

    def test_parse_empty_html(self):
        """Handle empty HTML."""
        sessions = parse_sessions_page("<html><body></body></html>")
        assert sessions == []


class TestFetchPage:
    """Tests for fetch_page function."""

    @patch("tpc_reporter.scraper.requests.get")
    def test_successful_fetch(self, mock_get):
        """Successfully fetch a page."""
        mock_response = Mock()
        mock_response.text = "<html>content</html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        result = fetch_page("https://example.com")
        assert result == "<html>content</html>"

    @patch("tpc_reporter.scraper.requests.get")
    def test_fetch_failure(self, mock_get):
        """Handle fetch failure."""
        import requests

        mock_get.side_effect = requests.RequestException("Connection error")

        result = fetch_page("https://example.com")
        assert result is None


class TestScrapeFunctions:
    """Tests for scrape_speakers and scrape_sessions functions."""

    @patch("tpc_reporter.scraper.fetch_page")
    def test_scrape_speakers(self, mock_fetch):
        """Scrape speakers from URL."""
        mock_fetch.return_value = SAMPLE_SPEAKERS_HTML

        speakers = scrape_speakers("https://example.com")
        assert len(speakers) == 3
        mock_fetch.assert_called_once()

    @patch("tpc_reporter.scraper.fetch_page")
    def test_scrape_speakers_fetch_failure(self, mock_fetch):
        """Handle fetch failure when scraping speakers."""
        mock_fetch.return_value = None

        speakers = scrape_speakers("https://example.com")
        assert speakers == []

    @patch("tpc_reporter.scraper.fetch_page")
    def test_scrape_sessions(self, mock_fetch):
        """Scrape sessions from URL."""
        mock_fetch.return_value = SAMPLE_SESSIONS_HTML

        sessions = scrape_sessions("https://example.com")
        assert len(sessions) > 0
        mock_fetch.assert_called_once()


class TestScrapeSite:
    """Tests for scrape_site function."""

    @patch("tpc_reporter.scraper.time.sleep")
    @patch("tpc_reporter.scraper.scrape_sessions")
    @patch("tpc_reporter.scraper.scrape_speakers")
    def test_scrape_site(self, mock_speakers, mock_sessions, mock_sleep):
        """Scrape entire site."""
        mock_speakers.return_value = [Speaker(name="Test")]
        mock_sessions.return_value = [Session(title="Test Session")]

        result = scrape_site("https://example.com")

        assert len(result.speakers) == 1
        assert len(result.sessions) == 1
        assert result.base_url == "https://example.com"
        assert len(result.errors) == 0

    @patch("tpc_reporter.scraper.time.sleep")
    @patch("tpc_reporter.scraper.scrape_sessions")
    @patch("tpc_reporter.scraper.scrape_speakers")
    def test_scrape_site_with_errors(self, mock_speakers, mock_sessions, mock_sleep):
        """Collect errors when scraping fails."""
        mock_speakers.side_effect = Exception("Speaker error")
        mock_sessions.side_effect = Exception("Session error")

        result = scrape_site("https://example.com")

        assert len(result.errors) == 2


class TestCsvFunctions:
    """Tests for CSV conversion functions."""

    def test_speakers_to_csv(self):
        """Convert speakers to CSV."""
        speakers = [
            Speaker(
                name="Jane Doe",
                title="Director",
                institution="AI Institute",
                image_url="https://example.com/img.jpg",
            ),
            Speaker(name="John Smith", title="Professor", institution="University"),
        ]

        csv = speakers_to_csv(speakers)
        lines = csv.split("\n")

        assert lines[0] == "Name,Title,Institution,Image URL"
        assert "Jane Doe" in lines[1]
        assert "John Smith" in lines[2]

    def test_sessions_to_csv(self):
        """Convert sessions to CSV."""
        sessions = [
            Session(
                title="Opening Session",
                session_type="plenary",
                datetime="Monday 9:00",
                track="Main",
            ),
        ]

        csv = sessions_to_csv(sessions)
        lines = csv.split("\n")

        assert lines[0] == "Title,Type,DateTime,Track,Description"
        assert "Opening Session" in lines[1]
        assert "plenary" in lines[1]

    def test_csv_escape(self):
        """Escape special characters in CSV."""
        assert _csv_escape("simple") == "simple"
        assert _csv_escape("with, comma") == '"with, comma"'
        assert _csv_escape('with "quotes"') == '"with ""quotes"""'
        assert _csv_escape("with\nnewline") == '"with\nnewline"'
        assert _csv_escape("") == ""
