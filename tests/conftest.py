import os
import pytest

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret'
os.environ['SESSION_COOKIE_SECURE'] = 'false'
os.environ['R2_ENDPOINT_URL'] = 'https://example.invalid'
os.environ['R2_ACCESS_KEY_ID'] = 'test'
os.environ['R2_SECRET_ACCESS_KEY'] = 'test'
os.environ['R2_BUCKET_NAME'] = 'test-bucket'
os.environ['R2_PUBLIC_URL'] = 'https://cdn.example.invalid'
os.environ['REGISTRATION_ENABLED'] = 'true'

from app import app, db, limiter

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False   
    limiter.enabled = False                  
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app.test_client()