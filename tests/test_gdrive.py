"""Tests for Google Drive collector module."""

from unittest.mock import Mock, patch

from tpc_reporter.gdrive import (
    DOC_EXPORT_URL,
    SHEET_EXPORT_URL,
    DriveFile,
    collect_all_data,
    collect_track_data,
    detect_file_type,
    download_doc,
    download_file,
    download_sheet,
    extract_file_id,
)


class TestExtractFileId:
    """Tests for extract_file_id function."""

    def test_spreadsheet_url(self):
        """Extract ID from Google Sheets URL."""
        url = "https://docs.google.com/spreadsheets/d/1ABC123xyz_-/edit#gid=0"
        assert extract_file_id(url) == "1ABC123xyz_-"

    def test_document_url(self):
        """Extract ID from Google Docs URL."""
        url = "https://docs.google.com/document/d/1DEF456abc/edit"
        assert extract_file_id(url) == "1DEF456abc"

    def test_drive_file_url(self):
        """Extract ID from Google Drive file URL."""
        url = "https://drive.google.com/file/d/1GHI789def/view"
        assert extract_file_id(url) == "1GHI789def"

    def test_open_id_format(self):
        """Extract ID from ?id= format URL."""
        url = "https://drive.google.com/open?id=1JKL012ghi"
        assert extract_file_id(url) == "1JKL012ghi"

    def test_invalid_url(self):
        """Return None for invalid URLs."""
        assert extract_file_id("https://example.com/not-a-drive-url") is None
        assert extract_file_id("just-a-string") is None

    def test_complex_url_with_params(self):
        """Extract ID from URL with multiple parameters."""
        url = "https://docs.google.com/spreadsheets/d/1ABC123/edit?usp=sharing&ouid=123"
        assert extract_file_id(url) == "1ABC123"


class TestDetectFileType:
    """Tests for detect_file_type function."""

    def test_spreadsheet(self):
        """Detect spreadsheet type."""
        url = "https://docs.google.com/spreadsheets/d/1ABC/edit"
        assert detect_file_type(url) == "sheet"

    def test_document(self):
        """Detect document type."""
        url = "https://docs.google.com/document/d/1ABC/edit"
        assert detect_file_type(url) == "doc"

    def test_generic_file(self):
        """Detect generic file type."""
        url = "https://drive.google.com/file/d/1ABC/view"
        assert detect_file_type(url) == "file"


class TestDriveFile:
    """Tests for DriveFile dataclass."""

    def test_sheet_export_url(self):
        """Get export URL for sheet."""
        f = DriveFile(
            file_id="1ABC",
            name="test.csv",
            file_type="sheet",
            url="https://docs.google.com/spreadsheets/d/1ABC/edit",
        )
        assert f.export_url == SHEET_EXPORT_URL.format(file_id="1ABC")

    def test_doc_export_url(self):
        """Get export URL for doc."""
        f = DriveFile(
            file_id="1DEF",
            name="test.txt",
            file_type="doc",
            url="https://docs.google.com/document/d/1DEF/edit",
        )
        assert f.export_url == DOC_EXPORT_URL.format(file_id="1DEF")


class TestDownloadFile:
    """Tests for download_file function."""

    @patch("tpc_reporter.gdrive.requests.get")
    def test_successful_download(self, mock_get, tmp_path):
        """Successfully download a file."""
        mock_response = Mock()
        mock_response.text = "col1,col2\nval1,val2"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        output_path = tmp_path / "test.csv"
        result = download_file("https://example.com/file", str(output_path))

        assert result is True
        assert output_path.exists()
        assert output_path.read_text() == "col1,col2\nval1,val2"

    @patch("tpc_reporter.gdrive.requests.get")
    def test_creates_parent_directories(self, mock_get, tmp_path):
        """Create parent directories if they don't exist."""
        mock_response = Mock()
        mock_response.text = "content"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        output_path = tmp_path / "nested" / "dir" / "test.csv"
        result = download_file("https://example.com/file", str(output_path))

        assert result is True
        assert output_path.exists()

    @patch("tpc_reporter.gdrive.requests.get")
    def test_handles_request_exception(self, mock_get, tmp_path):
        """Handle request exceptions gracefully."""
        import requests

        mock_get.side_effect = requests.RequestException("Connection error")

        output_path = tmp_path / "test.csv"
        result = download_file("https://example.com/file", str(output_path), retries=1)

        assert result is False
        assert not output_path.exists()

    @patch("tpc_reporter.gdrive.requests.get")
    def test_detects_not_found_page(self, mock_get, tmp_path):
        """Detect Google's not found error page."""
        mock_response = Mock()
        mock_response.text = "<!DOCTYPE html><html>File not found</html>"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        output_path = tmp_path / "test.csv"
        result = download_file("https://example.com/file", str(output_path))

        assert result is False

    @patch("tpc_reporter.gdrive.time.sleep")
    @patch("tpc_reporter.gdrive.requests.get")
    def test_retries_on_rate_limit(self, mock_get, mock_sleep, tmp_path):
        """Retry on rate limiting."""
        rate_limited = Mock()
        rate_limited.text = "Too many requests. Please try again later."
        rate_limited.raise_for_status = Mock()

        success = Mock()
        success.text = "actual content"
        success.raise_for_status = Mock()

        mock_get.side_effect = [rate_limited, success]

        output_path = tmp_path / "test.csv"
        result = download_file("https://example.com/file", str(output_path))

        assert result is True
        assert mock_sleep.called


class TestDownloadSheet:
    """Tests for download_sheet function."""

    @patch("tpc_reporter.gdrive.download_file")
    def test_with_url(self, mock_download, tmp_path):
        """Download sheet from URL."""
        mock_download.return_value = True

        url = "https://docs.google.com/spreadsheets/d/1ABC123/edit"
        output_path = tmp_path / "sheet.csv"
        result = download_sheet(url, str(output_path))

        assert result is True
        called_url = mock_download.call_args[0][0]
        assert "1ABC123" in called_url
        assert "export?format=csv" in called_url

    @patch("tpc_reporter.gdrive.download_file")
    def test_with_file_id(self, mock_download, tmp_path):
        """Download sheet from file ID directly."""
        mock_download.return_value = True

        output_path = tmp_path / "sheet.csv"
        result = download_sheet("1ABC123", str(output_path))

        assert result is True
        called_url = mock_download.call_args[0][0]
        assert "1ABC123" in called_url

    @patch("tpc_reporter.gdrive.download_file")
    def test_with_sheet_gid(self, mock_download, tmp_path):
        """Download specific sheet by GID."""
        mock_download.return_value = True

        output_path = tmp_path / "sheet.csv"
        result = download_sheet("1ABC123", str(output_path), sheet_gid="12345")

        assert result is True
        called_url = mock_download.call_args[0][0]
        assert "gid=12345" in called_url

    @patch("tpc_reporter.gdrive.download_file")
    def test_invalid_url(self, mock_download, tmp_path):
        """Handle invalid URL."""
        output_path = tmp_path / "sheet.csv"
        result = download_sheet("https://invalid-url.com", str(output_path))

        assert result is False
        mock_download.assert_not_called()


class TestDownloadDoc:
    """Tests for download_doc function."""

    @patch("tpc_reporter.gdrive.download_file")
    def test_with_url(self, mock_download, tmp_path):
        """Download doc from URL."""
        mock_download.return_value = True

        url = "https://docs.google.com/document/d/1DEF456/edit"
        output_path = tmp_path / "doc.txt"
        result = download_doc(url, str(output_path))

        assert result is True
        called_url = mock_download.call_args[0][0]
        assert "1DEF456" in called_url
        assert "export?format=txt" in called_url

    @patch("tpc_reporter.gdrive.download_file")
    def test_with_file_id(self, mock_download, tmp_path):
        """Download doc from file ID directly."""
        mock_download.return_value = True

        output_path = tmp_path / "doc.txt"
        result = download_doc("1DEF456", str(output_path))

        assert result is True


class TestCollectTrackData:
    """Tests for collect_track_data function."""

    @patch("tpc_reporter.gdrive.download_doc")
    @patch("tpc_reporter.gdrive.download_sheet")
    def test_collect_both_files(self, mock_sheet, mock_doc, tmp_path):
        """Collect both attendees and notes."""
        mock_sheet.return_value = True
        mock_doc.return_value = True

        result = collect_track_data(
            track_id="Track-1",
            attendees_url="https://sheets.example.com/attendees",
            notes_url="https://docs.example.com/notes",
            output_dir=str(tmp_path),
        )

        assert result["track_id"] == "Track-1"
        assert result["attendees_path"] is not None
        assert result["notes_path"] is not None
        assert len(result["errors"]) == 0

    @patch("tpc_reporter.gdrive.download_doc")
    @patch("tpc_reporter.gdrive.download_sheet")
    def test_collect_attendees_only(self, mock_sheet, mock_doc, tmp_path):
        """Collect only attendees when no notes URL."""
        mock_sheet.return_value = True

        result = collect_track_data(
            track_id="Track-2",
            attendees_url="https://sheets.example.com/attendees",
            notes_url=None,
            output_dir=str(tmp_path),
        )

        assert result["attendees_path"] is not None
        assert result["notes_path"] is None
        mock_doc.assert_not_called()

    @patch("tpc_reporter.gdrive.download_doc")
    @patch("tpc_reporter.gdrive.download_sheet")
    def test_records_errors(self, mock_sheet, mock_doc, tmp_path):
        """Record errors when downloads fail."""
        mock_sheet.return_value = False
        mock_doc.return_value = False

        result = collect_track_data(
            track_id="Track-3",
            attendees_url="https://sheets.example.com/attendees",
            notes_url="https://docs.example.com/notes",
            output_dir=str(tmp_path),
        )

        assert result["attendees_path"] is None
        assert result["notes_path"] is None
        assert len(result["errors"]) == 2


class TestCollectAllData:
    """Tests for collect_all_data function."""

    @patch("tpc_reporter.gdrive.collect_track_data")
    @patch("tpc_reporter.gdrive.download_sheet")
    def test_collect_all_tracks(self, mock_sheet, mock_track, tmp_path):
        """Collect data for multiple tracks."""
        mock_sheet.return_value = True
        mock_track.return_value = {
            "track_id": "Track-1",
            "attendees_path": "/path/to/attendees.csv",
            "notes_path": "/path/to/notes.txt",
            "errors": [],
        }

        track_configs = {
            "Track-1": {
                "attendees_url": "https://example.com/attendees1",
                "notes_url": "https://example.com/notes1",
            },
            "Track-2": {
                "attendees_url": "https://example.com/attendees2",
                "notes_url": "https://example.com/notes2",
            },
        }

        result = collect_all_data(
            lightning_talks_url="https://example.com/talks",
            track_configs=track_configs,
            output_dir=str(tmp_path),
        )

        assert result["lightning_talks_path"] is not None
        assert len(result["tracks"]) == 2
        assert len(result["errors"]) == 0

    @patch("tpc_reporter.gdrive.collect_track_data")
    @patch("tpc_reporter.gdrive.download_sheet")
    def test_aggregates_errors(self, mock_sheet, mock_track, tmp_path):
        """Aggregate errors from all tracks."""
        mock_sheet.return_value = False  # Lightning talks fails
        mock_track.return_value = {
            "track_id": "Track-1",
            "attendees_path": None,
            "notes_path": None,
            "errors": ["Error 1", "Error 2"],
        }

        result = collect_all_data(
            lightning_talks_url="https://example.com/talks",
            track_configs={"Track-1": {}},
            output_dir=str(tmp_path),
        )

        # 1 error from lightning talks + 2 from track
        assert len(result["errors"]) == 3
