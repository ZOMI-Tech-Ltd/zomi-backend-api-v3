from extensions import db


class Media(db.Model):

    __tablename__ = 'media'

    _id = db.Column(db.String(100), primary_key=True)
    url = db.Column(db.String(200), nullable=False)

    height = db.Column(db.JSON, nullable=True)
    width = db.Column(db.JSON, nullable=True)

   

    def __repr__(self):
        return f"<Media(id={self.id}, url={self.url})>"
