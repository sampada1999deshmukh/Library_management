from app import create_app,db

app = create_app()

if __name__ == "__main__":
    with app.app_context():
        from app.system.models import Users
        from app.system.models import Books
        from app.system.models import BorrowHistory
        from app.system.models import BorrowRequest

        db.create_all()
    app.run(host='0.0.0.0', port=8080, debug=True)
