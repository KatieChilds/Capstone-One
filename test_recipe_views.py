"""Recipe view tests for Fridge Raiders app (CAPSTONE ONE)."""

from app import app, CURR_USER_KEY, create_search_string, get_saved_recipe_ids
import os
from unittest import TestCase
from models import db, connect_db, User, Recipe, Preference
from flask import session

os.environ['DATABASE_URL'] = "postgresql:///fridge_raiders-test"

app.config['SQLALCHEMY_ECHO'] = False

app.config['TESTING'] = True

app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']

app.app_context().push()
db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class RecipeViewsTestCase(TestCase):
    """Test the recipe views for fridge raiders app."""

    def setUp(self):
        """Create test client and add sample data."""
        User.query.delete()
        Recipe.query.delete()
        Preference.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="tester",
                                    first_name="test",
                                    last_name="user",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.testuser_id = 99999
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

    def test_create_search_string(self):
        """Creates the query string for recipe search API calls."""
        self.assertEqual(create_search_string(
            {"cuisine": "italian", "diet": "vegetarian"}), "cuisine=italian&diet=vegetarian")
        self.assertEqual(create_search_string({"cuisine": [
                         "italian", "greek", "korean"], "number": 5}), "cuisine=italian,greek,korean&number=5")

    def test_search_recipes_loggedout_get(self):
        """Shows the search form for logged out users."""
        with self.client as c:
            resp = c.get('/recipes/search')
            self.assertIn("Cuisine(s)", str(resp.data))
            self.assertIn("Diet(s)", str(resp.data))
            self.assertIn("Intolerance(s)", str(resp.data))
            self.assertIn("Max Cooking Time", str(resp.data))
            self.assertIn("recipe box", str(resp.data))
            self.assertNotIn("Save Preferences", str(resp.data))

    def test_search_recipes_user_get(self):
        """Shows the search form for users."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get('/recipes/search')
            self.assertIn("Cuisine(s)", str(resp.data))
            self.assertIn("Diet(s)", str(resp.data))
            self.assertIn("Intolerance(s)", str(resp.data))
            self.assertIn("Max Cooking Time", str(resp.data))
            self.assertIn("recipe box", str(resp.data))
            self.assertIn("Save Preferences", str(resp.data))

    def test_search_recipes_loggedout_post(self):
        """Handles the submitted search form for a logged out user."""
        with self.client as c:
            complex_search_form_data = {"cuisine": "spanish", "diet": "vegetarian", "intolerances": [
            ], "includeIngredients": "", "excludeIngredients": "", "maxReadyTime": 20, "number": "2", "save": False}
            resp = c.post('/recipes/search',
                          data=complex_search_form_data, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Spanish Gazpacho Soup", str(resp.data))
            self.assertIn("Your Recipes from", str(resp.data))
            self.assertIn("Go to Recipe", str(resp.data))
            self.assertNotIn("tester", str(resp.data))

    def test_search_recipes_user_post(self):
        """Handles the submitted search form for a user."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            complex_search_form_data = {"cuisine": "spanish", "diet": "vegetarian", "intolerances": [
            ], "includeIngredients": "", "excludeIngredients": "", "maxReadyTime": 20, "number": "2", "save": False}
            resp = c.post('/recipes/search',
                          data=complex_search_form_data, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Spanish Gazpacho Soup", str(resp.data))
            self.assertIn("Your Recipes from", str(resp.data))
            self.assertIn("Go to Recipe", str(resp.data))
            self.assertIn("tester", str(resp.data))
            # Check that recipes returned in search are stored in session.
            self.assertEqual(len(session['recipes']), 1)
            self.assertIn("Spanish Gazpacho Soup", session['recipes'])

    # def test_session_recipes(self):
    #     """Stores recipes returned from search in the session."""
    #     with self.client as c:
    #         resp = c.get('/recipes')

    #         self.assertEqual(resp.status_code, 200)
    #         self.assertEqual(len(session['recipes']), 1)
    #         self.assertIn("Spanish Gazpacho Soup", session['recipes'])

    def test_session_recipes_empty(self):
        """Shows message to let user know that no recipes were found when session['recipes'] is empty."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess['recipes'] = []

            resp = c.get('/recipes', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                "Sorry, no recipes were found that match", str(resp.data))
            self.assertEqual(len(session['recipes']), 0)

    def test_get_saved_recipe_ids(self):
        """Creates a list of recipe ids to be used by other view functions."""
        saved_recipes = Recipe.query.filter_by(user_id=self.testuser.id).all()
        self.assertEqual(get_saved_recipe_ids(
            saved_recipes), [1095745, 650484])

    def test_get_recipe_loggedout(self):
        """Shows the information of a given recipe for a logged out user."""
        with self.client as c:
            resp = c.get('/recipes/1095745')

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Mushroom Hummus Crostini", str(resp.data))
            self.assertNotIn("SAVE RECIPE", str(resp.data))
            self.assertNotIn("tester", str(resp.data))

    def test_get_recipe_user(self):
        """Shows the information of a given recipe for a user."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get('/recipes/1095841')

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Spanish Gazpacho Soup", str(resp.data))
            self.assertIn("SAVE RECIPE", str(resp.data))
            self.assertIn("tester", str(resp.data))

    def test_get_byIngredients_loggedout(self):
        """Redirects logged out user to homepage."""
        with self.client as c:
            resp = c.get('/recipes/byIngredients', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                "Must be logged in to use that feature.", str(resp.data))
            self.assertNotIn("tester", str(resp.data))

    def test_get_byIngredients_user_get(self):
        """Shows the search form for the What's in your Fridge? search for a user."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get('/recipes/byIngredients')

            self.assertEqual(resp.status_code, 200)
            self.assertIn("What ingredients do you have", str(resp.data))
            self.assertIn("SEARCH", str(resp.data))
            self.assertIn("tester", str(resp.data))

    def test_get_byIngredients_user_post(self):
        """Handles the form submission for the What's in your Fridge? search for a user."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            byIngredients_form_data = {"ingredients": [
                "cheese", "peas", "chicken"], "ranking": 2, "number": 5}
            resp = c.post('/recipes/byIngredients',
                          data=byIngredients_form_data, follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                "Click on an ingredient you are missing", str(resp.data))
            self.assertIn("tester", str(resp.data))
            self.assertIn("Peas And Tarragon", html)
            # Check that recipes returned in search are saved in session.
            self.assertEqual(len(session['recipes']), 5)
            self.assertIn("Peas And Tarragon", session['recipes'])

    # def test_byIngredient_session_recipes(self):
    #     """Stores recipes returned from the byIngredients search."""
    #     with self.client as c:
    #         resp = c.get('/recipes/results')

    #         self.assertEqual(resp.status_code, 200)
    #         self.assertEqual(len(session['recipes']), 5)
    #         self.assertIn("Peas And Tarragon", session['recipes'])

    def test_byIngredient_session_empty(self):
        """Redirects and shows a message if there are not recipes returned."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess['recipes'] = []
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get('/recipes/results', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn(
                "Sorry, no recipes were found that match", str(resp.data))
            self.assertIn("What ingredients do you have", str(resp.data))

    def test_save_recipe_loggedout(self):
        """Redirects and shows a message if there is a logged out user."""
        with self.client as c:
            resp = c.post('/recipes/1095841/saved', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Unauthorized access.", str(resp.data))
            self.assertNotIn("tester", str(resp.data))

    def test_save_recipe_user(self):
        """Saves a recipe to the user's recipes for a user."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.post('/recipes/1095841/saved', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("tester", str(resp.data))
            self.assertIn("Your Recipes", str(resp.data))
            self.assertIn("Spanish Gazpacho Soup", str(resp.data))
            self.assertIn("Palak Paneer", str(resp.data))

    def test_add_favourite_loggedout(self):
        """Redirects and shows message to a logged out user."""
        with self.client as c:
            resp = c.post('/recipes/1095841/favourite', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Unauthorized access.", str(resp.data))
            self.assertNotIn("tester", str(resp.data))

    def test_add_favourite_user(self):
        """Adds a favourite to the user's recipes for a user."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            new_save = Recipe(user_id=self.testuser.id,
                              recipe_id=1095841, favourite=False)
            db.session.add(new_save)
            db.session.commit()
            resp = c.post('/recipes/1095841/favourite', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("tester", str(resp.data))
            self.assertIn("Your Recipes", str(resp.data))
            self.assertIn("Spanish Gazpacho Soup", str(resp.data))
            self.assertNotIn("Palak Paneer", str(resp.data))

    def test_remove_favourite_loggedout(self):
        """Redirects and shows message to a logged out user."""
        with self.client as c:
            resp = c.post('/recipes/1095841/favourite/remove',
                          follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Unauthorized access.", str(resp.data))
            self.assertNotIn("tester", str(resp.data))

    def test_remove_favourite_user(self):
        """Removes a favourite from the user's recipes for a user."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            new_save = Recipe(user_id=self.testuser.id,
                              recipe_id=1095841, favourite=True)
            db.session.add(new_save)
            db.session.commit()
            resp = c.post('/recipes/1095841/favourite/remove',
                          follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("tester", str(resp.data))
            self.assertIn("Your Recipes", str(resp.data))
            self.assertIn("Mushroom Hummus Crostini", str(resp.data))
            self.assertNotIn("Spanish Gazpacho Soup", str(resp.data))
            self.assertNotIn("Palak Paneer", str(resp.data))

    def test_get_ingredient_substitutes(self):
        """Shows a list of substitutes for a chosen ingredient."""
        with self.client as c:
            resp = c.get('/ingredient/2041')

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Possible Ingredient Substitutions", str(resp.data))
            self.assertIn("tarragon leaves", str(resp.data))

    def test_get_ingredient_substitutes_none(self):
        """Shows a message to inform of no available substitutes."""
        with self.client as c:
            resp = c.get('/ingredient/10018368')

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Possible Ingredient Substitutions", str(resp.data))
            self.assertIn(
                "Could not find any substitutes for that ingredient.", str(resp.data))

    def test_get_similar_recipes_loggedout(self):
        """Shows a list of recipes that are similar from the API."""
        with self.client as c:
            resp = c.get('/recipes/1095841/similar')

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Your recipes from", str(resp.data))
            self.assertIn("White Gazpacho", str(resp.data))
            self.assertNotIn("tester", str(resp.data))

    def test_get_similar_recipes_user(self):
        """Shows a list of recipes that are similar form the API for a user."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get('/recipes/1095841/similar')

            self.assertEqual(resp.status_code, 200)
            self.assertIn("tester", str(resp.data))
            self.assertIn("Your recipes from", str(resp.data))
            self.assertIn("White Gazpacho", str(resp.data))
