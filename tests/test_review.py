import numpy as np
from app.main import Request, analyze

def test_reviewer_chronological_prediction_no_holdout_leakage():
    prefix=list(range(10)); a=analyze(Request(values=prefix+[10,11,12],holdout=3,horizon=2))
    b=analyze(Request(values=prefix+[100,200,300],holdout=3,horizon=2))
    assert a['holdout_prediction']==b['holdout_prediction']==[10,11,12]
    assert a['training_residual_scale']==b['training_residual_scale']
    assert a['mae']==0 and np.isclose(b['mae'],189)
    assert len(b['anomalies'])==3

def test_reviewer_seasonal_cycle_phase():
    r=analyze(Request(values=[1,2,3]*5,holdout=3,horizon=5,method='seasonal',season_length=3))
    assert r['holdout_prediction']==[1,2,3] and r['future_forecast']==[1,2,3,1,2]
    assert r['mae']==0 and r['anomalies']==[]

def test_reviewer_constant_and_single_holdout():
    r=analyze(Request(values=[7]*10,holdout=1,method='naive'))
    assert r['mae']==0 and r['rmse']==0 and r['anomalies']==[]
