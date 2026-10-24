from tests.factories import seed_basic


def test_statistics_overview(container):
    seed_basic(container)
    stats = container.statistics.overview()
    assert stats.students_total == 2
    assert stats.students_active == 2
