from flask import render_template, request, redirect, url_for, flash,send_file
from . import bp
from .service import *
import csv
from io import BytesIO,StringIO

@bp.route('/')
def home_view():
    return redirect(url_for('Library.signin_view'))


@bp.route('/register', methods=['GET', 'POST'])
def register_view():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        if register_user(username, email, password, role):
            flash('User registered successfully!', 'success')
            return redirect(url_for('Library.signin_view'))
        else:
            flash('An error occurred. Please try again.', 'danger')
    return render_template('register.html', message='An error occurred. Please try again.', category='danger')


@bp.route('/signin', methods=['GET', 'POST'])
def signin_view():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_authenticated = sign_in_user(email, password)
        if user_authenticated == 'admin':
            return render_template('admin.html')
        elif user_authenticated == 'user':
            return render_template('users.html')
        else:
            return render_template('sign_in.html')
    return render_template('sign_in.html')


@bp.route('/add_book', methods=['GET', 'POST'])
def add_book_view():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in first.', 'warning')
        return redirect(url_for('Library.signin_view'))
    user = Users.query.get(user_id)
    if not user:
        flash('Invalid user session. Please log in again.', 'danger')
        return redirect(url_for('Library.signin_view'))
    if user.role != 'admin':
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('Library.signin_view'))
    if request.method == 'POST':
        name = request.form.get('name')
        author = request.form.get('author')
        isbn = request.form.get('isbn')
        total_copies = int(request.form.get('total_copies'))
        if add_book(name, author, isbn, total_copies):
            flash('Book added successfully!', 'success')
            return render_template('add_book.html')
        else:
            flash('Failed to add book. Please check the details and try again.', 'danger')

    return render_template('add_book.html')


@bp.route('/available_books', methods=['GET'])
def show_books():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in first.', 'warning')
        return redirect(url_for('Library.signin_view'))
    all_books = get_all_books()
    available_books = [book for book in all_books if book['available_copies'] > 0]
    user = Users.query.filter_by(user_id=user_id).first()
    if user and user.role == "user":
        return render_template('book_list.html', books=available_books)
    else:
        return redirect(url_for('Library.signin_view'))


@bp.route('/book_request',methods=['POST'])
def book_request():
    data = request.args.get('book')
    data = data.replace("'",'"')
    book = json.loads(data)
    return render_template('book_request.html',book=book)

@bp.route('/submit_book_request', methods=["POST"])
def submit_book_request():
    user_id = session.get("user_id")
    if not user_id:
        return "Error: User not Found in.", 401
    book_id = request.form.get("book_id")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    if not book_id or not start_date or not end_date:
        return "Error: All fields are required.", 400
    result = add_book_request(user_id, book_id, start_date, end_date)
    return result


@bp.route('/admin/book_requests')
def admin_book_requests():
    user_id = session.get('user_id')
    if not user_id:
        return "Error: User not Found in.", 401
    user = Users.query.filter_by(user_id=user_id).first()
    if user.role != "admin":
        return "Error: Unauthorized access.", 403
    requests = fetch_pending_book_requests()
    return render_template('admin_book_requests.html', requests=requests)


@bp.route('/admin/approve_request', methods=['POST'])
def approve_request():
    data = request.args.get('request')
    data = data.replace("'", '"')
    book = json.loads(data)
    result = approve_book_request(data=book)
    if result == "This book request has already been approved.":
        return "Error: This book request has already been approved.", 400
    elif result == "Book not found.":
        return "Error: Book not found.", 404
    elif result == "No copies of the book are currently available.":
        return "Error: No copies of the book are currently available.", 400
    elif result == "The book request has been approved successfully.":
        return result
    elif result == "Overlapping borrow dates detected.":
        return "Error: Overlapping borrow dates detected.", 400
    else:
        return "An unknown error occurred.", 500



@bp.route('/admin/borrow_history', methods=['GET'])
def borrow_history():
    user_id = session.get('user_id')
    if not user_id:
        return "Error: User not Found in.", 401
    user = Users.query.filter_by(user_id=user_id).first()
    if user.role != "admin":
        return "Error: Unauthorized access.", 403

    history_records = BorrowHistory.query.all()
    return render_template('borrow_history.html', history_records=history_records)


@bp.route('/book_history',methods=['GET'])
def book_history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    history = get_borrow_history(user_id)
    return render_template('book_history.html', history=history)


@bp.route('/download_borrow_history', methods=['GET'])
def download_borrow_history():
    user_id = session.get('user_id')
    history = get_borrow_history(user_id)
    if not history:
        return "No borrow history found."
    output = BytesIO()
    output_text = StringIO()
    writer = csv.writer(output_text, quoting=csv.QUOTE_MINIMAL)
    writer.writerow(['Book ID', 'Book Name', 'Borrow Date', 'Returned Date'])
    for entry, book_name in history:
        print(f"Borrow Date Type: {type(entry.start_date)}, Return Date Type: {type(entry.returned_date)}")
        borrow_date = entry.start_date.strftime('%Y-%m-%d') if hasattr(entry.start_date, 'strftime') else str(
            entry.start_date)

        return_date = (entry.return_date.strftime('%Y-%m-%d')
                       if entry.returned_date and hasattr(entry.returned_date, 'strftime')
                       else 'Not Returned')

        writer.writerow([entry.book_id, book_name, borrow_date, return_date])
    output_text.seek(0)
    output.write(output_text.getvalue().encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='borrow_history.csv')


@bp.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('Library.signin_view'))