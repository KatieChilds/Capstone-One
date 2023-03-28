from flask import Flask, redirect, render_template, session, g, flash, request
import requests
from flask_debugtoolbar import DebugToolbarExtension
from sqlalchemy.exc import IntegrityError
from models import db, connect_db, User, Recipe, Preference
from forms import RegisterForm, LoginForm, ByIngredientsForm, ComplexSearchForm
from secret import API_KEY
from bs4 import BeautifulSoup

CURR_USER_KEY = 'curr_user'
API_BASE_URL = 'https://api.spoonacular.com/'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///fridge_raiders'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)
app.app_context().push()
db.create_all()

app.config['SECRET_KEY'] = "oh-so-very-very-secret"

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
    if not g.user and g.user.id != user_id:
        flash("Unauthorized access. Please login.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    preferences = Preference.query.filter(
        Preference.user_id == user_id).first()
    return render_template('users/profile.html', user=user, preferences=preferences.preferences)


# *********************************************************************** #
    # Recipe views


def create_search_string(preferences):
    """Construct the query string needed for the API endpoint of complexSearch."""
    choices = []
    for (k, v) in preferences.items():
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
    preferences = {}
    if form.validate_on_submit():
        for choice in form.data:
            if choice != 'csrf_token' and form.data[choice] != [] and form.data[choice] != None and form.data[choice] != '' and choice != 'save':
                preferences[choice] = form.data[choice]

        query_string = create_search_string(preferences)

        res = requests.get(
            f"{API_BASE_URL}recipes/complexSearch?{query_string}", params={'apiKey': API_KEY})
        recipes = res.json()['results']
        session['recipes'] = recipes
        if g.user and form.data['save'] == True:
            save_preferences = Preference(
                user_id=g.user.id, preferences=preferences)
            db.session.add(save_preferences)
            db.session.commit()
        return redirect('/recipes')
    else:
        return render_template('recipes/complex_search.html', form=form)


@app.route('/recipes')
def show_recipes():
    """Shows the recipes collected from the complexSearch results."""
    return render_template('recipes/show.html', recipes=session['recipes'])


@app.route('/recipes/<int:recipe_id>')
def get_recipe(recipe_id):
    """Shows detailed information for the chosen recipe."""
    res = requests.get(
        f"{API_BASE_URL}recipes/{recipe_id}/information", params={'apiKey': API_KEY})
    recipe = res.json()

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
    return render_template('recipes/show_byIngredients.html', recipes=session['recipes'])


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


@app.route('/user/<int:user_id>/preferences', methods=["GET", "POST"])
def update_user_preferences(user_id):
    """Update user preferences on profile page and in database."""


@app.route('/user/<int:user_id>/shoppinglist')
def get_user_shoppinglist(user_id):
    """Retrieves user's shopping list from API and displays."""


@app.route('/user/<int:user_id>/shoppinglist/add', methods=["POST"])
def add_to_shoppinglist(user_id):
    """Add an item to a user's shopping list."""


@app.route('/user/<int:user_id>/shoppinglist/delete', methods=["DELETE"])
def delete_from_shoppinglist(user_id):
    """Delete an item from a user's shopping list."""


@app.route('/user/<int:user_id>/saved-recipes')
def get_user_saved_recipes(user_id):
    """Shows user's saved recipes."""


@app.route('/user/<int:user_id>/favourite-recipes')
def get_user_favourite_recipes(user_id):
    """Shows user's favourite recipes."""
# *********************************************************************** #


@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
