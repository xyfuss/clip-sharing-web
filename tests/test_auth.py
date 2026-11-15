import bcrypt
from app import User, db 

def make_user(username='testuser', password='testpass'):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    db.session.add(User(username=username, password=hashed.decode('utf-8')))
    db.session.commit()

def test_login(client):
    make_user()
    response = client.post('/login', data={'username': 'testuser', 'password': 'testpass'})
    assert response.status_code == 302
    assert client.get('/').status_code == 200

def test_invalid_user_and_password(client):
    make_user()
    response = client.post('/login', data={'username': 'wronguser', 'password': 'wrongpass'}, follow_redirects=True)
    assert b'Invalid username or password' in response.data

def test_valid_user_invalid_password(client):
    make_user()
    response = client.post('/login', data={'username': 'testuser', 'password': 'wrongpass'}, follow_redirects=True)
    assert b'Invalid username or password' in response.data

def test_login_invalid_password_length(client):
    make_user()
    long_password = 'a' * 73
    response = client.post('/login', data={'username': 'testuser', 'password': long_password})
    assert b'Invalid username or password' in response.data

def test_successful_registration(client):
    response = client.post('/register', data={'username': 'testuser', 'password': 'testpass'})
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/login')

    user = User.query.filter_by(username='testuser').first()
    assert user is not None
    assert user.password != 'testpass'

def test_invalid_password_length(client):
    long_password = 'a' * 73
    response = client.post('/register', data={'username': 'testuser', 'password': long_password})
    assert b'Password is too long (max 72 bytes).' in response.data

def test_invalid_username_length(client):
    short_username = 'ab'
    long_username = 'a' * 31
    response_short = client.post('/register', data={'username': short_username, 'password': 'testpass'})
    response_long = client.post('/register', data={'username': long_username, 'password': 'testpass'})
    assert b'Username must be between 3 and 30 characters.' in response_short.data
    assert b'Username must be between 3 and 30 characters.' in response_long.data

