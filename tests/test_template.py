from pathlib import Path


def test_template_exposes_required_parameters() -> None:
    content = Path("template.yaml").read_text(encoding="utf-8")

    assert "Parameters:" in content
    assert "AlertThreshold:" in content
    assert "DefaultQuery:" in content
    assert "ScheduledCollectionFunction:" in content
