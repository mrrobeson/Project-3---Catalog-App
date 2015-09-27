from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem

engine = create_engine('sqlite:///restaurantmenu.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()
myFirstRestaurant = Restaurant(name = "Pizza Palace")

cheesepizza = MenuItem(name = "Pepperoni Pizza", description = 
	"Made with all natural ingredients and sausage", course = 
	"Entree", price = "$9.99", restaurant = myFirstRestaurant)
session.add(cheesepizza)
session.commit()