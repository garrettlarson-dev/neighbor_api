import json

# Function to load and output the contents of listings.json

def load_and_output_listings(file_path):
    with open(file_path, 'r') as file:
        listings = json.load(file)
        for listing in listings:
            print(listing)

# Example usage
load_and_output_listings('listings.json') 