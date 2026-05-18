#!/usr/bin/env python3
"""
NET-08: Tests del predictor y feature extractor
"""
import sys
import os
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestFailurePredictor:

    def test_predict_returns_dict(self):
        from ml.inference.predictor import FailurePredictor
        predictor = FailurePredictor()
        window = np.random.rand(60, 4)
        result = predictor.predict(window)
        assert isinstance(result, dict)

    def test_predict_has_required_keys(self):
        from ml.inference.predictor import FailurePredictor
        predictor = FailurePredictor()
        window = np.random.rand(60, 4)
        result = predictor.predict(window)
        assert 'probability'  in result
        assert 'alert'        in result
        assert 'risk_level'   in result

    def test_probability_range(self):
        from ml.inference.predictor import FailurePredictor
        predictor = FailurePredictor()
        window = np.random.rand(60, 4)
        result = predictor.predict(window)
        assert 0.0 <= result['probability'] <= 1.0

    def test_risk_level_values(self):
        from ml.inference.predictor import FailurePredictor
        predictor = FailurePredictor()
        window = np.random.rand(60, 4)
        result = predictor.predict(window)
        assert result['risk_level'] in ['NORMAL', 'WARNING', 'CRITICAL', 'unknown']

    def test_alert_is_bool(self):
        from ml.inference.predictor import FailurePredictor
        predictor = FailurePredictor()
        window = np.random.rand(60, 4)
        result = predictor.predict(window)
        assert isinstance(result['alert'], bool)


class TestFeatureExtractor:

    def test_generate_demo_features_shape(self):
        from pipeline.features.feature_extractor import generate_demo_features
        features = generate_demo_features(n_nodes=10, n_steps=120)
        assert features.shape[0] == 10
        assert features.shape[1] == 120
        assert features.shape[2] == 4

    def test_build_lstm_windows_shape(self):
        from pipeline.features.feature_extractor import generate_demo_features, build_lstm_windows
        features = generate_demo_features(n_nodes=5, n_steps=120)
        X = build_lstm_windows(features)
        assert X.ndim == 3
        assert X.shape[1] == 60
        assert X.shape[2] == 4

    def test_empty_features_returns_empty(self):
        from pipeline.features.feature_extractor import build_lstm_windows
        import pandas as pd
        X = build_lstm_windows(np.array([]))
        assert len(X) == 0


class TestAnomalyDetector:

    def test_normal_traffic_no_anomaly(self):
        from pipeline.anomaly.anomaly_detector import AnomalyDetector
        detector = AnomalyDetector()
        for _ in range(80):
            result = detector.detect('d1', 'utilization', 0.3)
        assert result.severity == 'NORMAL'

    def test_spike_detected_as_anomaly(self):
        from pipeline.anomaly.anomaly_detector import AnomalyDetector
        detector = AnomalyDetector()
        for _ in range(80):
            detector.detect('d1', 'utilization', 0.3)
        result = detector.detect('d1', 'utilization', 0.99)
        assert result.is_anomaly == True

    def test_summary_structure(self):
        from pipeline.anomaly.anomaly_detector import AnomalyDetector
        detector = AnomalyDetector()
        window = np.random.rand(60, 4)
        results = detector.scan_window('c1', window)
        summary = detector.summary(results)
        assert 'total_checked'     in summary
        assert 'anomalies'         in summary
        assert 'critical'          in summary
        assert 'max_z_score'       in summary
        assert 'affected_metrics'  in summary
