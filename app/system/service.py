from .models import *
from flask import flash,session
from app import db
from datetime import datetime
import json

def register_user(username, email, password, role):
    try:
        if Users.query.filter_by(email_id=email).first():
            flash('User with this email already exists', 'error')
            return False
        new_user = Users(user_name=username, email_id=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash('User registered successfully', 'success')
        return True
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while registering the user: {e}', 'error')
        return False

def sign_in_user(email, password):
    try:
        user = Users.query.filter_by(email_id=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.user_id
            session['username'] = user.user_name
            session['role'] = user.role  # Store role in the session
            flash('Login successful!', 'success')
            return user.role  # Return the role (e.g., 'admin' or 'user')
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            return False
    except Exception as e:
        flash(f'An error occurred while signing in: {e}', 'error')
        return False

def add_book(name, author, isbn, total_copies):
    existing_book = Books.query.filter_by(isbn=isbn).first()
    if existing_book:
        return False
    try:
        new_book = Books(name=name, author=author, isbn=isbn, total_copies=total_copies, available_copies=total_copies)
        db.session.add(new_book)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error adding book: {e}")
        return False

def get_all_books():
    try:
        books = Books.query.all()
        return [
            {
                'id': book.book_id,
                'name': book.name,
                'author': book.author,
                'isbn': book.isbn,
                'available_copies': book.available_copies
            }
            for book in books
        ]
    except Exception as e:
        flash(f'An error occurred while retrieving books: {e}', 'error')
        return []



def process_borrow_request(user_id, book_data, start_date, end_date):
    try:
        book = json.loads(book_data)
    except json.JSONDecodeError:
        return "Error: Invalid book data format.", 400

    if not start_date or not end_date:
        return "Error: Start date and end date are required.", 400
    try:
        start_date_timestamp = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp())
        end_date_timestamp = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp())
    except ValueError:
        return "Error: Invalid date format. Use YYYY-MM-DD.", 400

    borrow_request = BorrowRequest(
        user_id=user_id,
        book_id=book.get("id"),
        start_date=start_date_timestamp,
        end_date=end_date_timestamp,
        status="Pending"
    )

    try:
        db.session.add(borrow_request)
        db.session.commit()
        return "Book borrow request submitted successfully!", 200
    except Exception as e:
        db.session.rollback()
        return f"Error: Unable to submit borrow request. {str(e)}", 500

def add_book_request(user_id, book_id, start_date, end_date):
    try:
        new_request = BorrowRequest(
            user_id=user_id,
            book_id=book_id,
            start_date=start_date,
            end_date=end_date,
            status="Pending"
        )

        db.session.add(new_request)
        db.session.commit()
        return "Book request submitted successfully.", 200
    except Exception as e:
        db.session.rollback()
        return f"Error: Could not submit book request. {str(e)}", 500
def fetch_pending_book_requests():
    try:
        requests = BorrowRequest.query.all()
        results = []
        for request in requests:
            book = Books.query.filter_by(book_id=request.book_id).first()
            results.append({
                "user_id": request.user_id,
                "book_id": request.book_id,
                "book_name": book.name if book else "Unknown",
                "book_available": book.available_copies if book else "N/A",
                "start_date": request.start_date,
                "end_date": request.end_date,
                "status": request.status
            })
        return results
    except Exception as e:
        flash(f'An error occurred while fetching pending book requests: {e}', 'error')
        return []


def approve_book_request(data):
    try:
        book_request = BorrowRequest.query.filter_by(user_id=data['user_id'], book_id=data['book_id']).first()
        if not book_request:
            return "Request not found."
        if book_request.status == "Approved":
            return "This book request has already been approved."
        book_data = Books.query.filter_by(book_id=data['book_id']).first()
        if not book_data:
            return "Book not found."
        if book_data.available_copies <= 0:
            return "No copies of the book are currently available."
        overlapping_request = BorrowRequest.query.filter(
            BorrowRequest.book_id == data['book_id'],
            BorrowRequest.start_date < data['end_date'],
            BorrowRequest.end_date > data['start_date'],
            BorrowRequest.status == "Approved"
        ).first()
        if overlapping_request:
            return "Overlapping borrow dates detected."

        book_data.available_copies -= 1
        db.session.commit()
        book_request.status = "Approved"
        db.session.commit()
        borrow_history = BorrowHistory(
            user_id=data['user_id'],
            book_id=data['book_id'],
            start_date=book_request.start_date,
            end_date=book_request.end_date,
            returned_date=None
        )
        db.session.add(borrow_history)
        db.session.commit()
        db.session.delete(book_request)
        db.session.commit()
        return "The book request has been approved successfully."
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while approving the book request: {e}', 'error')
        return "An error occurred while processing the request."


def get_borrow_history(user_id):
    try:
        history = db.session.query(
            BorrowHistory,
            Books.name.label('book_name')
        ).join(Books, BorrowHistory.book_id == Books.book_id).filter(BorrowHistory.user_id == user_id).all()
        return history
    except Exception as e:
        flash(f'An error occurred while retrieving borrow history: {e}', 'error')
        return []


