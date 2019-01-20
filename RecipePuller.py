from allrecipes import AllRecipes
from lib import lib
from flask import Flask, request, render_template, Response, stream_with_context
import re

app=Flask(__name__)

carbsList = ["rice", "pasta", "quinoa", "couscous", "potatoes", "bread", "barley", "oats", "squash"]
fiberList = ["artichoke", "broccoli", "brussels sprouts", "cauliflower", "kale", "carrot", "parsnip", "turnip", "beet", "celery root"]
proteinList = ["chicken", "beef", "pork", "lentils", "black beans", "peas", "eggs"]
meatList = ["chicken", "beef", "ground beef", "pork", "ground pork"]
fruitsVegList = ["bell pepper", "artichoke", "broccoli", "brussels sprouts", "cauliflower", "kale", "carrot", "parsnip", "turnip", "beet", "celery root", "apple", "orange", "bok choi", "cucumber", "lettuce", "tomato", "cabbage"]
fruitsVegList_Small = ["bell pepper", "artichoke", "broccoli", "brussels sprouts", "cauliflower", "kale", "carrot", "parsnip", "turnip"]

scannedItems = {}

measr_lst = ["teaspoon", "t", "tsp", "tablespoon" "T", "tbl", "tbs", "tbsp",
			 "fluid", "fl", "gill", "cup", "pint", "pt", "quart", "qt",
			 "gallon" "gal", "ml", "milliliter", "millilitre", "cc", "mL", "l",
			 "liter", "litre", "L", "dl", "deciliter", "decilitre" "dL",
			 "pound", "lb", "ounce", "oz", "mg", "milligram" "milligramme",
			 "g", "gram", "gramme", "kg" "kilogram", "kilogramme", "mm",
			 "millimeter", "millimetre", "cm", "centimeter", "centimetre",
			 "inch", "inche", "in", "slice", "clove", "head", "can", "bottle",
			 "jar", "bag", "scoop", "cube", "large", "small", "sprig", ""]

gottem_str=""


#--TODO: Calculate lowest item price by price per amount, not just price.--
def getLowestPriceGoods(categoryList, pCode):
	lowestPrice=4096.0
	lowestItem=""
	lowestCoupon={}
	for it in categoryList:
		if it in scannedItems:
			temp=scannedItems[it]
		else:
			temp=getLowestPriceItem(pCode, it)
		if temp[1]<lowestPrice:
			lowestPrice=temp[1]
			lowestItem=it
			lowestCoupon=temp[0]
	return [lowestCoupon, lowestItem]

def getLowestPriceItem(pCode, item_):
	print("Browsing flyers for "+item_)
	lowestPrice=4096.0
	lowestCoupon={}
	couponList=lib['LeilaUy.ezyfoods'](postalCode=pCode, item=item_)
	for cp in couponList:
		if not((cp["name"]==None)or(cp["current_price"]==None)):
			if (item_ in str.lower(cp["name"])) and (cp["current_price"]<lowestPrice):
				lowestPrice=cp["current_price"]
				lowestCoupon=cp
	scannedItems[item_]=[lowestCoupon, lowestPrice]
	return [lowestCoupon, lowestPrice]

def gottems_to_needems(gottem_str,url_lst) -> str:
	str.lower(gottem_str)
	full_recipe_info = query_pull(gottem_str)
	main_recipe_url = full_recipe_info[0]['url']
	url_lst.append(main_recipe_url)
	detailed_recipe = AllRecipes.get(main_recipe_url)
	needem_lst = scan_for_missing(detailed_recipe, gottem_str)

	return needem_lst


def query_pull(must_haves) -> [int, slice]:
	query_options = {"wt":"", "ingIncl":must_haves,"sort":"re"}
	print(must_haves)
	query_result = AllRecipes.search(query_options)
	return query_result


def scan_for_missing(detailed_recipe, gottems) -> str:
	ing_lst = detailed_recipe['ingredients']

	crusty_ing = 0
	ing_needed = []

	last_digit = 0

	for i in range(len(ing_lst)):
		crusty_ing = str.lower(ing_lst[i])

		if "," in ing_lst[i]:
			crusty_ing = crusty_ing[:str.index(crusty_ing, ",")]

		last_digit = re.search('(\d)[\D]*$', crusty_ing)
		if(not last_digit==None):
			crusty_ing = crusty_ing[last_digit.start() + 2:]

		if ")" in crusty_ing:
			crusty_ing = crusty_ing[str.index(crusty_ing, ")") + 2:]

		if (" " in crusty_ing)and((crusty_ing[:str.index(crusty_ing, " ")] in measr_lst) \
				or (crusty_ing[:str.find(crusty_ing, "s ")]) in measr_lst):
			crusty_ing = crusty_ing[str.index(crusty_ing, " ") + 1:]

		if str.lower(crusty_ing) not in str.lower(gottems):
			ing_needed.append(str.lower(crusty_ing))
	print(ing_needed)
	return ing_needed

@app.route('/submit',methods=['POST'])
def main():
	print("--got here--")
	gottem_string=""
	url_list=[]
	couponList=[]
	pCode="M6G1A1"
	
	print(request.method)
	if request.method=='POST':
		if not request.form['PostalCode']=="":
			pCode=request.form['PostalCode']
		gottem_string=request.form['OwnedIngredients']
		if request.form['Submit']:
			print("running\n\n")
			execute(gottem_string,url_list,couponList,pCode)
			
	needs=gottems_to_needems(gottem_string,url_list)
	keepAlive("Beginning auxiliary item scanning...")
	for item in needs:
		temp=getLowestPriceItem(pCode, item)
		couponList.append(temp[0])
	#--TODO: Show recipe URL and coupon clippings on web!--
	for i in couponList:
		print(i)
	print(url_list[0])
	
	#execute(gottem_string,url_list,couponList,pCode)
	return 

def execute(gottem_string,url_list,couponList,pCode):
	temp=[]
	temp=getLowestPriceGoods(carbsList, pCode)
	#temp=getLowestPriceItem(pCode, "potatoes")
	gottem_string=temp[1]
	#gottem_string="potatoes"
	couponList.append(temp[0])
	print("carbs done")
	keepAlive("carbs done")
	temp=getLowestPriceGoods(fiberList, pCode)
	#temp=getLowestPriceItem(pCode, "carrot")
	if not temp[1] in gottem_string:
		gottem_string=gottem_string+", "+temp[1]
		couponList.append(temp[0])
	#gottem_string=gottem_string+", "+"carrot"
	print("fibers done")
	keepAlive("fibers done")
	render_template("RecipePlanner_Frontend2.html")
	temp=getLowestPriceGoods(proteinList, pCode)
	#temp=getLowestPriceItem(pCode, "black beans")
	if not temp[1] in gottem_string:
		gottem_string=gottem_string+", "+temp[1]
		couponList.append(temp[0])
	#gottem_string=gottem_string+", "+"black beans"
	print("protein done")
	keepAlive("protein done")
	temp=getLowestPriceGoods(fruitsVegList_Small, pCode)
	if not temp[1] in gottem_string:
		gottem_string=gottem_string+", "+temp[1]
		couponList.append(temp[0])
	print("vegetables done")
	keepAlive("vegetables done")
	return render_template("RecipePlanner_Frontend2.html")

@app.route('/',methods=['GET'])
def render():
	return render_template("RecipePlanner_Frontend.html")

def keepAlive(text):
	def alive(t):
		yield t
	return Response(stream_with_context(alive(text)))

if __name__=="__main__":
	main()
