from app.scraper import classify_resource
import pytest

def test_resource_classification():
    assert classify_resource("https://youtube.com/watch") == "video"
    assert classify_resource("lecture.pdf") == "slides"
    assert classify_resource("lab.ipynb") == "notebook"
    assert classify_resource("notes.html") == "document"

# Mock test for Discourse scraper
def test_discourse_scraper(requests_mock):
    from app.scraper import scrape_discourse
    mock_html = """
    <html><body>
    <tr class="topic-list-item">
        <td><a class="title" href="/t/1">Test Topic</a></td>
        <td><span class="discourse-tag">week1</span></td>
        <td><span class="relative-date" title="2025-01-01">1d</span></td>
    </tr>
    </body></html>
    """
    requests_mock.get("https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34?page=1", text=mock_html)
    
    results = scrape_discourse(max_pages=1)
    assert len(results) == 1
    assert results[0]["title"] == "Test Topic"
