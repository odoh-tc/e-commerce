from datetime import datetime
from sqlalchemy import DECIMAL, Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Enum
from sqlalchemy.orm import relationship
from database import Base
from schema.order import OrderStatus
from schema.user import UserRole



class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(25), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    is_verified = Column(Boolean, default=False)
    join_date = Column(DateTime, default=datetime.now)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.CUSTOMER)

    businesses = relationship('Business', back_populates="owner")
    orders = relationship('Order', back_populates="user")




class Business(Base):
    __tablename__ = 'businesses'

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String(100), nullable=False, unique=True)
    city = Column(String(100), nullable=False, default="Unspecified")
    region = Column(String(100), nullable=False, default="Unspecified")
    business_description = Column(String, nullable=True)
    logo = Column(String(100), nullable=False, default="default.jpg")
    owner_id = Column(Integer, ForeignKey('users.id'))

    owner = relationship('User', back_populates="businesses")
    products = relationship('Product', back_populates="business")



class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    category = Column(String(100), index=True)
    original_price = Column(DECIMAL(12, 2))
    new_price = Column(DECIMAL(12, 2))
    percentage_discount = Column(Integer)
    offer_expiration_date = Column(Date, default=datetime.now)
    product_image = Column(String(255), nullable=False, default='productdefault.jpg')
    date_published = Column(Date, default=datetime.now)
    quantity = Column(Integer, nullable=False, default=0)
    business_id = Column(Integer, ForeignKey('businesses.id'))

    business = relationship('Business', back_populates="products")

    def serialize(self):

        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "new_price": float(self.new_price),
            "percentage_discount": float(self.percentage_discount),
            "offer_expiration_date": self.offer_expiration_date.isoformat(),
            "product_image": self.product_image,
            "date_published": self.date_published.isoformat(),
            "quantity": self.quantity 
        }
    


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    quantity = Column(Integer, nullable=False, default=1)
    order_date = Column(DateTime, default=datetime.now)
    total_price = Column(DECIMAL(12, 2))
    status = Column(Enum(OrderStatus), default=OrderStatus.pending)

    product = relationship('Product')
    user = relationship('User', back_populates='orders')

    def serialize(self):
        return {
            "id": self.id,
            "product_id": self.product_id,
            "user_id": self.user_id,
            "quantity": self.quantity,
            "order_date": self.order_date.isoformat(),
            "total_price": float(self.total_price),
            "status": self.status.value
        }



































