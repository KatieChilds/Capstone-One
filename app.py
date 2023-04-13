from flask import Flask, redirect, render_template, session, g, flash
import requests
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User, Recipe, Preference
from forms import RegisterForm, LoginForm, ByIngredientsForm, ComplexSearchForm, UpdateUserForm, UpdatePreferencesForm
# from secret import API_KEY, key
import json
import os


CURR_USER_KEY = 'curr_user'
API_BASE_URL = 'https://api.spoonacular.com/'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'postgresql:///fridge_raiders')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['API_KEY'] = os.environ.get('API_KEY')

connect_db(app)
app.app_context().push()
db.create_all()

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

debug = DebugToolbarExtension(app)

# *********************************************************************** #
# Login/Logout/Keep user logged in


@app.before_request
def add_user_to_g():
    """If user is logged in, add curr_user to Flask global."""
    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None


def do_login(user):
    """Login user."""
    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

# *********************************************************************** #
# Homepage and Handling Signup/Login/Logout


@app.route('/')
def homepage():
    """Renders homepage for app."""
    return render_template('homepage.html', user=g.user)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Shows signup page and handles form submission."""

    form = RegisterForm()

    if form.validate_on_submit():
        try:

            user = User.signup(
                username=form.username.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                image_url=form.image_url.data,
                password=form.password.data)
            db.session.commit()

        except IntegrityError:
            flash("Username already taken. Please try another.", 'danger')
            return render_template('signup.html', form=form)

        do_login(user)

        return redirect('/')

    else:
        return render_template('signup.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(
            form.username.data, form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", 'success')
            return redirect('/')

        flash("Invalid credentials. Please try again if you have already signed up. Otherwise please click the signup button to join.", 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    """Handle user logout."""
    do_logout()
    flash("You have been logged out. Log back in below to access all of the features.", 'success')
    return redirect('/login')


@app.route('/user/<int:user_id>')
def show_user_profile(user_id):
    """Shows the user profile."""
    if not g.user or g.user.id != user_id:
        flash("Unauthorized access.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    user_preferences = Preference.query.filter(
        Preference.user_id == user_id).first()
    if user_preferences != None:
        preferences = json.loads(user_preferences.preferences)
    else:
        preferences = {"Notice": "No saved preferences."}
    return render_template('users/profile.html', user=user, preferences=preferences)


# *********************************************************************** #
    # Recipe views


def create_search_string(data):
    """Construct the query string needed for the API endpoint of complexSearch."""
    choices = []
    for (k, v) in data.items():
        if isinstance(v, list):
            new_v = ",".join(v)
            choices.append(f"{k}={new_v}")
        else:
            choices.append(f"{k}={v}")
    query_string = "&".join(choices)

    return query_string


@app.route('/recipes/search', methods=["GET", "POST"])
def search_recipes():
    """Show search form and handle form submission for general recipe search."""
    form = ComplexSearchForm()
    data = {}

    if form.validate_on_submit():
        for choice in form.data:
            if choice != 'csrf_token' and form.data[choice] != [] and form.data[choice] != None and form.data[choice] != '' and choice != 'save':
                data[choice] = form.data[choice]

        query_string = create_search_string(data)

        res = requests.get(
            f"{API_BASE_URL}recipes/complexSearch?{query_string}", params={'apiKey': API_KEY})
        recipes = res.json()['results']
        session['recipes'] = recipes
        if g.user and form.data['save'] == True:
            try:
                save_preferences = Preference(
                    user_id=g.user.id, preferences=data)
                db.session.add(save_preferences)
                db.session.commit()
            except IntegrityError:
                flash("Preferences have already been saved. Please do not check the box at the bottom of the form to continue with your search. If you wish to update your preferences please do so through your user profile.", "danger")
                return redirect('/recipes/search')
        return redirect('/recipes')
    else:
        return render_template('recipes/complex_search.html', form=form)


@app.route('/recipes')
def show_recipes():
    """Shows the recipes collected from the complexSearch results."""
    if session['recipes'] == []:
        flash("Sorry, no recipes were found that match your search criteria. Please ammend your search and try again.", "info")
        return redirect('/recipes/search')
    return render_template('recipes/show.html', recipes=session['recipes'])


def get_saved_recipe_ids(recipes):
    """Creates a list of recipe ids from user's saved recipes."""
    user_recipes = []
    for recipe in recipes:
        user_recipes.append(recipe.recipe_id)
    return user_recipes


@app.route('/recipes/<int:recipe_id>')
def get_recipe(recipe_id):
    """Shows detailed information for the chosen recipe."""
    res = requests.get(
        f"{API_BASE_URL}recipes/{recipe_id}/information", params={'apiKey': API_KEY})
    recipe = res.json()
    if g.user:
        saved_recipes = Recipe.query.filter_by(user_id=g.user.id).all()
        saved_recipes_ids = get_saved_recipe_ids(saved_recipes)
        return render_template('recipes/details.html', recipe=recipe, saved_recipes=saved_recipes_ids)
    return render_template('recipes/details.html', recipe=recipe)


@app.route('/recipes/byIngredients', methods=["GET", "POST"])
def get_byIngredients():
    """Show search form for What's in you fridge? and handles submission."""
    if not g.user:
        flash("Must be logged in to use that feature.", "danger")
        return redirect("/recipes/search")

    form = ByIngredientsForm()
    choices = {}
    if form.validate_on_submit():
        for choice in form.data:
            if choice != 'csrf_token':
                choices[choice] = form.data[choice]
        query_string = create_search_string(choices)

        res = requests.get(
            f"{API_BASE_URL}recipes/findByIngredients?{query_string}&ignorePantry=true", params={'apiKey': API_KEY})
        recipes = res.json()
        session['recipes'] = recipes
        return redirect('/recipes/results')
    else:
        return render_template('recipes/byIngredients.html', form=form)


@app.route('/recipes/results')
def show_byIngredients_recipes():
    """Shows the recipes collected from the byIngredients search results."""
    if session['recipes'] == []:
        flash("Sorry, no recipes were found that match your search criteria. Please ammend your search and try again.", "info")
        return redirect('/recipes/byIngredients')
    return render_template('recipes/show_byIngredients.html', recipes=session['recipes'])


@app.route('/recipes/<int:recipe_id>/saved', methods=["POST"])
def save_recipe(recipe_id):
    """Allows user to save a chosen recipe."""
    if not g.user:
        flash("Unauthorized access. Please login.", "danger")
        return redirect("/")

    saved_recipe = Recipe(user_id=g.user.id, recipe_id=recipe_id)
    db.session.add(saved_recipe)
    db.session.commit()
    return redirect(f"/user/{g.user.id}/saved-recipes")


@app.route('/recipes/<int:recipe_id>/favourite', methods=["POST"])
def add_favourite(recipe_id):
    """Allow users to favourite a recipe."""
    if not g.user:
        flash("Unauthorized access. Please login.", "danger")
        return redirect("/")

    recipe = Recipe.query.get_or_404(recipe_id)
    recipe.favourite = True
    db.session.commit()
    return redirect(f"/user/{g.user.id}/favourite-recipes")


@app.route('/recipes/<int:recipe_id>/favourite/remove', methods=["POST"])
def remove_favourite(recipe_id):
    """Removes favourite from user's favourite recipes and updates db."""
    if not g.user:
        flash("Unauthorized access. Please login.", "danger")
        return redirect("/")

    recipe = Recipe.query.get_or_404(recipe_id)
    recipe.favourite = False
    db.session.commit()
    return redirect(f"/user/{g.user.id}/favourite-recipes")


@app.route('/ingredient/<int:ingredient_id>')
def get_ingredient_substitutes(ingredient_id):
    """Display substitutes for a given ingredient."""
    res = requests.get(
        f"{API_BASE_URL}food/ingredients/{ingredient_id}/substitutes", params={'apiKey': API_KEY})
    substitutes = res.json()
    return render_template('recipes/ingredients.html', substitutes=substitutes)


@app.route('/recipes/<int:recipe_id>/similar')
def get_similar_recipes(recipe_id):
    """Display similar recipes for a given recipe."""
    res = requests.get(
        f"{API_BASE_URL}recipes/{recipe_id}/similar", params={'apiKey': API_KEY})
    recipes = res.json()
    return render_template('recipes/show.html', recipes=recipes)

# *********************************************************************** #
# User related views: updating profile and preferences, saving/favourite recpes, and managing shopping lists


@app.route('/user/<int:user_id>/update', methods=["GET", "POST"])
def update_user_profile(user_id):
    """Update user details on profile page and in database."""
    if not g.user or g.user.id != user_id:
        flash("Unauthorized access. Please login or view your own profile.", "danger")
        return redirect("/")
    user = User.query.get_or_404(user_id)
    form = UpdateUserForm(obj=user)

    if form.validate_on_submit():
        taken = User.query.filter_by(username=form.username.data).first()
        if taken == None:
            user.username = form.username.data
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.email = form.email.data
            user.image_url = form.image_url.data
            db.session.commit()
            return redirect(f"/user/{user.id}")
        elif taken.id == user_id:
            user.username = form.username.data
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.email = form.email.data
            user.image_url = form.image_url.data
            db.session.commit()
            return redirect(f"/user/{user.id}")
        else:
            flash("Username already taken. Please try another.", 'danger')
            return render_template('users/update.html', form=form)
    else:
        return render_template('users/update.html', form=form)


@app.route('/user/<int:user_id>/preferences', methods=["GET", "POST"])
def update_user_preferences(user_id):
    """Update user preferences on profile page and in database."""
    if not g.user or g.user.id != user_id:
        flash("Unauthorized access. Please login.", "danger")
        return redirect("/")

    user_preferences = Preference.query.filter_by(user_id=user_id).first()
    if user_preferences:
        form = UpdatePreferencesForm(data=user_preferences.preferences)
    else:
        form = UpdatePreferencesForm()
    if form.validate_on_submit():
        preferences = {}
        for choice in form.data:
            if choice != 'csrf_token' and form.data[choice] != [] and form.data[choice] is not None and form.data[choice] != '':
                preferences[choice] = form.data[choice]
        # convert preferences dict to JSON formatted string
        preferences_str = json.dumps(preferences)
        if user_preferences is not None:
            user_preferences.preferences = preferences_str
        else:
            save_preferences = Preference(
                user_id=user_id, preferences=preferences_str)
            db.session.add(save_preferences)
        db.session.commit()
        return redirect(f"/user/{user_id}")
    else:
        return render_template('users/update-preferences.html', form=form)


@app.route('/user/<int:user_id>/shoppinglist')
def get_user_shoppinglist(user_id):
    """Retrieves user's shopping list from API and displays."""
    if not g.user or g.user.id != user_id:
        flash("Unauthorized access. Please login.", "danger")
        return redirect("/")
    user = User.query.get_or_404(user_id)
    username = user.api_username
    hash = user.hash
    res = requests.get(f"{API_BASE_URL}mealplanner/{username}/shopping-list",
                       params={'apiKey': API_KEY, 'username': username, 'hash': hash})
    shoppinglist = res.json()['aisles']

    return render_template('users/shoppinglist.html', shoppinglist=shoppinglist)


@app.route('/shoppinglist/add/<ingredient_name>', methods=["GET", "POST"])
def add_to_shoppinglist(ingredient_name):
    """Add an item to a user's shopping list."""
    if not g.user:
        flash("Unauthorized access. Please login.", "danger")
        return redirect("/")
    user = User.query.get_or_404(g.user.id)
    username = user.api_username
    hash = user.hash
    items = {"item": ingredient_name, "parse": True}
    res = requests.post(f"{API_BASE_URL}mealplanner/{username}/shopping-list/items",
                        params={'apiKey': API_KEY, 'username': username, 'hash': hash}, json=items)

    return redirect(f"/user/{g.user.id}/shoppinglist")


@app.route('/shoppinglist/delete/<int:ingredient_id>', methods=["GET", "DELETE"])
def delete_from_shoppinglist(ingredient_id):
    """Delete an item from a user's shopping list."""
    if not g.user:
        flash("Unauthorized access. Please login.", "danger")
        return redirect("/")
    user = User.query.get_or_404(g.user.id)
    username = user.api_username
    hash = user.hash
    res = requests.delete(f"{API_BASE_URL}mealplanner/{username}/shopping-list/items/{ingredient_id}",
                          params={'apiKey': API_KEY, 'username': username, 'hash': hash})
    return redirect(f"/user/{g.user.id}/shoppinglist")


def get_recipe_ids(recipes):
    """Creates a list of recipe ids from user's saved/favourite recipes."""
    user_recipes = []
    for recipe in recipes:
        if recipe.favourite == True:
            user_recipes.append(recipe.recipe_id)
    return user_recipes


@app.route('/user/<int:user_id>/saved-recipes')
def get_user_saved_recipes(user_id):
    """Shows user's saved recipes."""
    if not g.user:
        flash("Unauthorized access. Please login.", "danger")
        return redirect("/")
    all_user_recipes = Recipe.query.filter_by(user_id=user_id).all()
    if len(all_user_recipes) == 0:
        flash("No recipes currently saved.", "info")
        return redirect('/')
    user_recipes = get_recipe_ids(all_user_recipes)
    recipes = []
    for recipe in all_user_recipes:
        res = requests.get(
            f"{API_BASE_URL}recipes/{recipe.recipe_id}/information", params={'apiKey': API_KEY})
        recipes.append(res.json())
    return render_template('users/saved-or-favourite.html', recipes=recipes, user_recipes=user_recipes)


@app.route('/user/<int:user_id>/favourite-recipes')
def get_user_favourite_recipes(user_id):
    """Shows user's favourite recipes."""
    if not g.user:
        flash("Unauthorized access. Please login.", "danger")
        return redirect("/")
    full_user_recipes = Recipe.query.filter_by(
        user_id=user_id, favourite=True).all()
    if full_user_recipes == []:
        flash("No recipes currently in favourites.", "info")
        return redirect('/')
    user_recipes = get_recipe_ids(full_user_recipes)
    recipes = []
    for recipe in full_user_recipes:
        res = requests.get(
            f"{API_BASE_URL}recipes/{recipe.recipe_id}/information", params={'apiKey': API_KEY})
        recipes.append(res.json())
    return render_template('users/saved-or-favourite.html', recipes=recipes, user_recipes=user_recipes)

# *********************************************************************** #


@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
