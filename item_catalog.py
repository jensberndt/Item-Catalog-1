from flask import Flask, request, url_for, redirect, render_template
from item_database_config import Item, Category
from database_operations import DatabaseOperations

app = Flask(__name__)

db = DatabaseOperations()

# Page with of our categories and the latest items.


@app.route('/')
@app.route('/category/')
def showCategories():
    categories = db.getListOfCategories()
    latestItems = db.getLatestItems()
    return render_template('category_list.html', categories=categories,
                           items=latestItems)


# Page with all items for a specific category


@app.route('/category/<int:category_id>/')
def showItemsForCategory(category_id):
    categories = db.getListOfCategories()
    category = db.getCategoryBy(category_id)
    items = db.getItemsFor(category_id)
    return render_template('category.html', main_category=category,
                           categories=categories, items=items)

# Page for a specific item.


@app.route('/category/<int:category_id>/item/<int:item_id>/')
def showItem(category_id, item_id):
    categories = db.getListOfCategories()
    item = db.getItemBy(item_id)

    print item[0].name

    return render_template('item.html', categories=categories, item=item)


# Add a new category


@app.route('/category/add', methods=['GET', 'POST'])
def addCategory():
    if request.method == 'POST':
        new_category = Category(name=request.form['name'], image_url=request.form['image_url'])
        db.addToDatabase(new_category)
        return redirect(url_for(showCategories))
    else:
        pass

# Edit a category


@app.route('/category/edit/<int:category_id>', methods=['GET', 'POST'])
def editCategory(category_id):
    updated_category = db.getCategoryBy(category_id)
    if request.method == 'POST':
        if request.form['name']:
            updated_category.name = request.form['name']
        if request.form['image_url']:
            updated_category.image_url = request.form['image_url']
        db.addToDatabase(updated_category)
        return redirect(showCategories)
    else:
        pass


# Add a new item in a category


@app.route('/category/<int:category_id>/addItem', methods=['GET', 'POST'])
def addItemToCategory(category_id):
    if request.method == 'POST':
        new_item = Item(name=request.form['name'], image_url=request.form['image_url'],
                        description=request.form['description'], category_id=category_id)
        db.addToDatabase(new_item)
        return redirect(showItemsForCategory(category_id))
    else:
        pass


# Edit an item


@app.route('/category/<int:category_id>/editItem/<int:item_id>', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    if request.method == 'POST':
        item_to_edit = db.getItemBy(item_id)
        if request.form['name']:
            item_to_edit.name = request.form['name']
        if request.form['image_url']:
            item_to_edit.image_url = request.form['image_url']
        if request.form['description']:
            item_to_edit.description = request.form['description']
        db.addToDatabase(item_to_edit)
        return redirect(showItemsForCategory(category_id))
    else:
        pass


# Delete an item


@app.route('/category/<int:category_id>/deleteItem<int:item_id>', methods=['GET', 'POST'])
def deleteItem(item_id):
    if request.method == 'POST':
        db.deleteItem(item_id)
        return
    else:
        pass


if __name__ == "__main__":
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
