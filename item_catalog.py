import json
import httplib2
import requests
import string
import random
from flask import Flask, url_for, session, redirect, request, render_template, jsonify, make_response
from item_database_config import Item
from database_operations import DatabaseOperations
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError


app = Flask(__name__)

db = DatabaseOperations()
credentials = {}
token_info = {}

CLIENT_ID = json.loads(open('client_secret.json', 'r').read())['web']['client_id']


# Static Pages
@app.route('/')
@app.route('/category/')
def showCategories():
    categories = db.getListOfCategories()
    latestItems = db.getLatestItems()
    for item in session:
        print session[item]
    return render_template('category_list.html', categories=categories,
                           items=latestItems, user_id=session.get('user_id'))


@app.route('/category/<int:category_id>/')
def showItemsForCategory(category_id):
    categories = db.getListOfCategories()
    category = db.getCategoryBy(category_id)
    items = db.getItemsFor(category_id)
    return render_template('category.html', main_category=category,
                           categories=categories, items=items, user_id=session.get('user_id'))


@app.route('/category/<int:category_id>/item/<int:item_id>/')
def showItem(category_id, item_id):
    categories = db.getListOfCategories()
    item = db.getItemBy(item_id)
    return render_template('item.html', categories=categories, item=item, main_category=category_id, user_id=session.get('user_id'))


# CRUD Operations
@app.route('/category/<int:category_id>/addItem', methods=['GET', 'POST'])
def addItemToCategory(category_id):
    if 'name' not in session:
        return redirect('/login')
    else:
        category = db.getCategoryBy(category_id)
        if request.method == 'POST':
            print request.form['state']
            print session['state']
            if checkIfClientAuthorizedWith(request.form['state']) is False:
                return responseWith('Invalid authorization paramaters.', 401)
            new_item = Item(name=request.form['name'], image_url=request.form['image_url'],
                            description=request.form['description'], category_id=category.id,
                            creator_id=session['user_id'])
            db.addToDatabase(new_item)
            return redirect(url_for('showItemsForCategory', category_id=category.id))
        else:
            return render_template('addItem.html', category=category, STATE=session.get('state'))


@app.route('/category/<int:category_id>/editItem/<int:item_id>/', methods=['GET', 'POST'])
def editItem(category_id, item_id):
    if 'name' not in session:
        return redirect('/login')
    item_to_edit = db.getItemBy(item_id)
    if request.method == 'POST':
        if checkIfClientAuthorizedWith(request.form['state']) is False:
            return responseWith('Invalid authorization paramaters.', 401)
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
    if 'name' not in session:
        return redirect('/login')
    item_to_delete = db.getItemBy(item_id)
    if request.method == 'POST':
        if checkIfClientAuthorizedWith(request.form['state']) is False:
            return responseWith('Invalid authorization paramaters.', 401)
        db.deleteFromDatabase(item_to_delete[0])
        return redirect(url_for('showItemsForCategory', category_id=item_to_delete[1].id))
    else:
        return render_template('deleteItem.html', category=item_to_delete[1], item=item_to_delete[0], STATE=session.get('state'))


# Login Routes
@app.route('/login')
def showLogin():
    session['state'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    return render_template('login.html', STATE=session.get('state'))


@app.route('/gconnect', methods=['POST'])
def gconnect():
    return checkIfAuthorizedWith(request)


@app.route('/gdisconnect')
def gdisconnect():
    return logout()


# JSON API
@app.route('/categories/JSON/')
def categoriesJSON():
    categories = db.getListOfCategories()
    return jsonify(categories=[category.serialize for category in categories])


@app.route('/category/<int:category_id>/items/JSON/')
def itemsJSON(category_id):
    items = db.getItemsFor(category_id)
    return jsonify(items=[item.serialize for item in items])


# oAuth Flow and Error Checking
def responseWith(message, response_code):
    response = make_response(json.dumps(message), response_code)
    response.headers['Content-Type'] = 'application/json'
    return response


def checkIfClientAuthorizedWith(client_state):
    return client_state == session['state']


def checkIfAuthorizedWith(client_request):
    if not checkIfClientAuthorizedWith(client_request.args.get('state')):
        return responseWith('Invalid authentication paramaters.', 401)
    else:
        request_data = client_request.data
        return tryOAuthFlow(request_data)


def tryOAuthFlow(request_data):
    try:
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        setCredentials(oauth_flow.step2_exchange(request_data))
        return validateAccess()
    except FlowExchangeError:
        return responseWith('Failed to upgrade the authorization code.', 401)


def validateAccess():
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % credentials.access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        return responseWith(result.get('error'), 500)
    else:
        setTokenInfo(result)
    return checkIfTokenInfoAndCrednetialForSameUser()


def checkIfTokenInfoAndCrednetialForSameUser():
    if token_info['user_id'] != credentials.id_token['sub']:
        return responseWith('Token\'s user ID doesn\'t match given user ID.', 401)
    else:
        return checkIfTokenIssuedToClient()


def checkIfTokenIssuedToClient():
    if token_info['issued_to'] != CLIENT_ID:
        return responseWith('Token\'s client ID does not match.', 401)
    else:
        return checkIfUserLoggedIn()


def checkIfUserLoggedIn():
    if session.get('credentials') is not None and credentials.id_token['sub'] == session.get('gplus_id'):
        return responseWith('Current user is already connected.', 200)
    else:
        return getUserInfoAndCreateSession()


def getUserInfoAndCreateSession():
    url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    response = requests.get(url, params=params)
    data = response.json()
    session['credentials'] = credentials.access_token
    session['gplus_id'] = credentials.id_token['sub']
    session['name'] = data['name']
    session['picture'] = data['picture']
    session['email'] = data['email']
    session['user_id'] = db.getUserBy(session).id
    return responseWith('User successfully connected.', 200)


def logout():
    if session.get('credentials')is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % session.get('credentials')
    print url
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == 200:
        del session['credentials']
        del session['gplus_id']
        del session['name']
        del session['picture']
        del session['email']
        del session['user_id']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# Setters for global variables
def setCredentials(new_credential):
    global credentials
    credentials = new_credential


def setTokenInfo(token):
    global token_info
    token_info = token


if __name__ == "__main__":
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
