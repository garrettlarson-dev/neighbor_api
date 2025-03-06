import os
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import json
import uvicorn

app = FastAPI()

class Item(BaseModel):
    length: int
    quantity: int

with open('listings.json', 'r') as file:
    listings = json.load(file)

@app.post("/")
async def handle_request(items: List[Item]):
    return process_items(items)

def process_items(items: List[Item]):
    print("process_items function called")
    response = []

    # Calculate total required space for each item
    required_space = []
    total_car_sq_ft = 0
    for item in items:
        car_sq_ft = item.length * 10 
        required_space.extend([car_sq_ft] * item.quantity)
        total_car_sq_ft += car_sq_ft * item.quantity

    print("Required space (sq ft):", required_space)

    print("Starting to check if a single listing can cover the total required space")
    # Check if a single listing can cover the total required space
    for listing in listings:
        listing_sq_ft = listing['length'] * listing['width']
        if listing_sq_ft >= total_car_sq_ft:
            print(f"Single listing {listing['id']} can cover the demand")
            # If a single listing can cover the demand, add it to the response
            response.append({
                'location_id': listing['location_id'],
                'listing_ids': [listing['id']],
                'total_price_in_cents': listing['price_in_cents'],
                'more_listings_available': False
            })

    print("No single listing can cover the demand, proceeding with location-based logic")
    # If no single listing can cover the demand, proceed with existing logic
    # Find suitable listings for each location
    location_dict = {}
    for listing in listings:
        loc_id = listing['location_id']
        if loc_id not in location_dict:
            location_dict[loc_id] = {'listings': [], 'total_price_in_cents': 0}
        
        location_dict[loc_id]['listings'].append(listing)

    print("Evaluating each location independently")
    location_best_options = {}

    # Evaluate each location independently
    for loc_id, data in location_dict.items():
        available_listings = data['listings']
        # Sort listings by square footage (length * width) in descending order
        available_listings.sort(key=lambda x: x['length'] * x['width'], reverse=True)

        # Check if a single listing can accommodate all cars for this location
        best_single_listing = None
        for listing in available_listings:
            listing_sq_ft = listing['length'] * listing['width']
            if listing_sq_ft >= total_car_sq_ft:
                if best_single_listing is None or listing['price_in_cents'] < best_single_listing['price_in_cents']:
                    best_single_listing = listing

        if best_single_listing:
            print(f"Best single listing at location {loc_id} can cover the demand")
            # Add the best single listing to the location's best options
            location_best_options[loc_id] = {
                'location_id': loc_id,
                'listing_ids': [best_single_listing['id']],
                'total_price_in_cents': best_single_listing['price_in_cents'],
                'more_listings_available': len(available_listings) > 1
            }
            continue

        print(f"Trying to fit all required spaces at location {loc_id}")
        used_listings = []
        total_price = 0
        remaining_space = required_space.copy()

        for listing in available_listings:
            # Calculate how many cars can fit in this listing
            listing_sq_ft = listing['length'] * listing['width']
            max_cars_fit = listing_sq_ft // (10 * 40)  # Assuming each car is 10x40

            # Fit as many cars as possible into this listing
            while remaining_space and max_cars_fit > 0:
                # Ensure the car's length is less than or equal to the listing's length
                if remaining_space[0] <= listing['length'] * 10:
                    used_listings.append(listing['id'])
                    total_price += listing['price_in_cents']
                    remaining_space.pop(0)
                    max_cars_fit -= 1
                else:
                    break

            if not remaining_space:
                break

        # Only add to location's best options if all required spaces are accommodated
        if not remaining_space:  # If all required spaces are accommodated
            more_listings_available = len(available_listings) > len(used_listings)
            location_best_options[loc_id] = {
                "location_id": loc_id,
                "listing_ids": used_listings,
                "total_price_in_cents": total_price,
                "more_listings_available": more_listings_available
            }

    # Convert location_best_options to a list for sorting and response
    response = list(location_best_options.values())

    print("Sorting the response by total price in cents")
    # Sort the response by total price in cents, ascending
    response.sort(key=lambda x: (x['total_price_in_cents'], len(x['listing_ids'])))

    # Print the response with better formatting
    for res in response:
        print(f"Location ID: {res['location_id']}")
        print(f"Listing IDs: {res['listing_ids']}")
        print(f"Total Price in Cents: {res['total_price_in_cents']}")
        print(f"More Listings Available: {res['more_listings_available']}")
        print("\n")

    # Print the total number of locations
    total_locations = len(location_dict)
    print(f"Total Locations: {total_locations}")

    # Print the number of locations considered for storing the cars
    considered_locations = len(response)
    print(f"Considered Locations: {considered_locations}")

    return response

# Function to calculate and display total length and width for each location
def calculate_totals_by_location(listings):
    location_totals = {}
    for listing in listings:
        loc_id = listing['location_id']
        if loc_id not in location_totals:
            location_totals[loc_id] = {'total_length': 0, 'total_width': 0}
        location_totals[loc_id]['total_length'] += listing['length']
        location_totals[loc_id]['total_width'] += listing['width']

    for loc_id, totals in location_totals.items():
        print(f"Location ID: {loc_id}")
        print(f"Total Length: {totals['total_length']}")
        print(f"Total Width: {totals['total_width']}")
        print("\n")  

def count_locations_for_car_length(car_length: int, location_dict) -> int:
    count = 0
    for loc_id, data in location_dict.items():
        for listing in data['listings']:
            if listing['length'] >= car_length:
                count += 1
                break 
    return count

def main():
    test_items = [
        {
            "length": 10,
            "quantity": 1
        },
        {
            "length": 20,
            "quantity": 2
        },
        {
            "length": 25,
            "quantity": 1
        }
    ]
    print("Test items:", test_items)  
    result = process_items([Item(**item) for item in test_items])
    print("Result:", result)  

    # calculate_totals_by_location(listings)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)