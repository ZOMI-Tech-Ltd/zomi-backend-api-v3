from extensions import db


class User(db.Model):
    __tablename__ = 'users'
    _id = db.Column(db.String(50), primary_key = True)
    username  = db.Column(db.String(50),nullable = False)

    taste = db.relationship("Taste", back_populates = 'user_relation', lazy = True)
    collection =  db.relationship("Collection", back_populates = 'user_relation', lazy = True)

    user_likes = db.relationship("Like", back_populates = 'user_relation', lazy = True)
    

    def __repr__(self):
        return f'User {self.username}'