"""User view tests for Fridge Raiders app (CAPSTONE ONE)."""

from app import app, CURR_USER_KEY
import os
from unittest import TestCase
# from bs4 import BeautifulSoup
from models import db, connect_db, User, Recipe, Preference

os.environ['DATABASE_URL'] = "postgresql:///fridge_raiders-test"

app.config['SQLALCHEMY_ECHO'] = False

app.config['TESTING'] = True

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

app.app_context().push()
db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class UserViewsTestCase(TestCase):
    """Test views related to user for fridge raiders app."""

    def setUp(self):
        """Create test client and add sample data."""
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

        recipe1 = Recipe(user_id=self.testuser.id,
                         recipe_id=1095745, favourite=True)
        recipe2 = Recipe(user_id=self.testuser.id,
                         recipe_id=650484, favourite=False)
        db.session.add_all([recipe1, recipe2])
        db.session.commit()

    def tearDown(self):
        """Clean up any failed transaction."""
        db.session.rollback()

    def test_show_user_profile(self):
        """Shows a user profile page if given valid user id."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f"/user/{self.testuser.id}")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser's Profile", html)

    def test_show_user_profile_invalid(self):
        """Shows alert message if invalid user id given or if id does not match current user instead of profile page."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get('/user/99999999999999', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Unauthorized access.", str(resp.data))

    def test_update_user_profile(self):
        """Shows form to update user profile given valid id."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f"/user/{self.testuser.id}/update")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Update your details testuser", str(resp.data))

    def test_update_user_profile2(self):
        """Tests POST request for update to user profile with valid username given."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post(f"/user/{self.testuser.id}/update", data={'username': 'tester', 'first_name': 'testing',
                          'last_name': 'test', 'email': 'tester@test.com', 'image_url': None}, follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("tester's Profile", html)
            self.assertIn("testing", html)
            self.assertIn("tester@test.com", html)
            self.assertNotIn("testuser", html)
            self.assertNotIn("test@test.com", html)

    def test_update_user_profile3(self):
        """Tests POST request for update to user profile with invalid username given."""
        self.test3user = User.signup(username="test3user",
                                     first_name="test",
                                     last_name="user",
                                     email="test3@test.com",
                                     password="testuser",
                                     image_url=None)
        self.test3user_id = 8888
        self.test3user.id = self.test3user_id
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post(f"/user/{self.testuser.id}/update", data={'username': 'test3user', 'first_name': 'testing',
                          'last_name': 'test', 'email': 'tester@test.com', 'image_url': None}, follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Update your details testuser", html)
            self.assertIn("Username already taken.", html)

    def test_update_user_preferences(self):
        """Shows form to update user's preferences given valid id."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f"/user/{self.testuser.id}/preferences")

            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                "Update your saved preferences testuser", str(resp.data))

    def test_update_user_preferences2(self):
        """Tests POST request to update user's preferences."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            preferences = {'cuisine': ['italian'], 'diet': [], 'intolerances': [
            ], 'includeIngredients': '', 'excludeIngredients': '', 'maxReadyTime': 40, 'number': 5}
            resp = c.post(f"/user/{self.testuser.id}/preferences",
                          data=preferences, follow_redirects=True)

            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser's Profile", html)
            self.assertIn("italian", html)
            self.assertIn("40", html)
            self.assertIn("5", html)

            preferences = Preference.query.filter_by(
                user_id=self.testuser.id).all()
            self.assertIsNotNone(preferences)

    def test_get_user_shoppinglist(self):
        """Shows user's shoppinglist."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f"/user/{self.testuser.id}/shoppinglist")
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser's Shopping List", html)

    def test_get_user_shoppinglist_invalid(self):
        """Does not show shoppinglist if invalid user id given."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f"/user/12345/shoppinglist", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Unauthorized access", html)

    def test_add_to_shoppinglist(self):
        """Adds a given ingredient to user's shoppinglist."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get('/shoppinglist/add/cauliflower',
                         follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser's Shopping List", html)
            self.assertIn("cauliflower", html)

    def test_delete_from_shoppinglist(self):
        """Deletes a given ingredient from user's shoppinglist."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get('/shoppinglist/delete/11135',
                         follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser's Shopping List", html)
            self.assertNotIn("cauliflower", html)

    def test_get_user_saved_recipes(self):
        """Shows user's saved recipes."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f"/user/{self.testuser.id}/saved-recipes")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Mushroom", str(resp.data))
            self.assertIn("Paneer", str(resp.data))

            saved_recipes = Recipe.query.filter_by(
                user_id=self.testuser.id).all()
            self.assertEqual(len(saved_recipes), 2)

    def test_get_user_saved_recipes_invalid(self):
        """Does not show saved recipes if loggedout user."""
        with self.client as c:
            resp = c.get(
                f"/user/{self.testuser.id}/saved-recipes", follow_redirects=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn("Unauthorized access", str(resp.data))

    def test_get_user_favourite_recipes(self):
        """Shows user's favourite recipes."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get(f"/user/{self.testuser.id}/favourite-recipes")

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Mushroom", str(resp.data))
            self.assertNotIn("Paneer", str(resp.data))

            favourite_recipes = Recipe.query.filter_by(
                user_id=self.testuser.id, favourite=True).all()
            self.assertEqual(len(favourite_recipes), 1)

    def test_get_user_favourite_recipes_invalid(self):
        """Does not show favourite recipes if logged out user."""
        with self.client as c:
            resp = c.get(
                f"/user/{self.testuser.id}/favourite-recipes", follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Unauthorized access", str(resp.data))
