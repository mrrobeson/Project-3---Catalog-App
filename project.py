from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine, distinct
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, CatalogItem

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

app = Flask(__name__)

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)
    #return "The state is %s" %login_session['state']


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: \
    150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route("/gdisconnect")
def gdisconnect():
    # Disconnect a connected user.
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'),
            401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Execute HTTP GET request to revoke current token.
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user session.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfuly disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # If the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for the given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

# catalog APIs
@app.route('/catalog/<int:catalog_id>/')
def catalogHome(catalog_id):
    catalogs = session.query(Catalog).all()
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    items = session.query(CatalogItem).filter_by(catalog_id=catalog_id)
    if 'username' not in login_session:
        return render_template('publiccategory.html', catalogs=catalogs, 
        catalog=catalog, items=items)
    else:
        return render_template('category.html', catalogs=catalogs, 
        catalog=catalog, items=items)
    #return render_template('catalog.html', catalog=catalog)


@app.route('/')
@app.route('/catalog/all')
@app.route('/catalogs/')
def showCatalogs():
    catalogs = session.query(Catalog).all()
    items = session.query(CatalogItem).all()

    if 'username' not in login_session:
        return render_template('publichome.html', catalogs=catalogs, 
            items=items)
    else:
        return render_template('home.html', catalogs=catalogs, items=items)


@app.route('/catalog/<int:catalog_id>/new/', methods=['GET','POST'])
def newItem(catalog_id):
    if 'username' not in login_session:
        return redirect('/login')

    if request.method == 'POST':
        newItem = CatalogItem(name = request.form['name'], 
            catalog_id = catalog_id)
        session.add(newItem)
        session.commit()
        flash('New item created!')
        return redirect(url_for('catalogHome', catalog_id = 
            catalog_id))
    else:
        return render_template('newitem.html', catalog_id = 
            catalog_id)

# @app.route('/catalog/new/', methods=['GET', 'POST'])
# this is not working, maybe this should be a new template showing all catalogs?
# def newCatalog():
#     if 'username' not in login_session:
#         return redirect('/login')

#     if request.method == 'POST':
#         newCatalog = Catalog(name = request.form['name'])
#         session.add(newCatalog)
#         session.commit()
#         flash('New catalog added')
#         return redirect(url_for('catalogHome', catalog_id = 
#             catalog_id))
#     else:
#         return render_template('newsport.html')


@app.route('/catalogs/<int:catalog_id>/<int:item_id>/edit', methods = ['GET', 'POST'])
def editItem(catalog_id, item_id):
    if 'username' not in login_session:
        return redirect(url_for('itemDetails'), catalog_id = 
            catalog_id, item_id = item_id)

    editedItem = session.query(CatalogItem).filter_by(id = item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        session.add(editedItem)
        session.commit()
        flash('Item Edited')
        return redirect(url_for('catalogHome', catalog_id = catalog_id))
    else:
        return render_template('edititem.html', catalog_id = 
            catalog_id, item_id = item_id, i = editedItem)

@app.route('/catalogs/<int:catalog_id>/<int:item_id>/details', methods = ['GET', 'POST'])
def itemDetails(catalog_id, item_id):
    itemToShow = session.query(CatalogItem).filter_by(id = item_id).one()
    if 'username' not in login_session:
        return render_template('publicitemdetails.html', catalog_id = 
            catalog_id, item_id = item_id, i = itemToShow)
    else:
        return render_template('itemdetails.html', catalog_id = 
            catalog_id, item_id = item_id, i = itemToShow)

# Task 3: Create a route for deleteCatalogItem function here

@app.route('/catalog/<int:catalog_id>/<int:item_id>/delete/', methods = 
    ['GET', 'POST'])
def deleteItem(catalog_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
            
    deletedItem = session.query(CatalogItem).filter_by(id = item_id).one()
    if request.method == 'POST':
        session.delete(deletedItem)
        session.commit()

        return redirect(url_for('catalogHome', catalog_id = catalog_id))
    else:
        return render_template('deleteitem.html', catalog_id = 
            catalog_id, item_id = item_id, item = deletedItem)

@app.route('/catalog/JSON')
def catalogHomeJSON():
    catalog = session.query(Catalog).all()
    items = session.query(CatalogItem).all()
    return jsonify(CatalogItems=[i.serialize for i in items])


@app.route('/catalog/<int:catalog_id>/item/JSON')
def catalogHomeJSON(catalog_id):
    catalog = session.query(Catalog).filter_by(id = 
        catalog_id).one()
    items = session.query(CatalogItem).filter_by(catalog_id=
        catalog_id).all()
    return jsonify(CatalogItems=[i.serialize for i in items])

@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/JSON/')
def catalogItemJSON(catalog_id, item_id):
    catalog = session.query(Catalog).filter_by(id = 
        catalog_id).one()
    item = session.query(CatalogItem).filter_by(id = item_id).one()
    return jsonify(CatalogItem=[item.serialize])


# @app.route('/')
# def showcatalogs(catalog_id):

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)