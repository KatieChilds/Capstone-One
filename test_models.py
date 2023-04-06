"""Model tests for Fridge Raiders app (CAPSTONE ONE)."""

from app import app
import os
from unittest import TestCase
from sqlalchemy import exc
from models import db, User, Recipe, Preference

os.environ['DATABASE_URL'] = "postgresql:///fridge_raiders-test"
app.config['SQLALCHEMY_ECHO'] = False

app.config['TESTING'] = True

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

app.app_context().push()
db.create_all()


class ModelsTestCase(TestCase):
    """Test the models for the fridge raider app."""

    def setUp(self):
        """Create client and add sample data."""
        User.query.delete()
        Recipe.query.delete()
        Preference.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    first_name="test",
                                    last_name="user",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.testuser_id = 9999
        self.testuser.id = self.testuser_id

        db.session.commit()

    def tearDown(self):
        """Clean up any failed transaction."""
        db.session.rollback()

    def test_user_model(self):
        """Tests to see if the basic user model works."""
        u = User(username="test", first_name="tester", last_name="used",
                 email="tester@test.com", password="123456789", image_url=None, hash="123456789", api_username="api_test")

        db.session.add(u)
        db.session.commit()

        self.u = u
        self.u.id = u.id
        # user should have no recipes or preferences
        self.assertEqual(len(u.recipes), 0)
        self.assertEqual(len(u.preferences), 0)
        # does the repr method work?
        self.assertEqual(u.__repr__(), f"<User id:{self.u.id} username:test>")

    def test_valid_user_signup(self):
        """New User instance is created for valid credentials."""
        tester = User.signup(username="test1", first_name="testing",
                             last_name="tester", email="test1@test.com", password="password", image_url=None)
        uid = 1111
        tester.id = uid
        db.session.commit()

        tester = User.query.get(uid)

        self.assertIsNotNone(tester)
        self.assertEqual(tester.username, "test1")
        self.assertEqual(tester.first_name, "testing")
        self.assertEqual(tester.last_name, "tester")
        self.assertEqual(tester.email, "test1@test.com")
        self.assertNotEqual(tester.password, "password")
        self.assertTrue(tester.password.startswith("$2b$"))

    def test_invalid_username_signup(self):
        """Fails to create new instance of User if invalid username credentials."""
        invalid = User.signup(username=None, first_name="testtest",
                              last_name="testing", email="test2@test.com", password="password", image_url=None)
        uid = 12345
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_first_name_signup(self):
        """Fails to create new instance of User if invalid first_name credentials."""
        invalid = User.signup(username="testtest", first_name=None,
                              last_name="test", email="test2@test.com", password="password", image_url=None)
        uid = 123456
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_last_name_signup(self):
        """Failes to create a new instance of User if invalid last_name credentials."""
        invalid = User.signup(username="testingtest", first_name="testtest",
                              last_name=None, email="test3@test.com", password="password", image_url=None)
        uid = 1234567
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_signup(self):
        """Fails to create a new instance of User if invalid email credentials."""
        invalid = User.signup(username="test2", first_name="test",
                              last_name="tester",
                              email=None, password="password", image_url=None)
        uid = 12345678
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password_signup(self):
        """Fails to create a new instance of User if invalid password credentials."""
        with self.assertRaises(ValueError) as context:
            User.signup(username="test3", first_name="test",
                        last_name="testing",
                        email="test4@gmail.com", password=None, image_url=None)
        with self.assertRaises(ValueError) as context:
            User.signup(username="test3", first_name="test",
                        last_name="testing",
                        email="test4@gmail.com", password="", image_url=None)

    def test_valid_user_auth(self):
        """Authenticate class method returns user when valid credentials are used."""
        user = User.authenticate(username=self.testuser.username,
                                 password="testuser")
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.testuser.id)

    def test_invalid_username_auth(self):
        """Authenticate class method returns False when invalid username credentials are used."""
        self.assertFalse(User.authenticate(username="badusername",
                                           password="password"))

    def test_invalid_password_auth(self):
        """Authenticate class method returns False when invalid password credentials are used."""
        self.assertFalse(User.authenticate(
            username=self.testuser.username, password="badpassword"))

    def test_recipe_model(self):
        """Tests to see if basic recipe model works."""
        r = Recipe(user_id=self.testuser.id, recipe_id=12345, favourite=False)
        db.session.add(r)
        db.session.commit()

        self.r = r

        # checks if user_id is the same as testuser
        self.assertEqual(r.user_id, self.testuser.id)

        # does the repr method work?
        self.assertEqual(r.__repr__(
        ), f"<Recipe user_id:{self.r.user_id} recipe_id:12345 favourite:False>")

    def test_preference_model(self):
        """Tests to see if basic preference model works."""
        p = Preference(user_id=self.testuser.id, preferences=None)
        db.session.add(p)
        db.session.commit()

        self.p = p

        # checks if user_id is the same a testuser
        self.assertEqual(p.user_id, self.testuser.id)

        # does the repr method work?
        self.assertEqual(p.__repr__(), f"<Preferences for {self.p.user_id}>")
