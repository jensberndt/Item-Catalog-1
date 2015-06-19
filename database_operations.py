from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from item_database_config import Base, Category, Item


engine = create_engine('sqlite:///item_catalog.db')
Base.metadata.bind = engine
database_session = sessionmaker(bind=engine)
session = database_session()


class DatabaseOperations:

    def getCategoryBy(self, category_id):
        print category_id
        print Category.id
        print Category.id == category_id
        return session.query(Category).filter_by(id=category_id).one()

    def getListOfCategories(self):
        return session.query(Category).all()

    def getItemBy(self, item_id):
        return session.query(Item, Category.name).filter_by(id=item_id).join(Category).one()

    def getItemsFor(self, category_id):
        return session.query(Item).filter_by(category_id=category_id).all()

    def getLatestItems(self):
        return session.query(Item).limit(10)

    def addToDatabase(self, new_or_updated_object):
        session.add(new_or_updated_object)
        session.commit()
        return

    def deleteFromDatabase(self, item_id):
        item_to_delete = session.query(Item).filter_by(id=item_id).one()
        session.delete(item_to_delete)
        session.commit()
        return
