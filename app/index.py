from app import app, db

if __name__ == '__main__':
    with app.app_context():
        db.create_all()   # Tạo tất cả bảng trong database
    app.run(debug=True)
