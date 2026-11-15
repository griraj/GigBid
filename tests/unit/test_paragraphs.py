import pytest

from agent.paragraphs import regenerate_paragraph


EVIDENCE = [{'id': 'e1', 'title': 'Forecasting dashboard', 'text': 'Forecasting dashboard',
             'skills': ['python'], 'outcome': 'won'}]


def test_regeneration_only_replaces_selected_paragraph():
    response = regenerate_paragraph('Intro.\n\nOld second paragraph.', 1, EVIDENCE)
    assert response['text'].startswith('Intro.\n\n')
    assert response['suggestion'] == 'I delivered forecasting dashboard [e1].'
    assert response['requires_approval'] is True


def test_regeneration_rejects_unsupported_or_unavailable_evidence():
    with pytest.raises(ValueError, match='out of range'):
        regenerate_paragraph('A.', 1, EVIDENCE)
    with pytest.raises(ValueError, match='unverified'):
        regenerate_paragraph('A.', 0, [{**EVIDENCE[0], 'outcome': 'unverified'}])
    with pytest.raises(ValueError, match='No verified'):
        regenerate_paragraph('A.', 0, [])
