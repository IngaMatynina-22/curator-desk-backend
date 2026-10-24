from tests.factories import seed_basic


def test_export_students_csv(container):
    seed_basic(container)
    result = container.reports.export_students(fmt="csv")
    assert result.path.exists()
    assert result.rows == 2
    assert result.path.read_text(encoding="utf-8-sig").count("\n") >= 3


def test_export_summary_pdf(container):
    seed_basic(container)
    result = container.reports.export_summary(fmt="pdf")
    assert result.path.exists()
    assert result.path.stat().st_size > 0
