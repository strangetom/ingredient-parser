# BBC

This dataset is derived from 10599 recipes scraped from [bbc.co.uk/food](https://bbc.co.uk/food) between 2017-06 and 2017-07. The original data can be found at https://archive.org/details/recipes-en-201706.

The `bbc-ingredients-snapshot-2017.csv` file was derived from the source data with the following steps:

1. Load `cookstr-recipes.json`

   ```python
   with open("recipes-en-201706/cookstr-recipes.json", "r") as f:
       lines = f.readlines()
   recipes = [json.loads(l) for l in lines]
   ```

   

2. Iterate through all recipes and create a list of unique ingredient sentences

   ```python
   ingredients = set()
   for recipe in recipes:
       if "ingredients" in recipe.keys():
           for i in recipe["ingredients"]:
               ingredients.add(i)
   ```

   This list contains 63195 sentences