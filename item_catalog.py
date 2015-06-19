from flask import Flask, request, url_for, redirect, render_template, jsonify
from item_database_config import Item, Category
from database_operations import DatabaseOperations

app = Flask(__name__)

db = DatabaseOperations()

# Static Pages


@app.route('/')
@app.route('/category/')
def showCategories():
    categories = db.getListOfCategories()
    latestItems = db.getLatestItems()
    return render_template('category_list.html', categories=categories,
                           items=latestItems)


@app.route('/category/<int:category_id>/')
def showItemsForCategory(category_id):
    categories = db.getListOfCategories()
    category = db.getCategoryBy(category_id)
    items = db.getItemsFor(category_id)
    return render_template('category.html', main_category=category,
                           categories=categories, items=items)


@app.route('/category/<int:category_id>/item/<int:item_id>/')
def showItem(category_id, item_id):
    categories = db.getListOfCategories()
    item = db.getItemBy(item_id)

    print item[0].name

    return render_template('item.html', categories=categories, item=item)


# CRUD Operations


@app.route('/category/<int:category_id>/addItem', methods=['GET', 'POST'])
def addItemToCategory(category_id):
    category = db.getCategoryBy(category_id)
    if request.method == 'POST':
        new_item = Item(name=request.form['name'], image_url=request.form['image_url'],
                        description=request.form['description'], category_id=category.id)
        db.addToDatabase(new_item)
        return redirect(url_for('showItemsForCategory', category_id=category.id))
    else:
        return render_template('addItem.html', category=category)


@app.route('/category/<int:category_id>/editItem/<int:item_id>/', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    item_to_edit = db.getItemBy(item_id)
    if request.method == 'POST':
        if request.form['name']:
            item_to_edit[0].name = request.form['name']
        if request.form['image_url']:
            item_to_edit[0].image_url = request.form['image_url']
        if request.form['description']:
            item_to_edit[0].description = request.form['description']
        db.addToDatabase(item_to_edit[0])
        return redirect(url_for('showItemsForCategory', category_id=item_to_edit[1].id))
    else:
        return render_template('editItem.html', category=item_to_edit[1], item=item_to_edit[0])


@app.route('/category/<int:category_id>/deleteItem/<int:item_id>/', methods=['GET', 'POST'])
def deleteItem(category_id, item_id):
    item_to_delete = db.getItemBy(item_id)
    if request.method == 'POST':
        db.deleteFromDatabase(item_to_delete[0])
        return redirect(url_for('showItemsForCategory', category_id=item_to_delete[1].id))
    else:
        return render_template('deleteItem.html', category=item_to_delete[1], item=item_to_delete[0])


# JSON API
@app.route('/categories/JSON/')
def categoriesJSON():
    categories = db.getListOfCategories()
    return jsonify(categories=[category.serialize for category in categories])


@app.route('/category/<int:category_id>/items/JSON/')
def itemsJSON(category_id):
    items = db.getItemsFor(category_id)
    return jsonify(items=[item.serialize for item in items])


if __name__ == "__main__":
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
