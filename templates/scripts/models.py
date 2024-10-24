from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()  # Create a Base class

class Users(Base):
    __tablename__ = 'Users'  # Ensure table names match your database

    Id = Column(Integer, primary_key=True, autoincrement=True)
    Username = Column(String, unique=True, nullable=False)
    Password = Column(String, nullable=False)
    Email = Column(String, unique=True, nullable=False)
    DateCreated = Column(DateTime, nullable=False)
    Decks = Column(Text, nullable=True)
    CardsUnlocked = Column(Text, nullable=True)
    ProfilePicture = Column(String, nullable=True)


    # Relationship to Decks if needed
    decks = relationship("Decks", back_populates="user")


class Decks(Base):
    __tablename__ = 'Decks'  # Ensure table names match your database

    DeckId = Column(Integer, primary_key=True)
    Owner = Column(String, nullable=False)
    UserDeckNum = Column(Integer, nullable=False)
    Deck = Column(Integer, ForeignKey('Users.Id'))  # Ensure this matches Users table

    # Relationship back to Users
    user = relationship("Users", back_populates="decks")
