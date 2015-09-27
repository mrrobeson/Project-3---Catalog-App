from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Catalog, Base, CatalogItem

engine = create_engine('sqlite:///catalogwithusers.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

User1 = User(name="Robo Barista", email="tinnyTim@udacity.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(User1)
session.commit()

# Equipment for Swimmmer's Weekly
catalog1 = Catalog(name="Swim and Dive")

session.add(catalog1)
session.commit()

catalogItem1 = CatalogItem(name="Sprint Goggles", 
                     description="Low profile for new personal records.",
                     catalog=catalog1)

session.add(catalogItem1)
session.commit()

catalogItem2 = CatalogItem(name="Squeegie Towel", 
                     description="Dry, squeeze, and repeat.",
                     catalog=catalog1)

session.add(catalogItem2)
session.commit()

catalogItem3 = CatalogItem(name="Jammer", 
                     description="The Speedo for the self conscious.",
                     catalog=catalog1)

session.add(catalogItem3)
session.commit()

catalogItem4 = CatalogItem(name="Swim Cap", 
                     description="Save your hair with this fashionable latex look",
                     catalog=catalog1)

session.add(catalogItem4)
session.commit()


# Menu for Super Stir Fry
catalog2 = Catalog(name="Crossfit")

session.add(catalog2)
session.commit()


catalogItem1 = CatalogItem(name="High Socks", 
                     description="The tie-die way to accent your fabulous shins.",
                     catalog=catalog2)

session.add(catalogItem1)
session.commit()

catalogItem2 = CatalogItem(name="Bearing Bar", 
                     description="Feel free to drop it from overhead with 10 lb plates.",
                     catalog=catalog2)

session.add(catalogItem2)
session.commit()

catalogItem3 = CatalogItem(name="Weight Belt", 
                     description="On and off at the door.",
                     catalog=catalog2)

session.add(catalogItem3)
session.commit()

catalogItem4 = CatalogItem(name="Knee Sleeves", 
                     description="Please wash once a year whether needed or not.",
                     catalog=catalog2)

session.add(catalogItem4)
session.commit()

catalogItem5 = CatalogItem(name="Tights", 
                     description="Nothing says I snatch more than you like these do.",
                     catalog=catalog2)

session.add(catalogItem5)
session.commit()



print "added sports and equipment!"
