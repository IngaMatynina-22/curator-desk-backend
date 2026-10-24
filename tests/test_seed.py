from app.database.seed import DEMO_PASSWORD, DEMO_USERNAME, is_seeded, seed_full


def test_full_seed(container):
    assert is_seeded(container.session) is False
    result = seed_full(container.session)
    assert result["skipped"] is False
    assert result["students"] == 6
    assert is_seeded(container.session) is True

    again = seed_full(container.session)
    assert again["skipped"] is True

    login = container.auth.login({"username": DEMO_USERNAME, "password": DEMO_PASSWORD})
    assert login.user.full_name
    assert container.groups.count() >= 1
    assert container.students.list({}).total == 6
    assert container.academic.list_subjects()
    assert container.assignments.list({}).total >= 1
    assert container.events.list({}).total >= 1
