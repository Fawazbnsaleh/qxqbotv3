import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from al_rased.features.detection.engine import DetectionEngine

@pytest.fixture
def mock_joblib():
    with patch("al_rased.features.detection.engine.joblib") as mock:
        yield mock

@pytest.fixture
def mock_model():
    model = MagicMock()
    model.classes_ = ["Normal", "Spam", "Hate"]
    # Mocking predict_proba to return probabilities for [Normal, Spam, Hate]
    model.predict_proba.return_value = np.array([[0.1, 0.8, 0.1]]) 
    return model

def test_prediction_spam(mock_joblib, mock_model):
    """Test standard spam detection."""
    # Setup the mock to return our fake model
    mock_joblib.load.return_value = mock_model
    
    # Ensure model is not loaded initially
    DetectionEngine._model = None
    
    result = DetectionEngine.predict("This is a spam message")
    
    assert result["label"] == "Spam"
    assert result["confidence"] == 0.8
    mock_joblib.load.assert_called_once()

def test_prediction_normal(mock_joblib, mock_model):
    """Test normal message detection."""
    mock_joblib.load.return_value = mock_model
    mock_model.predict_proba.return_value = np.array([[0.9, 0.05, 0.05]])
    
    DetectionEngine._model = None
    result = DetectionEngine.predict("Hello world")
    
    assert result["label"] == "Normal"
    assert result["confidence"] == 0.9

def test_model_load_failure(mock_joblib):
    """Test behavior when model fails to load."""
    mock_joblib.load.side_effect = Exception("Model not found")
    
    DetectionEngine._model = None
    result = DetectionEngine.predict("Test")
    
    # Should fallback to safe default
    assert result["label"] == "Normal"
    assert result["confidence"] == 0.0
