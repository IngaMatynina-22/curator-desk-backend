from datetime import datetime, timedelta


def test_create_recurring_weekly_events(container):
    start = datetime.now().replace(microsecond=0) + timedelta(days=1)
    created = container.calendar.create_recurring_events(
        {
            "title": "Weekly stand-up",
            "starts_at": start,
            "ends_at": start + timedelta(hours=1),
        },
        {"freq": "weekly", "count": 3},
    )
    assert len(created) == 3
    group_ids = {container.events.get(e.id).id for e in created}
    assert len(group_ids) == 3
    # all share recurrence_group_id on ORM
    from app.models.event import Event

    entities = [container.session.get(Event, e.id) for e in created]
    assert entities[0].recurrence_group_id
    assert len({e.recurrence_group_id for e in entities}) == 1
