import mysql.connector
from urllib.request import Request, urlopen
from dbConnection import getConnection
from bs4 import BeautifulSoup
from uuid import uuid4
from datetime import datetime
import re
import ssl
import time

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

dietList = ['Vegetarian', 'Gluten-Free', 'Paleo', 'Keto', 'Dairy-Free', 'Low-Carb']
numOfPages = 5
connection = getConnection()
cursor = connection.cursor(buffered=True)

def isRecipeExist(recipe_name):
    query =  """SELECT recipe_id FROM recipes WHERE recipe_name = %s"""
    cursor.execute(query,(recipe_name,))
    row = cursor.fetchone()
    if row is not None:
        return row[0]   
    return False

def isRecipeDietExist(recipe_id, diet):
    query =  """SELECT * FROM recipe_diet WHERE (recipe_id = %s AND diet_type = %s) """
    values = (recipe_id, diet)
    cursor.execute(query, values)
    row = cursor.fetchone()
    if row is not None:
        return True
    return False

def getDifficulty(cook_time):
    if(cook_time <= 15): return "Easy"
    elif(15 < cook_time <= 30): return "Moderate"
    elif(cook_time > 30): return "Hard"

def updatePageUrl(num, diet, numOfPages=5):
    url = f"https://www.skinnytaste.com/recipes/{diet}/page/{num}/"
    print(f"Page {num} of {numOfPages}...[{url}]")
    return url

def getRecipeUrls(start, numOfPages, diet):
    # make default paramenters 
    # - start = 1
    # - numOfPages = 2
    # -

    urlList = []
    if(start >= numOfPages):
        return

    pageCount = start
    while pageCount <= numOfPages:
        req = Request(updatePageUrl(pageCount, diet), headers={'User-Agent': 'Mozilla/5.0'})
        html = urlopen(req, timeout=10, context=ctx).read()
        soup = BeautifulSoup(html, 'html.parser')

        tag_list = soup.find('div', class_="archives")
        tags = tag_list.findAll('a',{'href': re.compile(r'^(?!https:\/\/www.skinnytaste.com\/recipes\/).*')})
        for tag in tags:
            url = tag.get('href', None)
            urlList.append(url)
            print(url, end='\n')

        pageCount = pageCount + 1
        time.sleep(3)

    return urlList

def getRecipeComponents(url, diet):
    req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urlopen(req, timeout=10, context=ctx).read()
    soup = BeautifulSoup(html, 'html.parser')

    try:
        recipe = soup.find('div', class_="wprm-recipe-template-skinnytaste")
        recipe_name = recipe.find('h2', class_ = "wprm-recipe-name").get_text()

        if(recipe.find('div', class_ = "wprm-recipe-prep-time-container") is not None):
            if(recipe.find('span', class_ = "wprm-recipe-prep_time-hours")):
                prep_time =  int(recipe.find('span', class_ = "wprm-recipe-prep_time-hours").get_text()) * 60
                if(recipe.find('span', class_ = "wprm-recipe-prep_time-minutes")):
                    prep_time = prep_time + int(recipe.find('span', class_ = "wprm-recipe-prep_time-minutes").get_text())
            else:
                prep_time = int(recipe.find('span', class_ = "wprm-recipe-prep_time-minutes").get_text())
        else:
            prep_time = 0

        # print('prep_time', prep_time)
        if(recipe.find('div', class_ = "wprm-recipe-cook-time-container") is not None):
            if(recipe.find('span', class_ = "wprm-recipe-cook_time-hours")):
                cook_time = int(recipe.find('span', class_ = "wprm-recipe-cook_time-hours").get_text()) * 60
                if(recipe.find('span', class_ = "wprm-recipe-cook_time-minutes")):
                    cook_time = cook_time + int(recipe.find('span', class_ = "wprm-recipe-cook_time-minutes").get_text())
            else:
                cook_time = int(recipe.find('span', class_ = "wprm-recipe-cook_time-minutes").get_text())
        else:
            cook_time = 0
        # print('cook_time', cook_time)
        
        calories = round(float(recipe.find('span', class_ = "wprm-recipe-calories").get_text()))
        # print('calories', calories)

        courses = recipe.find('span', class_ = "wprm-recipe-course").get_text().split(', ')
        # print('courses', courses)

        method = recipe.find('ul', class_="wprm-recipe-instructions").get_text()
        # print('method', method)

        difficulty = getDifficulty(cook_time)
        # print('difficulty', difficulty)


        recipe_notes = ""
        if(recipe.find('div', class_="wprm-recipe-template-skinnytaste")):
            recipe_notes = recipe.find('div', class_="wprm-recipe-template-skinnytaste").get_text()
        # print('recipe_notes', recipe_notes)

    except (AttributeError, NameError, ValueError, UnboundLocalError) as err:
        print(f"Something went wrong: {err}")
        print(f"Recipe: {url}")
        with open("problem-recipes-urls.txt",'a') as urlFile, open("problem-recipes-diet.txt",'a') as dietFile:
            urlFile.write(f"{url}\n")
            dietFile.write(f"{diet}\n")
        return

    time.sleep(2)

    try:

        if (isRecipeExist(recipe_name)):
            print(f'Recipe {recipe_name} is already stored in Database!')
            id = isRecipeExist(recipe_name)
            if(id is not False) and (isRecipeDietExist(id, diet) is False): 
                insertRecipeDiet(id, diet)
            return 

        recipe_id = str(uuid4())
        method_id = insertMethod(recipe_id, method)
        insertRecipe(recipe_id, recipe_name, recipe_notes, calories, prep_time, cook_time, difficulty, method_id)
        insertRecipeDiet(recipe_id, diet)
    
        ingredient_group = recipe.find('ul', class_ = "wprm-recipe-ingredients")
        ingredient_tags = ingredient_group.findAll('li', class_ = "wprm-recipe-ingredient")

        ingredient_count = 0
        for i in ingredient_tags:
            
            ingredient_name= ""
            ingredient_amount= ""
            ingredient_unit= ""
            ingredient_notes = ""

            if (i.find('span', class_ = "wprm-recipe-ingredient-name")):
                ingredient_name = i.find('span', class_ = "wprm-recipe-ingredient-name").get_text()

            if (i.find('span', class_ = "wprm-recipe-ingredient-amount")):
                ingredient_amount = i.find('span', class_ = "wprm-recipe-ingredient-amount").get_text()

            if (i.find('span', class_ = "wprm-recipe-ingredient-unit")):
                ingredient_unit = i.find('span', class_ = "wprm-recipe-ingredient-unit").get_text()

            if (i.find('span', class_ = "wprm-recipe-ingredient-notes")):
                ingredient_notes = i.find('span', class_ = "wprm-recipe-ingredient-notes").get_text()

            try:
                ingredient_count = ingredient_count + 1
                insertIngredients(recipe_id, ingredient_name, ingredient_amount, ingredient_unit , ingredient_notes)
            except connection.Error as err:
                print("Something went wrong: {}".format(err))

        print(f"Ingredients [{ingredient_count}] inserted successfully")

        for course in courses:
            insertRecipeCourse(recipe_id, course)
    
        return recipe_name

    except (mysql.connector.Error, AttributeError, NameError, ValueError, UnboundLocalError) as err:
        print("Something went wrong: {}".format(err))

def insertRecipe(recipe_id, recipe_name, recipe_notes, calories, prep_time, cook_time, difficulty, method_id):
    insert_query =  """INSERT INTO recipes (recipe_id, recipe_name, recipe_notes, calories, prep_time, cook_time, difficulty, method_id) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s) """
    values = (recipe_id, recipe_name, recipe_notes, calories, prep_time, cook_time, difficulty, method_id)
    cursor.execute(insert_query, values)
    connection.commit()
    print("Recipe inserted successfully")

def insertIngredients(recipe_id, ingredient_name, ingredient_amount, ingredient_unit, ingredient_notes):
    ingredient_id = str(uuid4())
    insert_query =  """INSERT INTO ingredients (ingredient_id, recipe_id, ingredient_name, amount, unit, ingredient_notes) 
                    VALUES (%s, %s, %s, %s, %s, %s) """
    values = (ingredient_id, recipe_id, ingredient_name, ingredient_amount, ingredient_unit, ingredient_notes)
    cursor.execute(insert_query, values)
    connection.commit()
    # print("Ingredient inserted successfully")
    return ingredient_id

def insertMethod(recipe_id, method):
    method_id = str(uuid4())
    insert_query =  """INSERT INTO recipe_method (method_id, recipe_id, method) 
                    VALUES (%s, %s, %s) """
    values = (method_id, recipe_id, method)
    cursor.execute(insert_query, values)
    connection.commit()
    print("Method inserted successfully")
    return method_id

def insertRecipeIngredient(recipe_id, ingredient_id):
    id = str(uuid4())
    insert_query = """INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id) VALUES (%s, %s, %s) """
    values = (id, recipe_id, ingredient_id)
    cursor.execute(insert_query, values)
    connection.commit()
    print("Recipe-Ingredient entry inserted successfully")

def insertRecipeDiet(recipe_id, diet):
    id = str(uuid4())
    insert_query = """INSERT INTO recipe_diet (id, recipe_id, diet_type) VALUES (%s, %s, %s) """
    values = (id, recipe_id, diet)
    cursor.execute(insert_query, values)
    connection.commit()
    print("Recipe-Diet entry inserted successfully")
    return id

def insertRecipeCourse(recipe_id, course):
    id = str(uuid4())
    insert_query = """INSERT INTO recipe_courses (id, recipe_id, course) VALUES (%s, %s, %s) """
    values = (id, recipe_id, course)
    cursor.execute(insert_query, values)
    connection.commit()
    print("Recipe-Course entry inserted successfully")
    return id

if __name__ == "__main__":

    count = 0
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    print(f"Start: {dt_string}\n")	

    for diet in dietList:
        urlList = getRecipeUrls(start, numOfPages, diet)
        print(f"Completed....gathered {len(urlList)} {diet} recipe urls\n")
        print("Inserting....\n")
        for url in urlList:
            recipe_name = getRecipeComponents(url, diet)
            if recipe_name is not None :
                count = count + 1
                cur_time = datetime.now().strftime("%H:%M:%S")
                print(f"{count}) {recipe_name} was Complete -- {cur_time}\n")
    
    cursor.close()

    
    