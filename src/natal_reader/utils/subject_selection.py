import json
import os
import googlemaps
from natal_reader.utils.constants import SUBJECT_DIR
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ANSI color codes
RED = "\033[91m"
RESET = "\033[0m" 

gmaps = googlemaps.Client(key=os.getenv("GMAPS_API_KEY"))

# Helper function to format display name from filename
def _format_display_name(filename):
    name_part = filename.stem
    return ' '.join(word.capitalize() for word in name_part.split('_'))

def get_date_of_birth():
    while True:
        try:
            year = int(input("Enter the year of birth: "))
            if year < 0 or year > datetime.now().year:
                raise ValueError
            break
        except ValueError:
            # Format error message in red
            print(f"{RED}Invalid year. Please enter a valid year between 0 and {datetime.now().year}.{RESET}")

    while True:
        try:
            month = int(input("Enter the month of birth (1-12): "))
            if month < 1 or month > 12:
                raise ValueError
            break
        except ValueError:
            # Format error message in red
            print(f"{RED}Invalid month. Please enter a valid month between 1 and 12.{RESET}")

    while True:
        try:
            day = int(input("Enter the day of birth (1-31): "))
            # Simplified date validation logic
            try:
                # Check if the date is valid for the given month/year
                datetime(year, month, day) 
            except ValueError as e:
                 # Format error message in red
                print(f"{RED}Invalid day: {e}. Please enter a valid day.{RESET}")
                continue # Ask again
            break # Exit loop if date is valid
        except ValueError: # Catch potential int conversion errors
             # Format error message in red
            print(f"{RED}Invalid input. Please enter a number for the day.{RESET}")
            
    return year, month, day
    

def get_time_of_birth():
    while True:
        try:
            time = input("Enter the time of birth in 24-hour format (e.g. 15:30 for 3:30pm): ")
            hour, minute = map(int, time.split(':'))
            if hour < 0 or hour > 23:
                raise ValueError
            if minute < 0 or minute > 59:
                raise ValueError
            break
        except ValueError:
             # Format error message in red
            print(f"{RED}Invalid time. Please enter a valid time in 24-hour format (e.g. 15:30 for 3:30pm).{RESET}")

    return hour, minute


def get_timezone(latitude, longitude):
    timestamp = datetime.now().timestamp()
    try:
        timezone_result = gmaps.timezone((latitude, longitude), timestamp=timestamp)
        if timezone_result and 'timeZoneId' in timezone_result:
            timezone_str = timezone_result['timeZoneId']
        else:
             # Format warning message in red (optional, could be yellow/normal)
            print(f"{RED}Warning: Could not determine timezone via Google API.{RESET}")
            timezone_str = None
    except Exception as e:
        # Format error message in red
        print(f"{RED}Error getting timezone from Google API: {e}{RESET}")
        timezone_str = None # Or ask user? For now, setting to None.
    return timezone_str


def get_place_of_birth():
    while True:
        try:
            address = input("Enter the place of birth: ")
            geocode_result = gmaps.geocode(address)
            if not geocode_result:
                 # Format error message in red
                print(f"{RED}Invalid address. Could not geocode. Please enter a valid address.{RESET}")
                continue

            # Defensive coding: check structure before accessing
            if not isinstance(geocode_result, list) or len(geocode_result) == 0:
                 print(f"{RED}Unexpected geocode result format. Please try again.{RESET}")
                 continue
                 
            location = geocode_result[0].get('geometry', {}).get('location', {})
            if not location or 'lat' not in location or 'lng' not in location:
                 # Format error message in red
                print(f"{RED}Could not get coordinates for this address. Please try again.{RESET}")
                continue

            address_components = geocode_result[0].get('address_components', [])
            city = next((comp['long_name'] for comp in address_components if 'locality' in comp['types']), None)
            country = next((comp['long_name'] for comp in address_components if 'country' in comp['types']), None)

            # Handle cases where city or country might not be found
            if not city:
                print("Could not determine city from address components. Using address as fallback.")
                # Attempt to get a broader administrative area or use the formatted address
                city = next((comp['long_name'] for comp in address_components if 'administrative_area_level_1' in comp['types']), None)
                if not city:
                     city = geocode_result[0].get('formatted_address', address) # Fallback

            if not country:
                 print("Could not determine country from address components.")
                 # Maybe add a fallback or raise an error depending on requirements
                 country = "Unknown" # Placeholder

            return city, country, location['lat'], location['lng']
        except googlemaps.exceptions.ApiError as e:
             print(f"{RED}Google Maps API Error: {e}. Check API key and usage limits.{RESET}")
             # Decide if to retry or exit. For now, retrying.
        except Exception as e:
             # Format error message in red
            print(f"{RED}Error processing place of birth: {e}. Please try again.{RESET}")


def get_subject_data(subject_name=None):
    SUBJECT_DIR.mkdir(parents=True, exist_ok=True) # Ensure directory exists
    
    existing_subjects = list(SUBJECT_DIR.glob('*.json'))
    subject_map = {i + 1: subject_file for i, subject_file in enumerate(existing_subjects)}

    selected_subject_file = None

    if subject_map:
        print("Existing subjects:")
        for num, file_path in subject_map.items():
            display_name = _format_display_name(file_path)
            print(f"  {num} - {display_name}")
        
        prompt = "Enter the number of an existing subject, or enter a new name to create: "
    else:
        prompt = "No existing subjects found. Enter a name to create a new subject: "

    while True: # Loop until valid selection or new name
        user_input = input(prompt).strip()
        if user_input.isdigit():
            try:
                selection_num = int(user_input)
                if selection_num in subject_map:
                    selected_subject_file = subject_map[selection_num]
                    subject_name = _format_display_name(selected_subject_file) # Use formatted name
                    print(f"Selected existing subject: {subject_name}")
                    break 
                else:
                     # Format error message in red
                    print(f"{RED}Invalid number. Please select from the list.{RESET}")
            except ValueError:
                 # Format error message in red
                 # This case might not be reached due to isdigit(), but good practice
                print(f"{RED}Invalid input. Please enter a number or a name.{RESET}")
        elif user_input: # Treat as a new name
            subject_name = user_input
            subject_name_formatted = subject_name.lower().replace(" ", "_")
            selected_subject_file = SUBJECT_DIR / f"{subject_name_formatted}.json"
            if selected_subject_file.exists():
                 # Format error message in red
                print(f"{RED}A subject with this name ('{subject_name_formatted}.json') already exists. Please choose a different name or select the existing entry by number if listed.{RESET}")
                # Re-prompt by continuing the loop
            else:
                print(f"Creating new subject: {subject_name}")
                # Pass formatted name for file, original for display/data
                create_subject_data(subject_name_formatted, subject_name) 
                break # Exit loop after creation attempt
        else:
             # Format error message in red
             print(f"{RED}Input cannot be empty. Please enter a number or a name.{RESET}")


    # Load data from the selected or newly created file
    if selected_subject_file and selected_subject_file.exists():
        try:
            with open(selected_subject_file, 'r') as f:
                subject_data = json.load(f)
            return subject_data
        except json.JSONDecodeError:
             # Format error message in red
            print(f"{RED}Error: The subject file {selected_subject_file} is corrupted or not valid JSON.{RESET}")
            return None
        except Exception as e: # Catch other potential file reading errors
            print(f"{RED}Error reading subject file {selected_subject_file}: {e}{RESET}")
            return None
    else:
         # Format error message in red
         # This path might be reached if create_subject_data failed to write the file
        print(f"{RED}Error: Could not find or load the subject file: {selected_subject_file}{RESET}")
        return None


def create_subject_data(subject_file_name, original_name):
    print(f"\n--- Creating data for {original_name} ---")
    year, month, day = get_date_of_birth()
    hour, minute = get_time_of_birth()
    # Handle potential errors from get_place_of_birth if it returns None or raises exception
    try:
        place_info = get_place_of_birth()
        if place_info is None:
             print(f"{RED}Failed to get place of birth information. Aborting subject creation.{RESET}")
             return # Stop creation if place info is missing
        city, country, lat, lon = place_info
    except Exception as e:
        print(f"{RED}An unexpected error occurred during place of birth entry: {e}. Aborting subject creation.{RESET}")
        return

    timezone = get_timezone(lat, lon)

    # Ask for email (optional)
    email = input("Enter email address (optional, press Enter to skip): ").strip()

    dob_datetime = datetime(year, month, day, hour, minute)
    dob_str = dob_datetime.strftime("%Y-%m-%d %H:%M:%S")

    subject_data = {
        "name": original_name,
        "date_of_birth": dob_str,
        "birthplace": {
            "longitude": lon,
            "latitude": lat,
            "place": city,
            "country": country,
            "timezone": timezone # Timezone can be None if lookup failed
        }
    }
    
    # Add email only if provided
    if email:
        subject_data["email"] = email

    # Ensure the SUBJECT_DIR exists (redundant check, but safe)
    SUBJECT_DIR.mkdir(parents=True, exist_ok=True) 
    
    SUBJECT_FILE = SUBJECT_DIR / f"{subject_file_name}.json"
    try:
        with open(SUBJECT_FILE, 'w') as f:
            json.dump(subject_data, f, indent=4)
        print(f"Subject data saved successfully to {SUBJECT_FILE}")
    except IOError as e:
         # Format error message in red
        print(f"{RED}Error writing subject data to file {SUBJECT_FILE}: {e}{RESET}")



if __name__ == "__main__":
    # Removed the empty string argument, get_subject_data now handles the prompting
    subject_data = get_subject_data() 
    if subject_data:
        print("\n--- Loaded Subject Data ---")
        print(json.dumps(subject_data, indent=4))
    else:
        print("\nFailed to load or create subject data.")



