from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()  # Create a Base class

class Users(Base):
    __tablename__ = 'Users'  # Ensure table names match your database

    id = Column(Integer, primary_key=True)
    Username = Column(String, unique=True, nullable=False)
    Password = Column(String, nullable=False)
    Email = Column(String, nullable=False)
    ProfilePicture = Column(String)
    DateCreated = Column(String)

    # Relationship to Decks if needed
    decks = relationship("Decks", back_populates="user")


class Decks(Base):
    __tablename__ = 'Decks'  # Ensure table names match your database

    id = Column(Integer, primary_key=True)
    Deck = Column(String, nullable=False)
    UserDeckNum = Column(Integer, nullable=False)
    Owner = Column(Integer, ForeignKey('Users.id'))  # Ensure this matches Users table

    # Relationship back to Users
    user = relationship("Users", back_populates="decks")
