"""Application constants."""

SENSITIVE_AUDIT_FIELDS = frozenset(
    {
        "phone",
        "email",
        "address",
        "emergency_contact",
        "notes",
        "personal_notes",
    }
)

DEFAULT_OPERATOR = "curator"
