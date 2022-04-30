# Recipe Scraper

## **Description**
A web scraper designed to scrape [www.skinnytaste.com](#www.skinnytaste.com) for recipes 

## **Requirements**
Requires python-dotenv package

```pip install python-dotenv```

## **Database Tables and Fields**

**recipes**
- recipe id
- recipe_name
- recipe_notes
- diet (keto etc)
- calories
- prep_time
- cook_time
- difficulty (East, moderate, hard)
- method_id

**ingredients**
- id
- recipe_id
- ingredient_id
- ingredient_name
- amount
- unit
- ingredient_notes

**recipe_method**
- method_id
- recipe_id
- method

**recipe_diet**
- id
- recipe_id
- diet_type  (Vegetarian, Gluten Free, Paleo, Keto, Dairy Free, Low Carb)

**recipe_courses**
- id
- recipe_id
- course



