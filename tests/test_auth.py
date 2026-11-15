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