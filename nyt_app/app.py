# web scraping packages
import requests
import json
from bs4 import BeautifulSoup
from fpdf import FPDF
from flask import Flask, request, send_file, render_template, jsonify
import os
from pathlib import Path
from unidecode import unidecode


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download_recipe', methods=['GET', 'POST'])
def download_recipe():
    if request.method == 'POST':
        url = request.form['url']
        # url = input("Enter the URL of the recipe you want to download from NYT Cooking: ")
        # url = "https://cooking.nytimes.com/recipes/1020043-pressure-cooker-chipotle-honey-chicken-tacos"
        try:
            page = requests.get(url)
        except requests.exceptions.RequestException as e:
            print("Oops...something went wrong. Please check the URL and try again.")
            raise

        soup = BeautifulSoup(page.content, 'html5lib')

        # The recipe content in the provided source code is embedded within a <script> element with the attribute type="application/ld+json"
        table = soup.find('script', attrs={'type':'application/ld+json'})
        # get tips
        tips = soup.find('div', attrs={'class':'tips_tips__Fa_AO'})

        if tips:
            tips_label = tips.find('span', attrs={'class': 'pantry--label'})
            if tips_label and tips_label.text.lower() == 'tip':
                tips_list = tips.find('ul', attrs={'class': 'tips_tipsList__hQ0LX'})
                if tips_list:
                    tips_items = tips_list.find_all('li', attrs={'class': 'pantry--body-long'})
                    tips_content = [tip.get_text(separator=' ', strip=True) for tip in tips_items]
                    # Now 'tips_content' contains a list of tips
                    tips_content = [unidecode(tip.get_text(separator=' ', strip=True)) for tip in tips_items]


        # The recipe content is in JSON format, so we can use the json package to parse it
        data = json.loads(table.string)
        name = unidecode(data['name']).encode("latin-1").decode("latin-1")

        # Original string
        description = data['description']
        # Remove or replace non-Latin-1 characters
        description = unidecode(description).encode("latin-1").decode("latin-1")

        yd = data['recipeYield'].encode("latin-1").decode("latin-1")
        ingredients = [unidecode(ingredient).encode("latin-1").decode("latin-1") for ingredient in data['recipeIngredient']]
        instructions = [{'@type': instruction['@type'], 'text': unidecode(instruction['text']).encode("latin-1").decode("latin-1")} for instruction in data['recipeInstructions']]

        nutrition_cal = str(data['nutrition']['calories'])
        nutrition_carbs = str(data['nutrition']['carbohydrateContent'])
        nutrition_protein = str(data['nutrition']['proteinContent'])
        nutrition_fat = str(data['nutrition']['fatContent'])
        nutrition_sodium = str(data['nutrition']['sodiumContent'])
        nutrition_fiber = str(data['nutrition']['fiberContent'])
        nutrition_sugar = str(data['nutrition']['sugarContent'])

        # Parse HTML content, in case the description contains HTML tags
        soup = BeautifulSoup(description, 'html.parser')
        # Extract text content within <a> tags
        linked_text = soup.find('a').get_text(separator=' ', strip=True) if soup.find('a') else None
        # Remove all HTML tags
        description = soup.get_text(separator=' ', strip=True)


        pdf = FPDF()
        pdf.set_title(name)
        # Adding a page
        pdf.add_page()
        # set style and size of font 
        pdf.set_font("helvetica", 'UB', size = 16)
        # create a cell
        pdf.cell(200, 10, txt = name, ln = 1, align = 'C')
        pdf.set_font("helvetica", size = 12)
        pdf.cell(200, 10, txt = "Recipe Yield: " + yd, ln = 3, align = 'C')
        pdf.ln(5)  # Adjust the value to set the desired space

        pdf.multi_cell(200, 10, txt = description)
        pdf.ln(5)  # Adjust the value to set the desired space

        # Combine nutrition information
        nutrition_info = f"Calories: {nutrition_cal} | Carbs: {nutrition_carbs} | Protein: {nutrition_protein} | Fat: {nutrition_fat} | Sodium: {nutrition_sodium} | Fiber: {nutrition_fiber} | Sugar: {nutrition_sugar}"

        # Create a multi_cell for the nutrition information
        pdf.multi_cell(200, 4, txt=nutrition_info)
        pdf.ln(10)

        pdf.set_font("helvetica", 'B', size=14)
        pdf.cell(200, 10, txt = "Ingredients:", ln = 5)
        pdf.set_font("helvetica", size = 12)
        ingredient_text = "\n".join(ingredients)
        pdf.multi_cell(200, 10, txt=ingredient_text, align='L')

        pdf.ln(5)

        pdf.set_font("helvetica", 'B', size=14)
        pdf.cell(200, 10, txt = "Instructions", ln = 7)
        pdf.set_font("helvetica", size = 12)
        # Loop through instructions and add each with numbering
        for index, instruction in enumerate(instructions, start=1):
            instruction_text = f"{index}. {instruction['text']}"
            pdf.multi_cell(200, 10, txt=instruction_text, align='L')

        if tips:
            pdf.ln(5)
            pdf.set_font("helvetica", 'B', size=12)
            pdf.cell(200, 10, txt = "Notes: ", ln = 7)
            pdf.set_font("helvetica", size = 12)
            pdf.multi_cell(200, 10, txt="\n".join(tips_content), align='L')

        filename = name.replace(" ", "_") + ".pdf"
        downloads_path = str(Path.home() / "Downloads")
        pdf_path = os.path.join(downloads_path, filename)
        pdf.output(pdf_path)
        return send_file(pdf_path, as_attachment=True), 200, {'message': 'Recipe downloaded successfully! Check your Downloads folder.'}

    return render_template('download_recipe.html')

if __name__ == '__main__':
    app.run(debug=False)
