import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


@pytest.fixture
def api(tmp_path):
    path = tmp_path / 'parking.db'
    with TestClient(create_app(path)) as client:
        yield client, path


def send(client, event_type='SPACE_OCCUPIED', space_id='P01'):
    return client.post('/webhook/parking-event', json={
        'space_id': space_id, 'event_type': event_type, 'vehicle_id': 'CAR_104',
    })


def test_seed_and_restart(api):
    client, path = api
    spaces = client.get('/parking-spaces').json()
    assert [s['space_id'] for s in spaces] == [f'P{i:02}' for i in range(1, 21)]
    assert all(s['status'] == 'available' and s['vehicle_id'] is None for s in spaces)
    assert client.get('/events').json() == []
    send(client)
    with TestClient(create_app(path)) as restarted:
        assert len(restarted.get('/parking-spaces').json()) == 20
        assert restarted.get('/parking-spaces').json()[0]['status'] == 'occupied'
        assert len(restarted.get('/events').json()) == 1


def test_valid_arrival(api):
    client, _ = api
    response = send(client)
    assert response.status_code == 201
    event = response.json()
    assert event['event_id'] == 1 and event['timestamp']
    space = client.get('/parking-spaces').json()[0]
    assert space['status'] == 'occupied' and space['vehicle_id'] == 'CAR_104'
    assert space['last_updated'] == event['timestamp']
    assert client.get('/events').json() == [event]


def test_valid_departure(api):
    client, _ = api
    send(client)
    assert send(client, 'SPACE_AVAILABLE').status_code == 201
    space = client.get('/parking-spaces').json()[0]
    assert space['status'] == 'available' and space['vehicle_id'] is None
    events = client.get('/events?limit=1').json()
    assert len(events) == 1 and events[0]['event_type'] == 'SPACE_AVAILABLE'


@pytest.mark.parametrize('prior_events,event_type', [
    (('SPACE_OCCUPIED',), 'SPACE_OCCUPIED'),
    (('SPACE_OCCUPIED', 'SPACE_AVAILABLE'), 'SPACE_AVAILABLE'),
    ((), 'SPACE_AVAILABLE'),
])
def test_invalid_transition(api, prior_events, event_type):
    client, _ = api
    for prior_event in prior_events:
        assert send(client, prior_event).status_code == 201
    before = client.get('/parking-spaces').json()
    events = client.get('/events').json()
    assert send(client, event_type).status_code == 409
    assert client.get('/parking-spaces').json() == before
    assert client.get('/events').json() == events


def test_unknown_space(api):
    client, _ = api
    assert send(client, space_id='P99').status_code == 404
    assert client.get('/events').json() == []


@pytest.mark.parametrize('payload', [
    {}, {'space_id': 'P01', 'event_type': 'UNKNOWN', 'vehicle_id': 'CAR_1'},
    {'space_id': 'P01', 'event_type': 'SPACE_OCCUPIED'},
    {'space_id': 'P01', 'event_type': 'SPACE_OCCUPIED', 'vehicle_id': ''},
    {'space_id': 'P01', 'event_type': 'SPACE_OCCUPIED', 'vehicle_id': '  '},
    {'space_id': 1, 'event_type': 'SPACE_OCCUPIED', 'vehicle_id': 'CAR_1'},
])
def test_bad_payload(api, payload):
    client, _ = api
    assert client.post('/webhook/parking-event', json=payload).status_code == 422
    assert client.get('/events').json() == []


def test_transaction_rollback(api):
    client, path = api
    before = client.get('/parking-spaces').json()
    with sqlite3.connect(path) as connection:
        connection.execute('''CREATE TRIGGER fail_event BEFORE INSERT ON parking_events
                              BEGIN SELECT RAISE(ABORT, 'forced failure'); END''')
    with TestClient(create_app(path), raise_server_exceptions=False) as failing:
        assert send(failing).status_code == 500
    assert client.get('/parking-spaces').json() == before
    assert client.get('/events').json() == []


def test_concurrent_arrivals(api):
    client, _ = api
    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = list(pool.map(lambda _: send(client).status_code, range(2)))
    assert sorted(codes) == [201, 409]
    assert len(client.get('/events').json()) == 1


def test_limits_and_cors(api):
    client, _ = api
    for limit in ['0', '-1', '1001', 'nope']:
        assert client.get('/events', params={'limit': limit}).status_code == 422
    response = client.options('/webhook/parking-event', headers={
        'Origin': 'http://localhost:5173', 'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'content-type',
    })
    assert response.headers['access-control-allow-origin'] == 'http://localhost:5173'


def test_simulation_controls(api) -> None:
    client, _ = api
    before = client.get('/parking-spaces').json()
    assert client.get('/simulation/status').json() == {'running': False}
    for action, running in [
        ('stop', False), ('start', True), ('start', True), ('stop', False),
    ]:
        response = client.post(f'/simulation/{action}')
        assert response.status_code == 200
        assert response.json() == {'running': running}
        assert client.get('/simulation/status').json() == {'running': running}
    assert client.get('/parking-spaces').json() == before
    assert client.get('/events').json() == []


def test_manual_simulation_records_arrival_and_departure(api) -> None:
    client, _ = api
    assert client.post('/simulation/departure').status_code == 409

    arrival_response = client.post('/simulation/arrival')
    assert arrival_response.status_code == 201
    arrival = arrival_response.json()
    departure_response = client.post('/simulation/departure')
    assert departure_response.status_code == 201
    departure = departure_response.json()

    assert arrival['event_type'] == 'SPACE_OCCUPIED'
    assert departure['event_type'] == 'SPACE_AVAILABLE'
    assert arrival['space_id'] == departure['space_id']
    assert arrival['vehicle_id'] == departure['vehicle_id']
    assert client.get('/events?limit=2').json() == [departure, arrival]


def test_simulation_speed(api) -> None:
    client, _ = api
    assert client.get('/simulation/speed').json() == {'speed': 1.0}
    assert client.post('/simulation/speed', json={'speed': 1.5}).json() == {'speed': 1.5}
    assert client.post('/simulation/speed', json={'speed': 3}).status_code == 422
    assert client.get('/simulation/speed').json() == {'speed': 1.5}


def test_analytics_reconstructs_occupancy_from_recorded_events(api) -> None:
    client, _ = api
    assert client.get('/analytics').json()['points'] == []
    for event_type, space_id in [
        ('SPACE_OCCUPIED', 'P01'), ('SPACE_OCCUPIED', 'P02'), ('SPACE_AVAILABLE', 'P01'),
    ]:
        assert send(client, event_type, space_id).status_code == 201

    response = client.get('/analytics')
    assert response.status_code == 200
    summary = response.json()
    assert summary['capacity'] == 20
    assert [point['occupied'] for point in summary['points']] == [1, 2, 1]
    assert summary['total_arrivals'] == 2
    assert summary['total_departures'] == 1
    assert sum(hour['arrivals'] for hour in summary['hourly']) == 2
    assert sum(hour['departures'] for hour in summary['hourly']) == 1
    assert summary['spaces'][:3] == [
        {'space_id': 'P01', 'arrivals': 1},
        {'space_id': 'P02', 'arrivals': 1},
        {'space_id': 'P03', 'arrivals': 0},
    ]


def test_live_api_works_without_trained_forecast(tmp_path) -> None:
    app = create_app(tmp_path / 'parking.db', forecast_artifact_dir=tmp_path / 'empty')
    with TestClient(app) as client:
        for path in ['/forecast/facilities', '/forecast']:
            assert client.get(path).status_code == 503
        assert len(client.get('/parking-spaces').json()) == 20
