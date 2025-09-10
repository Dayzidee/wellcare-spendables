from app import app, db, socketio, Customer, Account, ACCOUNT_TYPES
from werkzeug.security import generate_password_hash
import os

def setup_database():
    with app.app_context():
        print("Creating all database tables...")
        db.create_all()
        print("Tables created.")

        # Seed the admin user
        if not Customer.query.filter_by(username='admin').first():
            print("Creating admin user...")
            admin_user = Customer(
                username='admin',
                password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
                is_admin=True,
                account_tier='premier'
            )
            db.session.add(admin_user)
            db.session.commit()

            # Create accounts for the admin
            for acc_type in ACCOUNT_TYPES:
                initial_balance = 50000.0 if acc_type == "Checking" else 250000.0
                account = Account(account_type=acc_type, balance=initial_balance, owner=admin_user)
                db.session.add(account)

            db.session.commit()
            print("Admin user and accounts created.")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    setup_database()
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Server with Socket.IO starting on http://127.0.0.1:{port}")
    socketio.run(app, host='0.0.0.0', port=port)
