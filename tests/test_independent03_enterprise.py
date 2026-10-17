"""Independent UTC precision and invalid-offset checks on timestamp validation."""
from datetime import datetime,timedelta,timezone
import pytest
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)


def test_independent_microsecond_grid_survives_forecast_dates():
    start=datetime(2026,1,1,tzinfo=timezone.utc)
    data={'values':list(range(10)),'holdout':3,'horizon':2,'timestamps':[(start+timedelta(microseconds=i)).isoformat() for i in range(10)]}
    response=client.post('/analyze',json=data)
    assert response.status_code==200
    result=response.json()
    assert result['timestamp_interval_seconds']==1e-6
    assert result['future_timestamps']==['2026-01-01T00:00:00.000010Z','2026-01-01T00:00:00.000011Z']
    assert result['holdout_prediction']==[7,8,9]


@pytest.mark.parametrize('offset',['+00:60','+01:99','-02:75'])
def test_independent_invalid_offset_minutes_not_silently_normalized(offset):
    timestamps=[f'2026-01-{day:02d}T00:00:00{offset}' for day in range(1,11)]
    response=client.post('/analyze',json={'values':list(range(10)),'holdout':3,'horizon':2,'timestamps':timestamps})
    assert response.status_code==422, 'Invalid ISO offset minutes were silently normalized to a different offset'
