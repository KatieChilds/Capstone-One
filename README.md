# Capstone-One
Capstone Project One for the Springboard SEC bootcamp  
[API URL](https://spoonacular.com/food-api/docs)  

Site Name: Fridge Raiders Capstone  
[Link](https://fridge-raiders-capstone.herokuapp.com/)

Fridge Raiders allows you to search for recipes based on type of cuisine and other preferences.  
If you signup to the site you will be able to not only search for recipes based on preferences but you will be able to search based on what ingredients you already have. You will be able to save recipes to try and add recipes to your favourites if you really liked them. The site can store a user's selected search preferences for them also. Oh, did I forget to mention that it also has features to let you search for alternatives for ingredients you might be missing from a recipe and build your own shopping list?!  

Full list of Features:  
* Search Recipes based on preferences - preferences include: cuisine, intolerances, diet, ingredients to include or exclude, time to prepare and max number of recipes to return. This feature is available to any user and is included as the most basic version of the site. It was included to that any user could visit the site and still be able to interact with it without the need to signup.
* Search Recipes based on ingredients - Users who have signed up to the site can input ingredients they already have and search for recipes based on maximising their use or minimising the number of ingredients they are missing. It was included so that users could find recipes that make use of what they already have.
* Save a Recipe - Users who signup can choose to save a chosen recipe so that they can easily find it when navigating back to the site for future use. It was included to make user experience more tailored and negate needing to search for the same recipe over and over again.
* Favourite a Recipe - Similar to saving a recipe, a user can favourite any of their saved recipes to keep track of those that they enjoyed. Again, it was included to make the user experience more tailored and easy.
* Build a Shopping List - Based on a chosen recipe, a signed in user can add ingredients to their shopping list to help them keep track of what they need to buy. It was included to create a more holistic site for users and what information they might need from their search results.
* Delete items from shopping list - A user can delete an item from their shopping list. Included to allow for user's to change their needs as required.
* Search for alternative ingredients - If a user has searched by ingredients they already have, they can choose any of the ingredients they are missing and search for possible alternatives. This feature was included to try to help users minimise the ingredients they are missing even further by offering up suggestions for things to use instead.
* Save Preferences - A signed in user can save their preferences when searching based on preferences so that they will not need to fill them in every time. This was included to make the user experience more tailored.
* Update Profile - A user can update their profile details, including username, first and last names, image and email address. It was included to allow for flexibility for a user to change information about themselves.
* Update Preferences - A user can update their saved preferences if they change their mind about their favourite choices or their diet/intolerances change. This feature was included to allow for user's to adapt and change preferences as needed.

What will your user experience be like?!  
If you do not wish to sign up, your user experience will allow you to search for recipes based on your chosen preferences. You can choose a recipe to view the details and even choose to view similar recipes. At this point you will need to sign up to access the remaining features.  

If you do sign up, you can carry out a search as described above but with the option to save your chosen preferences. You can still view the recipes, choose one to see the details and see similar recipes with the added bonus of being able to save a recipe and add it to your favourites if you choose. The other option you have is to search for recipes based on ingredients you already have. You can enter a comma-separated list of ingredients and choose whether to maximise the use of the ingredients you have or minimise the number of missing ingredients. This time the recipes will return with a summary of the number of ingredients it uses that you have, the number of ingredients you are missing, and the number of likes the recipe has received from all users of the API. It will also show a list of the ingredients you are missing and those that you have which is uses. From the list of missing ingredients you can click on any of them to see possible alternatives, if there are any, that could be used instead. From any of the alternatives listed or the original ingredients listed in a chosen recipe you can add these to your shopping list. You can view your shopping list, saved and favourite recipes using the nav-bar. When you are all done, don't forget to logout!  

A few words about the API:
The Spoonacular API has been fantastic to work with. If you do want to play around with the code more feel free to obtain your own free API Key from their site. If hosting a copy yourself locally be sure to get an API Key and put that in where the environment variable is. There are many more endpoints I haven't touched on and if you enjoy what I have done you should check out the API yourself and see what you can do with it. The ideas are endless!  

Tech Stack Used:
* Python 3.11.0
* HTML
* SQLAlchemy
* Flask
* Postgres
* For full dependencies list see the requirements.txt file included in the code files

A note from me:
I had a great time making this! If you do check it out and/or have read this far please do get in touch with any feedback/suggestions/questions.


