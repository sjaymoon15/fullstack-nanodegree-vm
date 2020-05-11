from models import Base, Category, Item
from flask import Flask, jsonify, request, redirect, url_for, abort, g, render_template
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

import json

engine = create_engine('sqlite:///categoryitem.db', connect_args={'check_same_thread': False})

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
  # items = session.query(Item).filter_by(cat_id=cat_id).all()
  # category['items'] = [i.serialize for i in items]
  return jsonify(category)

@app.route('/categories/<int:cat_id>/items/<int:item_id>/JSON')
def showItemJSON(cat_id, item_id):
  category = session.query(Category).filter_by(id=cat_id).one()
  item = session.query(Item).filter_by(id=item_id).one()
  return jsonify({'id': item.id, 'title': item.title, 'description': item.description, 'category_id': item.cat_id})


@app.route('/')
@app.route('/categories/')
def showCategories():
  categories = session.query(Category).all()
  return render_template('categories.html', categories=categories)

@app.route('/categories/<int:cat_id>/items')
def showCategory(cat_id):
  category = session.query(Category).filter_by(id=cat_id).one()
  items = session.query(Item).filter_by(cat_id=category.id).all()
  return render_template('category.html', category=category, items=items, item_num=len(items))

@app.route('/categories/<int:cat_id>/items/<int:item_id>')
def showItem(cat_id, item_id):
  category = session.query(Category).filter_by(id=cat_id).one()
  item = session.query(Item).filter_by(id=item_id).one()
  return render_template('item.html', category=category, item=item)

@app.route('/categories/<int:cat_id>/items/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(cat_id, item_id):
  category = session.query(Category).filter_by(id=cat_id).one()
  item = session.query(Item).filter_by(id=item_id).one()
  if request.method == 'POST':
    session.delete(item)
    session.commit()
    return redirect(url_for('showCategory', cat_id=category.id))
  else:
    return render_template('deleteItem.html', category=category, item=item)

@app.route('/categories/<int:cat_id>/items/<int:item_id>/edit/', methods=['GET','POST'])
def editItem(cat_id, item_id):
  item = session.query(Item).filter_by(id=item_id).one()
  if request.method == 'POST':
    if request.form['title']:
      item.title = request.form['title']
    if request.form['description']:
      item.description = request.form['description']
    if request.form['cat_id']:
      cat_id = request.form['cat_id']
      category = session.query(Category).filter_by(id=cat_id).one()
      item.cat_id = cat_id
      item.category = category
    session.add(item)
    session.commit()
    return redirect(url_for('showItem', cat_id=cat_id, item_id=item_id))
  else:
    category = session.query(Category).filter_by(id=cat_id).one()
    item = session.query(Item).filter_by(id=item_id).one()
    categories = session.query(Category).all()
    return render_template('editItem.html', category=category, item=item, categories=categories)

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
    newItem = Item(title=request.form['title'], description=request.form['description'], cat_id=request.form['cat_id'])
    session.add(newItem)
    session.commit()
    return redirect(url_for('showItem', item_id=newItem.id, cat_id=request.form['cat_id']))
  else:
    categories = session.query(Category).all()
    return render_template('newItem.html', categories=categories)

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
