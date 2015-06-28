from item_database_config import Category
from database_operations import DatabaseOperations

db = DatabaseOperations()
new_categories = [Category(name='Crustaceans'),
                  Category(name='Corals'),
                  Category(name='Marine Mammals'),
                  Category(name='Fish'),
                  Category(name='Birds'),
                  Category(name='Reptiles'),
                  Category(name='Sharks & Rays')]
for new_category in new_categories:
    db.addToDatabase(new_category)
