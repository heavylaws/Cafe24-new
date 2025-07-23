from app import create_app
from app.models import User
from flask_jwt_extended import create_access_token
app=create_app()
with app.app_context():
    u = User.query.filter_by(username='manager').first()
    if u is None:
        raise SystemExit("No user with username 'manager' found. Run `flask --app run.py seed-db` first or create a user before generating a token.")

    print('id', u.id)
    token = create_access_token(identity=str(u.id))
    print('token', token)
