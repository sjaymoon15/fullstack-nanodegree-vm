from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
  __tablename__ = 'user'

  id = Column(Integer, primary_key=True)
  email = Column(String(250), nullable=False)

class Category(Base):
  __tablename__ = 'category'

  id = Column(Integer, primary_key=True)
  name = Column(String(250), nullable=False)
  items = relationship('Item', back_populates='category')

  @property
  def serialize(self):
    return {
      'id': self.id,
      'name': self.name
    }

class Item(Base):
  __tablename__ = 'item'

  id = Column(Integer, primary_key=True)
  title = Column(String(250), nullable=False)
  description = Column(String(250))
  cat_id = Column(Integer, ForeignKey('category.id'))
  category = relationship('Category', back_populates='items')

  @property
  def serialize(self):
    return {
      'id': self.id,
      'title': self.title,
      'description': self.description,
      'cat_id': self.cat_id
    }

engine = create_engine('sqlite:///categoryitem.db', connect_args={'check_same_thread': False})

Base.metadata.create_all(engine)

