from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Category, Item, User

engine = create_engine('sqlite:///categoryitem.db', connect_args={'check_same_thread': False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# create dummy categories
category1 = Category(name="Soccer")
session.add(category1)
session.commit()

category2 = Category(name="Snowboarding")
session.add(category2)
session.commit()

# create dummy items for category1
item1 = Item(title="Jersey", description="Good Jersey", cat_id=category1.id)
session.add(item1)
session.commit()

item2 = Item(title="Soccer Cleats", description="Good Soccer Cleats", cat_id=category1.id)
session.add(item2)
session.commit()

item3 = Item(title="Two Shinguards", description="Good Shinguards", cat_id=category1.id)
session.add(item3)
session.commit()


# create dummy items for category2
item4 = Item(title="Snowboard", description="Good Snowboard", cat_id=category2.id)
session.add(item4)
session.commit()

item5 = Item(title="Goggles", description="Good Goggles", cat_id=category2.id)
session.add(item5)
session.commit()

print('Added categories and items')