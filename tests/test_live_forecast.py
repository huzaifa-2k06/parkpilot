from datetime import datetime, timedelta, timezone
import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from backend.database import Database
from backend.main import create_app
from backend.schemas import ParkingEventRequest
from ml.live_forecast import select_horizons, scores


def test_policy_selection_is_independent_of_test_outcomes() -> None:
    """A held-out failure must be reported without tuning the selected policy."""
    actual = [20, 10, 8]
    baseline = scores(actual, [18, 8, 6], 20)
    candidate = scores(actual, [20, 10, 8], 20)
    short = {5: {'validation': {'persistence': baseline, 'regression': candidate}}}
    calendar = {'same_day': {'validation': {
        'persistence': baseline, 'calendar': candidate, 'regression': baseline,
    }}}
    selected = select_horizons(short, calendar)
    assert selected == ([5], ['same_day'], [])
    # Deliberately reverse the rankings in the test set.
    short[5]['test'] = {'persistence': candidate, 'regression': baseline}
    calendar['same_day']['test'] = {
        'persistence': candidate, 'calendar': baseline, 'regression': candidate,
    }
    assert select_horizons(short, calendar) == selected


def test_missing_full_lot_validation_examples_prevent_promotion() -> None:
    baseline = scores([10, 8], [8, 6], 20)
    candidate = scores([10, 8], [10, 8], 20)
    assert candidate.mae < baseline.mae
    assert select_horizons(
        {5: {'validation': {'persistence': baseline, 'regression': candidate}}}, {},
    ) == ([], [], [])


def test_live_forecast_tracks_events_in_an_existing_database(tmp_path: Path) -> None:
    database = tmp_path / 'parking.db'
    app = create_app(database, live_forecast_path=tmp_path / 'missing.json')
    with TestClient(app) as client:
        facility = client.get('/live-forecast/facilities').json()[0]
        assert facility['id'] == 'parkpilot-demo'
        assert facility['max_horizon_minutes'] == 30
        arrival = datetime.now(timezone.utc) + timedelta(minutes=15)
        url = '/live-forecast/parkpilot-demo'
        params = {'arrival_at': arrival.isoformat()}
        before = client.get(url, params=params).json()
        assert before['estimated_free'] == 20
        assert before['model'] == 'Persistence'
        assert before['explanation']['inputs'][0]['value'] == '0 of 20'
        assert before['explanation']['raw_occupied'] == 0
        assert client.post('/simulation/arrival').status_code == 201
        forecast = client.get(url, params=params).json()
        assert forecast['estimated_occupied'] == 1
        assert forecast['estimated_free'] == 19
        assert datetime.fromisoformat(forecast['observed_at']) <= arrival

        assert client.get('/live-forecast/wrong', params=params).status_code == 404
        assert client.get(url, params={'arrival_at': '2026-11-17T12:00:00'}).status_code == 422
        assert client.get(url, params={
            'arrival_at': (arrival + timedelta(days=1)).isoformat(),
        }).status_code == 422
        assert client.get(url, params={
            'arrival_at': (arrival - timedelta(days=1)).isoformat(),
        }).status_code == 422

    with TestClient(app) as client:
        assert client.get(url, params=params).json()['estimated_free'] == 19


def test_enabled_worker_with_old_observations_returns_a_stale_error(tmp_path: Path) -> None:
    database = tmp_path / 'parking.db'
    app = create_app(database, live_forecast_path=tmp_path / 'missing.json')
    with TestClient(app) as client:
        assert client.post('/simulation/start').status_code == 200
        old = datetime.now(timezone.utc) - timedelta(minutes=2)
        app.state.simulation_started_at = old
        with sqlite3.connect(database) as connection:
            connection.execute('UPDATE parking_spaces SET last_updated = ?', (old.isoformat(),))
        params = {'arrival_at': (old + timedelta(minutes=10)).isoformat()}
        assert client.get('/live-forecast/parkpilot-demo', params=params).status_code == 503
        assert client.post('/simulation/stop').status_code == 200
        assert client.get('/live-forecast/parkpilot-demo', params=params).status_code == 200


def test_snapshots_rewind_events_at_five_minute_boundaries(tmp_path: Path) -> None:
    database = Database(tmp_path / 'parking.db')
    database.initialize()
    for bay in ('P01', 'P02'):
        database.record_event(ParkingEventRequest(
            space_id=bay, event_type='SPACE_OCCUPIED', vehicle_id=bay,
        ))
    seven_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=7)
    with database.connection() as connection:
        connection.execute("UPDATE parking_events SET timestamp = ? WHERE space_id = 'P01'",
                           (seven_minutes_ago.isoformat(),))
    history = database.occupancy_history(timedelta(minutes=5), 3)
    assert history.snapshots == [2, 1, 0, 0]
    assert (history.arrivals, history.departures) == (2, 0)


def test_calendar_uses_only_approved_horizons_and_labels_its_source(tmp_path: Path) -> None:
    policy_path = tmp_path / 'calendar.json'
    policy_path.write_text(json.dumps({'policy': {
        'version': 1, 'capacity': 20, 'short_weights': [0] * 8, 'short_intercept': 0,
        'learned_short_minutes': [], 'calendar_profile': [12] * 168,
        'calendar_weights': [0] * 5, 'calendar_intercept': 0,
        'calendar_bands': ['same_day'], 'learned_calendar_bands': [],
    }}), encoding='utf-8')
    app = create_app(tmp_path / 'parking.db', live_forecast_path=policy_path)
    with TestClient(app) as client:
        assert client.get('/live-forecast/facilities').json()[0]['max_horizon_minutes'] == 1440
        url = '/live-forecast/parkpilot-demo'
        now = datetime.now(timezone.utc)
        response = client.get(url, params={'arrival_at': (now + timedelta(hours=8)).isoformat()})
        assert response.status_code == 200
        forecast = response.json()
        assert forecast['source'] == 'simulated_calendar'
        assert forecast['current_occupied'] == 0
        assert forecast['estimated_free'] == 8
        assert forecast['explanation']['inputs'][-1]['value'] == '12 occupied'
        assert client.get(url, params={
            'arrival_at': (now + timedelta(days=2)).isoformat(),
        }).status_code == 422
