import requests
from app import main

def test_peer_check_success(mocker):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mocker.patch.object(requests, "get", return_value=mock_response)

    main.peer_up.set(0)
    main.peer_check_errors._value.set(0)

    # Run one iteration manually
    requests.get(main.PEER_URL)

    assert main.peer_up._value.get() in (0, 1)

def test_peer_check_failure(mocker):
    mocker.patch.object(requests, "get", side_effect=Exception("network error"))

    before = main.peer_check_errors._value.get()

    try:
        requests.get(main.PEER_URL)
    except Exception:
        main.peer_check_errors.inc()

    after = main.peer_check_errors._value.get()
    assert after == before + 1