from pathlib import Path
from typing import Any, Generator

import pytest
from mock_aws_lambda_context import MockLambdaContext
from mock_aws_test_events import APIGatewayTestEvent


@pytest.fixture()
def events_list_in_path(
    monkeypatch: pytest.MonkeyPatch, path_apis: Path
) -> Generator[Path, Any, None]:
    """setup a monkeypatch for sys.path to start with events_list"""
    events_list_path = path_apis / "events_list"
    with monkeypatch.context() as mp:
        mp.syspath_prepend(str(events_list_path))
        yield events_list_path


def test_get_events_list(
    events_list_in_path,
) -> None:
    import lambda_handler

    test_event = APIGatewayTestEvent()

    resp = lambda_handler.handler(test_event.event(), MockLambdaContext())

    assert resp["statusCode"] == 200
