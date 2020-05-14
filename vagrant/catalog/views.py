from models import Base, Category, Item, User
from flask import (Flask, jsonify, request, redirect,
                   url_for, abort, g, render_template, make_response)
from flask import session as login_session
import random
import string
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
import requests

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

engine = create_engine(
    'sqlite:///categoryitem.db',
    connect_args={
        'check_same_thread': False})

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)


@app.route('/categories/JSON')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[i.serialize for i in categories])


@app.route('/items/JSON')
def itemsJSON():
    items = session.query(Item).all()
    return jsonify(items=[i.serialize for i in items])


@app.route('/categories/<int:cat_id>/items/JSON')
def categoryJSON(cat_id):
    category = session.query(Category).filter_by(id=cat_id).one()
    items = session.query(Item).filter_by(cat_id=cat_id).all()
    return jsonify(
        category=category.serialize, items=[
            i.serialize for i in items])


@app.route('/categories/<int:cat_id>/items/<int:item_id>/JSON')
def showItemJSON(cat_id, item_id):
    category = session.query(Category).filter_by(id=cat_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(category=category.serialize, item=item.serialize)


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()
    login_session['email'] = data['email']

    newUserID = getUserID(login_session['email'])
    if newUserID is None:
        newUserID = createUser(login_session)
    login_session['user_id'] = newUserID

    return redirect(url_for('showCategories'))


def createUser(login_session):
    newUser = User(email=login_session['email'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except BaseException:
        return None


def isUserLoggedIn():
    if login_session is None or login_session.get('access_token') is None:
        return False
    return True


@app.route('/logout')
def logout():
    access_token = login_session.get('access_token')
    if access_token is None:
        return redirect(url_for('showCategories'))
    root_url = 'https://accounts.google.com/o/oauth2/revoke?token='
    url = root_url + login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['email']
        del login_session['user_id']
    return redirect(url_for('showCategories'))


@app.route('/')
@app.route('/categories/')
def showCategories():
    categories = session.query(Category).all()
    return render_template(
        'categories.html',
        categories=categories,
        isUserLoggedIn=isUserLoggedIn())


@app.route('/categories/<int:cat_id>/items')
def showCategory(cat_id):
    category = session.query(Category).filter_by(id=cat_id).one()
    items = session.query(Item).filter_by(cat_id=category.id).all()
    return render_template(
        'category.html',
        category=category,
        items=items,
        item_num=len(items))


@app.route('/categories/<int:cat_id>/items/<int:item_id>')
def showItem(cat_id, item_id):
    category = session.query(Category).filter_by(id=cat_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    isUserAuthor = False
    if isUserLoggedIn() == True and login_session['user_id'] == item.author_id:
        isUserAuthor = True
    return render_template(
        'item.html',
        category=category,
        item=item,
        isUserLoggedIn=isUserLoggedIn(),
        isUserAuthor=isUserAuthor)


@app.route(
    '/categories/<int:cat_id>/items/<int:item_id>/delete',
    methods=[
        'GET',
        'POST'])
def deleteItem(cat_id, item_id):
    category = session.query(Category).filter_by(id=cat_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    if isUserLoggedIn() == False or login_session['user_id'] != item.author_id:
        return redirect(url_for('showItem', cat_id=cat_id, item_id=item_id))
    if request.method == 'POST':
        session.delete(item)
        session.commit()
        return redirect(url_for('showCategory', cat_id=category.id))
    else:
        return render_template('deleteItem.html', category=category, item=item)


@app.route(
    '/categories/<int:cat_id>/items/<int:item_id>/edit/',
    methods=[
        'GET',
        'POST'])
def editItem(cat_id, item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    if isUserLoggedIn() == False or login_session['user_id'] != item.author_id:
        return redirect(url_for('showItem', cat_id=cat_id, item_id=item_id))
    if request.method == 'POST':
        if request.form['title']:
            item.title = request.form['title']
        if request.form['description']:
            item.description = request.form['description']
        if request.form['cat_id']:
            cat_id = request.form['cat_id']
            item.cat_id = cat_id
        session.add(item)
        session.commit()
        return redirect(url_for('showItem', cat_id=cat_id, item_id=item_id))
    else:
        category = session.query(Category).filter_by(id=cat_id).one()
        item = session.query(Item).filter_by(id=item_id).one()
        categories = session.query(Category).all()
        return render_template(
            'editItem.html',
            category=category,
            item=item,
            categories=categories)


@app.route('/categories/new/', methods=['GET', 'POST'])
def newCatagory():
    if request.method == 'POST':
        newCategory = Category(name=request.form['name'])
        session.add(newCategory)
        session.commit()
        return redirect(url_for('showCategories'))
    else:
        return render_template('newCategory.html')


@app.route('/items/new/', methods=['GET', 'POST'])
def newItem():
    if request.method == 'POST':
        newItem = Item(
            title=request.form['title'],
            description=request.form['description'],
            cat_id=request.form['cat_id'],
            author_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        return redirect(
            url_for(
                'showItem',
                item_id=newItem.id,
                cat_id=request.form['cat_id']))
    else:
        categories = session.query(Category).all()
        return render_template('newItem.html', categories=categories)


if __name__ == '__main__':
    app.secret_key = 'seriously_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
