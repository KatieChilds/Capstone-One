"""Models for Fridge Raiders app (CAPSTONE ONE)."""

from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import requests
import os

bcrypt = Bcrypt()
db = SQLAlchemy()
API_KEY = os.environ.get('API_KEY')


class User(db.Model):
    """User model for app."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, unique=True, nullable=False)
    first_name = db.Column(db.Text, nullable=False)
    last_name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    image_url = db.Column(db.Text, nullable=False,
                          default="/static/no-image.png")
    password = db.Column(db.Text, nullable=False)
    hash = db.Column(db.Text, nullable=False)
    api_username = db.Column(db.Text, nullable=False)

    recipes = db.relationship("Recipe", backref="user")
    preferences = db.relationship("Preference", backref="user")

    def __repr__(self):
        """Define representation for User instance."""
        return f"<User id:{self.id} username:{self.username}>"

    @classmethod
    def signup(cls, username, first_name, last_name, email, image_url, password):
        """Signup user, hashes password and adds user to system."""
        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')
        res = requests.post("https://api.spoonacular.com/users/connect", params={'apiKey': API_KEY}, json={
            "username": username, "firstName": first_name, "lastName": last_name, "email": email})
        data = res.json()
        hash = data['hash']
        api_username = data['username']
        if image_url is None or image_url == '':
            image_url = cls.image_url.default.arg
        user = User(username=username, first_name=first_name, last_name=last_name,
                    email=email, image_url=image_url, password=hashed_pwd, hash=hash, api_username=api_username)

        db.session.add(user)

        return user

    @classmethod
    def authenticate(cls, username, password):
        """Authenticate user for given username and password, else returns False."""

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False


class Recipe(db.Model):
    """Recipe model for app for storing user saved and favorited recipes."""

    __tablename__ = "recipes"

    user_id = db.Column(db.Integer, db.ForeignKey(
        "users.id", ondelete="cascade"))
    recipe_id = db.Column(db.Integer, nullable=False, primary_key=True)
    favourite = db.Column(db.Boolean, default=False)

    def __repr__(self):
        """Define representation for Recipe instance."""
        return f"<Recipe user_id:{self.user_id} recipe_id:{self.recipe_id} favourite:{self.favourite}>"


class Preference(db.Model):
    """Preference model for app for storing user preferences."""

    __tablename__ = "preferences"

    user_id = db.Column(db.Integer, db.ForeignKey(
        "users.id", ondelete="cascade"), primary_key=True)
    preferences = db.Column(db.JSON)

    def __repr__(self):
        """Define representation for Preference instance."""
        return f"<Preferences for {self.user_id}>"


def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)
