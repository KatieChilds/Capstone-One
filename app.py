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
            username=form.username.data, password=form.password.data)

        if user:
            flash(f"Hello, {user.username}!", 'success')
            return redirect('/')

        flash("Invalid credentials. Please try again if you have already signed up. Otherwise please click the signup button to join.", 'danger')
    else:
        return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    """Handle user logout."""
    do_logout()
    flash("You have been logged out. Log back in below to access all of the features.", 'success')
    return redirect('/login')

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
        return redirect('/recipes')
    else:
        return render_template('recipes/complex_search.html', form=form)


@app.route('/recipes')
def show_recipes():
    """Shows the recipes collected from the search results."""
    return render_template('recipes/show.html', recipes=session['recipes'])


@app.route('/recipes/<int:recipe_id>')
def get_recipe(recipe_id):
    """Shows detailed information for the chosen recipe."""
    res = requests.get(
        f"{API_BASE_URL}recipes/{recipe_id}/information", params={'apiKey': API_KEY})
    recipe = res.json()

    return render_template('recipes/details.html', recipe=recipe)
# *********************************************************************** #
    #

 # *********************************************************************** #


@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req
