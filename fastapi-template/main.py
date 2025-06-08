from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime, timedelta, timezone
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Fitness Studio Booking API")

# IST timezone
IST = timezone(timedelta(hours=5, minutes=30))

# In-memory data
class ClassItem(BaseModel):
    id: int
    name: str
    datetime_ist: datetime
    instructor: str
    available_slots: int

class Booking(BaseModel):
    class_id: int
    client_name: str = Field(..., min_length=1)
    client_email: EmailStr

# Seed data
classes = [
    ClassItem(id=1, name="Yoga", datetime_ist=datetime(2025, 6, 10, 8, 0, tzinfo=IST), instructor="Amit", available_slots=5),
    ClassItem(id=2, name="Zumba", datetime_ist=datetime(2025, 6, 10, 10, 0, tzinfo=IST), instructor="Priya", available_slots=3),
    ClassItem(id=3, name="HIIT", datetime_ist=datetime(2025, 6, 11, 7, 0, tzinfo=IST), instructor="Rahul", available_slots=4),
]

bookings: List[dict] = []

@app.get("/classes", summary="List all upcoming fitness classes")
def get_classes(timezone_offset: Optional[int] = Query(330, description="Timezone offset in minutes from UTC (default IST=330)")):
    """
    Returns all classes. Converts class times to the requested timezone.
    """
    tz = timezone(timedelta(minutes=timezone_offset))
    result = []
    for c in classes:
        local_time = c.datetime_ist.astimezone(tz)
        result.append({
            "id": c.id,
            "name": c.name,
            "datetime": local_time.isoformat(),
            "instructor": c.instructor,
            "available_slots": c.available_slots
        })
    return result

@app.post("/book", summary="Book a spot in a class")
def book_class(booking: Booking):
    # Find the class
    class_obj = next((c for c in classes if c.id == booking.class_id), None)
    if not class_obj:
        logging.warning(f"Booking failed: Class ID {booking.class_id} not found.")
        raise HTTPException(status_code=404, detail="Class not found")
    if class_obj.available_slots <= 0:
        logging.warning(f"Booking failed: No slots left for class {class_obj.name}.")
        raise HTTPException(status_code=400, detail="No slots available")
    # Check for duplicate booking
    for b in bookings:
        if b["class_id"] == booking.class_id and b["client_email"] == booking.client_email:
            logging.warning(f"Booking failed: Duplicate booking for {booking.client_email} in class {class_obj.name}.")
            raise HTTPException(status_code=400, detail="Already booked this class")
    # Book
    class_obj.available_slots -= 1
    bookings.append(booking.dict())
    logging.info(f"Booking successful: {booking.client_email} booked {class_obj.name}.")
    return {"message": "Booking successful", "class": class_obj.name, "client": booking.client_name}

@app.get("/bookings", summary="Get all bookings for a client")
def get_bookings(client_email: EmailStr = Query(..., description="Client email address")):
    user_bookings = [b for b in bookings if b["client_email"] == client_email]
    return {"bookings": user_bookings}

# Sample root endpoint
@app.get("/")
def root():
    return {"message": "Welcome to the Fitness Studio Booking API!"}