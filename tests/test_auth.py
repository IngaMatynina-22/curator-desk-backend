from app.core.exceptions import AuthError, ConflictError
from app.database.seed import DEMO_PASSWORD, DEMO_USERNAME


def test_register_login_logout(container):
    user = container.auth.register(
        {
            "username": "anna",
            "password": "secret12",
            "full_name": "Anna Curator",
            "email": "anna@example.com",
        }
    )
    assert user.username == "anna"

    session = container.auth.login({"username": "anna", "password": "secret12"})
    assert session.user.id == user.id
    assert container.auth.current_user().username == "anna"
    assert container.auth.require_user().id == user.id

    container.auth.logout()
    assert container.auth.current_user() is None


def test_login_invalid_password(container):
    container.auth.register(
        {"username": "bob", "password": "secret12", "full_name": "Bob"}
    )
    try:
        container.auth.login({"username": "bob", "password": "wrongpass"})
        assert False
    except AuthError:
        pass


def test_duplicate_username(container):
    container.auth.register(
        {"username": "dup", "password": "secret12", "full_name": "One"}
    )
    try:
        container.auth.register(
            {"username": "dup", "password": "secret12", "full_name": "Two"}
        )
        assert False
    except ConflictError:
        pass


def test_change_password(container):
    user = container.auth.register(
        {"username": "carl", "password": "oldpass1", "full_name": "Carl"}
    )
    container.auth.change_password(user.id, "oldpass1", "newpass1")
    container.auth.login({"username": "carl", "password": "newpass1"})
    assert container.auth.current_user().username == "carl"
