import json
import random
import string
import httplib2
import requests
from flask import Flask, request, url_for, redirect, render_template, jsonify, session, make_response
from item_database_config import Item
from database_operations import DatabaseOperations
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

CLIENT_ID = json.loads(open('client_secret.json', 'r').read())['web']['client_id']

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


# Login Routes


@app.route('/login')
def showLogin():
    session['state'] = ''.join(random.choice(string.ascii_uppercase + string.digits)
                       for x in xrange(32))
    return render_template('login.html', STATE=session['state'])


@app.route('/gconnect', methods=['POST'])
def gconnect():
    print "Started GConnect."

    if request.args.get('state') != session['state']:
        response = make_response(json.dumps("Invalid authentication paramaters."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps('Token\'s user ID doesn\'t match given user ID.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print "Checking client ID."
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps('Token\'s client ID does not match.'), 401)
        response.headers['Content-Type'] = 'addToDatabase/json'
        return response
    stored_credentials = session.get('credentials')
    store_gplus_id = session.get('gplus_id')
    if stored_credentials is not None and gplus_id == store_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    session['credentials'] = access_token
    session['gplus_id'] = gplus_id

    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = answer.json()

    session['username'] = data['name']
    session['picture'] = data['picture']
    session['email'] = data['email']

    return "Login successful!"


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
