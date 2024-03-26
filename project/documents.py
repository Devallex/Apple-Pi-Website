from app import (
    db,
    Mapped,
    mapped_column,
)


class Document(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(unique=True)
    is_published: Mapped[str] = mapped_column(default=False)
    creator_id: Mapped[int] = mapped_column()
    abstract: Mapped[str] = mapped_column(nullable=True)
    body: Mapped[str] = mapped_column()
    # history: Mapped[str] = mapped_column(nullable=True) # TODO: History
