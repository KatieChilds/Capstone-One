"""Forms for Fridge Raiders app (CAPSTONE ONE)."""

from wtforms import SelectField, StringField, EmailField, URLField, PasswordField, SelectMultipleField, IntegerField, BooleanField, RadioField
from flask_wtf import FlaskForm
from wtforms.validators import InputRequired, Optional, NumberRange

cuisines = ['african', 'american', 'british', 'cajun', 'caribbean', 'chinese', 'eastern european', 'european', 'french', 'german', 'greek', 'indian', 'irish',
            'italian', 'japanese', 'jewish', 'korean', 'latin american', 'mediterranean', 'mexican', 'middle eastern', 'nordic', 'southern', 'spanish', 'thai', 'vietnamese']

diets = ['gluten free', 'ketogenic', 'vegetarian', 'lacto-vegetarian',
         'ovo-vegetarian', 'pescetarian', 'paleo', 'primal', 'low FODMAP', 'Whole30']

intolerances = ['dairy', 'egg', 'gluten', 'grain', 'peanut', 'seafood',
                'sesame', 'shellfish', 'soy', 'sulfite', 'tree nut', 'wheat']


class RegisterForm(FlaskForm):
    """Form for user registration."""
    username = StringField("Username", validators=[InputRequired()])
    first_name = StringField("First Name", validators=[InputRequired()])
    last_name = StringField("Last Name", validators=[InputRequired()])
    email = EmailField("Email", validators=[InputRequired()])
    image_url = URLField("Photo URL", default=None)
    password = PasswordField("Password", validators=[InputRequired()])


class LoginForm(FlaskForm):
    """Form for user login."""
    username = StringField("Username", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired()])


class UpdateUserForm(FlaskForm):
    """Form to update user profile details."""
    username = StringField("Username", validators=[InputRequired()])
    first_name = StringField("First Name", validators=[InputRequired()])
    last_name = StringField("Last Name", validators=[InputRequired()])
    email = EmailField("Email", validators=[InputRequired()])
    image_url = URLField("Photo URL", default=None)


class ByIngredientsForm(FlaskForm):
    """Form for user to find recipes using findByIngredients."""
    ingredients = StringField("What ingredients do you have?",
                              validators=[InputRequired()])
    ranking = RadioField("Choose One:", choices=[(
        1, "Maximize used ingredients"), (2, "Minimize missing ingredients")], coerce=int, validators=[InputRequired()])
    number = IntegerField("Number of Recipes to View", default=5)


class ComplexSearchForm(FlaskForm):
    """Form for user to find recipes using complexSearch."""
    cuisine = SelectMultipleField("Cuisine(s)", choices=[(
        c, c) for c in cuisines], validators=[Optional()])
    diet = SelectMultipleField(
        "Diet(s)", choices=[(d, d) for d in diets], validators=[Optional()])
    intolerances = SelectMultipleField(
        "Intolerance(s)", choices=[(i, i) for i in intolerances], validators=[Optional()])
    includeIngredients = StringField("Ingredients to Include", validators=[
        Optional(strip_whitespace=True)])
    excludeIngredients = StringField("Ingredients to Exclude", validators=[
        Optional(strip_whitespace=True)])
    maxReadyTime = IntegerField(
        "Max Cooking Time", default=20, validators=[NumberRange(min=0, max=180, message="Value must be between 0 and 180.")])
    number = IntegerField("Number of Recipes to View", default=5)
    save = BooleanField("Save Preferences")


class UpdatePreferencesForm(FlaskForm):
    """Form to update user saved preferences for searching."""
    cuisine = SelectMultipleField("Cuisine(s)", choices=[(
        c, c) for c in cuisines], validators=[Optional()])
    diet = SelectMultipleField(
        "Diet(s)", choices=[(d, d) for d in diets], validators=[Optional()])
    intolerances = SelectMultipleField(
        "Intolerance(s)", choices=[(i, i) for i in intolerances], validators=[Optional()])
    includeIngredients = StringField("Ingredients to Include", validators=[
        Optional(strip_whitespace=True)])
    excludeIngredients = StringField("Ingredients to Exclude", validators=[
        Optional(strip_whitespace=True)])
    maxReadyTime = IntegerField(
        "Max Cooking Time", default=20, validators=[NumberRange(min=0, max=180, message="Value must be between 0 and 180.")])
    number = IntegerField("Number of Recipes to View", default=5)
