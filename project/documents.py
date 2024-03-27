from app import db, Mapped, mapped_column
from datetime import datetime


class Document(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    creation_date: Mapped[int] = mapped_column()
    creator_id: Mapped[int] = mapped_column()
    is_published: Mapped[str] = mapped_column(default=False)
    title: Mapped[str] = mapped_column(unique=True)
    abstract: Mapped[str] = mapped_column(nullable=True)
    body: Mapped[str] = mapped_column()
    # history: Mapped[str] = mapped_column(nullable=True) # TODO: History

    def getDateText(self):
        return str(datetime.fromtimestamp(self.creation_date))
