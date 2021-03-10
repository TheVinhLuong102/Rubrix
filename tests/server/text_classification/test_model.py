from pydantic import ValidationError
from rubric.server.commons.models import TaskStatus
from rubric.server.text_classification.model import (
    PredictionStatus,
    TextClassificationAnnotation,
    TextClassificationRecord,
)


def test_flatten_inputs():
    data = {
        "inputs": {
            "mail": {"subject": "The mail subject", "body": "This is a large text body"}
        }
    }
    record = TextClassificationRecord.parse_obj(data)
    assert list(record.text.keys()) == ["mail.subject", "mail.body"]


def test_flatten_metadata():
    data = {
        "inputs": {"text": "bogh"},
        "metadata": {
            "mail": {"subject": "The mail subject", "body": "This is a large text body"}
        },
    }
    record = TextClassificationRecord.parse_obj(data)
    assert list(record.metadata.keys()) == ["mail.subject", "mail.body"]


def test_confidence_integrity():
    data = {
        "multi_label": False,
        "inputs": {"data": "My cool data"},
        "prediction": {
            "agent": "test",
            "labels": [
                {"class": "A", "confidence": 0.3},
                {"class": "B", "confidence": 0.9},
            ],
        },
    }

    try:
        TextClassificationRecord.parse_obj(data)
    except ValidationError as e:
        assert "Wrong confidence distributions" in e.json()

    data["multi_label"] = True
    record = TextClassificationRecord.parse_obj(data)
    assert record is not None

    data["multi_label"] = False
    data["prediction"]["labels"] = [
        {"class": "B", "confidence": 0.9},
    ]
    record = TextClassificationRecord.parse_obj(data)
    assert record is not None

    data["prediction"]["labels"] = [
        {"class": "B", "confidence": 0.10000000012},
        {"class": "B", "confidence": 0.90000000002},
    ]
    record = TextClassificationRecord.parse_obj(data)
    assert record is not None


def test_prediction_ok_cases():

    data = {
        "multi_label": True,
        "inputs": {"data": "My cool data"},
        "prediction": {
            "agent": "test",
            "labels": [
                {"class": "A", "confidence": 0.3},
                {"class": "B", "confidence": 0.9},
            ],
        },
    }

    record = TextClassificationRecord(**data)
    assert record.predicted is None
    record.annotation = TextClassificationAnnotation(
        **{
            "agent": "test",
            "labels": [
                {"class": "A", "confidence": 1},
                {"class": "B", "confidence": 1},
            ],
        },
    )
    assert record.predicted == PredictionStatus.KO

    record.prediction = TextClassificationAnnotation(
        **{
            "agent": "test",
            "labels": [
                {"class": "A", "confidence": 0.9},
                {"class": "B", "confidence": 0.9},
            ],
        },
    )
    assert record.predicted == PredictionStatus.OK

    record.prediction = None
    assert record.predicted is None


def test_created_record_with_default_status():
    data = {
        "inputs": {"data": "My cool data"},
    }

    record = TextClassificationRecord.parse_obj(data)
    assert record.status == TaskStatus.default