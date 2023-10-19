from fastapi import FastAPI, HTTPException
from typing import List
from fastapi import Path
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Float, Integer, String, Sequence
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from geopy.distance import geodesic

# Database setup
DATABASE_URL = "sqlite:///./address_book.db"
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class Address(Base):
    __tablename__ = "addresses"
    id = Column(Integer, Sequence("address_id_seq"), primary_key=True, index=True)
    name = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)

Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Pydantic model for address input with validation
class AddressCreate(BaseModel):
    name: str
    latitude: float
    longitude: float

# Pydantic model for address response
class AddressResponse(BaseModel):
    id: int
    name: str
    latitude: float
    longitude: float

# FastAPI setup
app = FastAPI()

# API endpoint to create an address
@app.post("/addresses/", response_model=AddressResponse)
def create_address(address: AddressCreate):
    db_address = Address(**address)
    with SessionLocal() as session:
        session.add(db_address)
        session.commit()
        session.refresh(db_address)
    return AddressResponse(**db_address.__dict__)

# API endpoint to update an address
@app.put("/addresses/{address_id}", response_model=AddressResponse)
def update_address(address_id: int, address: AddressCreate):
    with SessionLocal() as session:
        db_address = session.query(Address).filter(Address.id == address_id).first()
        if db_address:
            for key, value in address.items():
                setattr(db_address, key, value)
            session.commit()
            session.refresh(db_address)
            return AddressResponse(**db_address.__dict__)
        else:
            raise HTTPException(status_code=404, detail="Address not found")

# API endpoint to delete an address
@app.delete("/addresses/{address_id}", response_model=AddressResponse)
def delete_address(address_id: int):
    with SessionLocal() as session:
        db_address = session.query(Address).filter(Address.id == address_id).first()
        if db_address:
            session.delete(db_address)
            session.commit()
            return AddressResponse(**db_address.__dict__)
        else:
            raise HTTPException(status_code=404, detail="Address not found")

# API endpoint to get addresses within a given distance
@app.get("/addresses/", response_model=List[AddressResponse])
def get_addresses_within_distance(latitude: float, longitude: float, distance: float = 1.0):
    with SessionLocal() as session:
        all_addresses = session.query(Address).all()
        nearby_addresses = [
            AddressResponse(
                id=addr.id,
                name=addr.name,
                latitude=addr.latitude,
                longitude=addr.longitude
            ) for addr in all_addresses
            if geodesic((latitude, longitude), (addr.latitude, addr.longitude)).miles <= distance
        ]
        return nearby_addresses
# API endpoint to get a specific address by id
@app.get("/addresses/{address_id}", response_model=AddressResponse)
def get_address_by_id(address_id: int = Path(..., title="The ID of the address to retrieve")):
    with SessionLocal() as session:
        db_address = session.query(Address).filter(Address.id == address_id).first()
        if db_address:
            return AddressResponse(
                id=db_address.id,
                name=db_address.name,
                latitude=db_address.latitude,
                longitude=db_address.longitude
            )
        else:
            raise HTTPException(status_code=404, detail="Address not found")





