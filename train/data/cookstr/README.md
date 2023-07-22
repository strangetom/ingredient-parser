# Cookstr

This dataset is derived from 7918 recipes scraped from [cookstr.com](cookstr.com) between 2017-06 and 2017-07. The original data can be found at https://archive.org/details/recipes-en-201706.

The `cookstr-ingredients-snapshot-2017.csv` file was derived from the source data with the following steps:

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

   This list contains 48084 sentences

3. Turn this list of ingredient sentences into a csv compatible with the training process by using `ingredient_parser.parse_ingredient_regex` to parse each sentence, then write the csv.

   ```python
   rows = []
   for ing in ingredients:
       parsed = parse_ingredient_regex(ing)
       
       rows.append([
           ing,
           parsed["name"],
           parsed["quantity"],
           parsed["unit"],
           parsed["comment"]
       ])
   with open("ingredient_parser/train/data/cookstr/cookstr-ingredients-snapshot-2017.csv", "w") as f:
       writer = csv.writer(f)
       writer.writerow(["input", "name", "quantity", "unit", "comment"])
       for row in rows:
           writer.writerow(row)
   ```

   This dataset was bootstrapped using the regex based parser (revision b2025e637b683b7a1d3e7502587a536bf1de8bbe) to turn the sentences into training data without having to do it manually. This is not intended to represent a useful, clean training dataset, but instead to jump start it's usefulness. T**he dataset will need to go through similar cleaning processing as the NYT dataset.**

   The model based parser was not used to avoid reinforcing inaccuracies. If the model based parser at the time of generating this dataset performed poorly with certain sentence constructs or ingredients, then using that parser to create this training data which would then be fed back into the model training process would reinforce those inaccuracies.