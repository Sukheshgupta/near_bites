from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class Restaurant(Base):
    __tablename__ = "restaurants"

    place_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    address = Column(String)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    rating = Column(Float, default=0.0)
    price_level = Column(Integer, default=1)
    cuisine_tags = Column(String, default="")  # comma-separated
    is_open = Column(Boolean, default=True)
    phone = Column(String, default="")
    photo_url = Column(String, default="")
    cached_at = Column(DateTime, default=datetime.utcnow)

    dishes = relationship("Dish", back_populates="restaurant", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="restaurant", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "place_id": self.place_id,
            "name": self.name,
            "address": self.address,
            "lat": self.lat,
            "lng": self.lng,
            "rating": self.rating,
            "price_level": self.price_level,
            "cuisine_tags": [t.strip() for t in self.cuisine_tags.split(",") if t.strip()],
            "is_open": self.is_open,
            "phone": self.phone,
            "photo_url": self.photo_url,
        }


class Dish(Base):
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_place_id = Column(String, ForeignKey("restaurants.place_id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    price = Column(Float, nullable=False)
    category = Column(String, default="Other")
    normalized_category = Column(String, default="Other")
    is_veg = Column(Boolean, default=False)
    is_vegan = Column(Boolean, default=False)
    cached_at = Column(DateTime, default=datetime.utcnow)

    restaurant = relationship("Restaurant", back_populates="dishes")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "category": self.category,
            "normalized_category": self.normalized_category,
            "is_veg": self.is_veg,
            "is_vegan": self.is_vegan,
        }


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, autoincrement=True)
    restaurant_place_id = Column(String, ForeignKey("restaurants.place_id", ondelete="CASCADE"), nullable=False)
    reviewer_name = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    restaurant = relationship("Restaurant", back_populates="reviews")

    def to_dict(self):
        return {
            "id": self.id,
            "restaurant_place_id": self.restaurant_place_id,
            "reviewer_name": self.reviewer_name,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def get_engine(db_url="sqlite:///./nearbites.db"):
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    return engine


def get_session_factory(engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)
