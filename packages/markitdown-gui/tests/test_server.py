import io
from fastapi.testclient import TestClient
from markitdown_gui.server import app

client = TestClient(app)


def test_get_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "MarkItDown" in response.text


def test_supported_formats():
    response = client.get("/api/supported-formats")
    assert response.status_code == 200
    data = response.json()
    assert ".pdf" in data["formats"]
    assert "PdfConverter" in data["converters"]


def test_convert_text_file():
    file_content = b"Hello MarkItDown Web GUI!"
    response = client.post(
        "/api/convert",
        files={"file": ("test.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "Hello MarkItDown Web GUI!" in data["markdown"]
    assert data["filename"] == "test.txt"


def test_convert_batch():
    file1 = ("doc1.txt", io.BytesIO(b"Doc 1 content"), "text/plain")
    file2 = ("doc2.txt", io.BytesIO(b"Doc 2 content"), "text/plain")

    response = client.post(
        "/api/convert-batch",
        files=[("files", file1), ("files", file2)],
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total_files"] == 2
    assert len(data["results"]) == 2
    assert "Doc 1 content" in data["results"][0]["markdown"]
    assert "Doc 2 content" in data["results"][1]["markdown"]
