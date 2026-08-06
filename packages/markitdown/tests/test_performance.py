import asyncio
import io
import time
from markitdown import MarkItDown


def test_convert_batch():
    md = MarkItDown()
    inputs = [
        "Hello World 1",
        "Hello World 2",
        "Hello World 3",
        "Hello World 4",
    ]
    # Convert as data URIs or plain text streams
    data_uris = [f"data:text/plain;charset=utf-8,{text}" for text in inputs]

    results = md.convert_batch(data_uris)
    assert len(results) == len(inputs)
    for i, res in enumerate(results):
        assert f"Hello World {i+1}" in res.text_content


def test_async_convert():
    md = MarkItDown()
    uri = "data:text/plain;charset=utf-8,Async%20Test"

    async def _run():
        res = await md.aconvert(uri)
        assert "Async Test" in res.text_content

    asyncio.run(_run())


def test_async_convert_batch():
    md = MarkItDown()
    inputs = [
        "Async Batch 1",
        "Async Batch 2",
        "Async Batch 3",
        "Async Batch 4",
    ]
    data_uris = [f"data:text/plain;charset=utf-8,{text}" for text in inputs]

    async def _run():
        results = await md.aconvert_batch(data_uris, concurrency=2)
        assert len(results) == len(inputs)
        for i, res in enumerate(results):
            assert f"Async Batch {i+1}" in res.text_content

    asyncio.run(_run())


def test_cached_converter_registration():
    md = MarkItDown()
    # Force initial cached sort
    md.convert("data:text/plain,test")
    assert md._sorted_converters is not None

    # Registering a new converter invalidates the cache
    from markitdown._base_converter import DocumentConverter, DocumentConverterResult

    class CustomTestConverter(DocumentConverter):
        def accepts(self, file_stream, stream_info=None, **kwargs):
            return False

        def convert(self, file_stream, stream_info=None, **kwargs):
            return DocumentConverterResult(text_content="custom")

    md.register_converter(CustomTestConverter())
    assert md._sorted_converters is None

    # Next convert re-populates the cache
    md.convert("data:text/plain,test")
    assert md._sorted_converters is not None
