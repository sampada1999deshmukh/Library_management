from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class Users(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100),nullable=False)
    email_id = db.Column(db.String(150),unique=True,nullable=False)
    password = db.Column(db.String(150),nullable=False)
    role = db.Column(db.String(100),nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Books(db.Model):
    book_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    isbn = db.Column(db.String(100), unique=True, nullable=False)
    total_copies = db.Column(db.Integer, nullable=False, default=1)
    available_copies = db.Column(db.Integer, nullable=False, default=1)


class BorrowRequest(db.Model):
    request_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), nullable=False)
    start_date = db.Column(db.BigInteger, nullable=False)
    end_date = db.Column(db.BigInteger, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Pending')

    user = db.relationship('Users', backref='borrow_requests')
    book = db.relationship('Books', backref='borrow_requests')

class BorrowHistory(db.Model):
    history_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), nullable=False)
    start_date = db.Column(db.BigInteger, nullable=False)
    end_date = db.Column(db.BigInteger, nullable=False)
    returned_date = db.Column(db.BigInteger, nullable=True)

    user = db.relationship('Users', backref='borrow_history')
    book = db.relationship('Books', backref='borrow_history')


