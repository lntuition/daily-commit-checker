import pytest
import responses

from src.request import Request


class TestRequest:
    @responses.activate
    def test_fetch_text_success(self) -> None:
        url = "http://github.com/mocking/success"
        key = "key"
        value = "value"
        responses.add(
            responses.GET,
            f"{url}?{key}={value}",
            body=b"text",
        )

        text = Request.fetch_text(url, {key: value})
        assert text == "text"

    @responses.activate
    def test_fetch_text_fail(self) -> None:
        url = "http://github.com/mocking/fail"
        responses.add(
            responses.GET,
            url,
            status=503,
        )

        with pytest.raises(Exception):
            Request.fetch_text(url)
