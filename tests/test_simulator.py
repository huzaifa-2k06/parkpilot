import json

import httpx
import pytest

from simulator import simulator


@pytest.mark.parametrize(
    ('mode', 'spaces', 'expected_type', 'expected_vehicle'),
    [
        ('arrival', [{'space_id': 'P01', 'status': 'available', 'vehicle_id': None}],
         'SPACE_OCCUPIED', None),
        ('departure', [{'space_id': 'P01', 'status': 'occupied', 'vehicle_id': 'CAR_104'}],
         'SPACE_AVAILABLE', 'CAR_104'),
        ('auto', [{'space_id': 'P01', 'status': 'occupied', 'vehicle_id': 'CAR_104'}],
         'SPACE_AVAILABLE', 'CAR_104'),
    ],
)
def test_selects_event_for_eligible_space(
    mode: str,
    spaces: list[simulator.Space],
    expected_type: str,
    expected_vehicle: str | None,
) -> None:
    event = simulator.choose_event(spaces, mode)
    assert event is not None
    assert event['space_id'] == 'P01'
    assert event['event_type'] == expected_type
    if expected_vehicle is None:
        assert event['vehicle_id'].startswith('CAR_')
    else:
        assert event['vehicle_id'] == expected_vehicle


def test_manual_departure_requires_an_occupied_space() -> None:
    assert simulator.choose_event(
        [{'space_id': 'P01', 'status': 'available', 'vehicle_id': None}], 'departure',
    ) is None


def test_automatic_mode_honors_start_and_stop(monkeypatch: pytest.MonkeyPatch) -> None:
    states = iter([False, True, True, True, False])
    events: list[simulator.Event] = []
    delays: list[float] = []

    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == '/simulation/status':
            return httpx.Response(200, json={'running': next(states)})
        if request.url.path == '/simulation/speed':
            return httpx.Response(200, json={'speed': 2.0})
        if request.url.path == '/parking-spaces':
            return httpx.Response(200, json=[
                {'space_id': 'P01', 'status': 'available', 'vehicle_id': None},
            ])
        assert request.method == 'POST' and request.url.path == '/webhook/parking-event'
        events.append(json.loads(request.content))
        return httpx.Response(201)

    def sleep(delay: float) -> None:
        delays.append(delay)
        if len(delays) == 3:
            raise KeyboardInterrupt

    monkeypatch.setattr(simulator, 'sleep', sleep)
    with httpx.Client(base_url='http://test', transport=httpx.MockTransport(respond)) as client:
        with pytest.raises(KeyboardInterrupt):
            simulator.run_automatic(client)

    assert len(events) == 1
    assert events[0]['event_type'] == 'SPACE_OCCUPIED'
    assert 1 <= delays[1] <= 2.5
