from tests.factories import seed_basic


def test_global_search(container):
    _, s1, _, _ = seed_basic(container)
    container.notes.create({"title": "Important note", "body": "Follow up with parents"})
    result = container.search.search({"query": s1.last_name})
    assert any(h.entity_id == s1.id for h in result.students)

    notes = container.search.search({"query": "parents"})
    assert notes.notes
