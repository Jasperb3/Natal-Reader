import json
from immanuel import charts
from immanuel.const import chart
from immanuel.setup import settings
from immanuel.classes.serialize import ToJSON
from datetime import datetime


settings.objects.append(chart.PHOLUS)
settings.objects.append(chart.CERES)
settings.objects.append(chart.PALLAS)
settings.objects.append(chart.JUNO)
settings.objects.append(chart.VESTA)
settings.objects.append(chart.NORTH_NODE)
settings.objects.append(chart.SOUTH_NODE)
settings.objects.append(chart.TRUE_NORTH_NODE)
settings.objects.append(chart.TRUE_SOUTH_NODE)
settings.objects.append(chart.VERTEX)
settings.objects.append(chart.LILITH)
settings.objects.append(chart.TRUE_LILITH)
settings.objects.append(chart.INTERPOLATED_LILITH)
settings.objects.append(chart.SYZYGY)
settings.objects.append(chart.PART_OF_FORTUNE)
settings.objects.append(chart.PART_OF_SPIRIT)
settings.objects.append(chart.PART_OF_EROS)
settings.objects.append(chart.PRE_NATAL_SOLAR_ECLIPSE)
settings.objects.append(chart.PRE_NATAL_LUNAR_ECLIPSE)
settings.objects.append(chart.POST_NATAL_SOLAR_ECLIPSE)
settings.objects.append(chart.POST_NATAL_LUNAR_ECLIPSE)


def get_natal_chart(dob: datetime, latitude: float, longitude: float) -> str:
    subject = charts.Subject(dob, latitude, longitude)
    subject_natal = charts.Natal(subject)
    natal_data = json.dumps(subject_natal, cls=ToJSON, indent=4)
    chart_data = json.loads(natal_data)

    output_lines = []

    # --- 1. Native Information ---
    output_lines.append("--- Natal Chart Summary ---")
    native_info = chart_data.get("native", {})
    date_time_info = native_info.get("date_time", {})
    coords_info = native_info.get("coordinates", {})
    
    output_lines.append(f"Birth Date/Time: {date_time_info.get('datetime', 'N/A')} ({date_time_info.get('timezone', 'N/A')})")
    output_lines.append(f"Julian Day: {date_time_info.get('julian', 'N/A'):.5f}")
    output_lines.append(f"Sidereal Time: {date_time_info.get('sidereal_time', 'N/A')}")
    
    lat = coords_info.get("latitude", {})
    lon = coords_info.get("longitude", {})
    output_lines.append(f"Birth Location: Latitude {lat.get('formatted', 'N/A')}, Longitude {lon.get('formatted', 'N/A')}")
    output_lines.append("-" * 25) # Separator

    # --- 2. Chart Details ---
    output_lines.append("--- Chart Details ---")
    output_lines.append(f"House System: {chart_data.get('house_system', 'N/A')}")
    output_lines.append(f"Chart Shape: {chart_data.get('shape', 'N/A')}")
    output_lines.append(f"Diurnal/Nocturnal: {'Diurnal' if chart_data.get('diurnal', False) else 'Nocturnal'}")
    moon_phase_info = chart_data.get('moon_phase', {})
    output_lines.append(f"Moon Phase: {moon_phase_info.get('formatted', 'N/A')}")
    output_lines.append("-" * 25) # Separator

    # --- 3. Celestial Objects (Planets, Points, Angles, Asteroids) ---
    output_lines.append("--- Celestial Objects ---")
    # Sort objects for consistent order, maybe by a standard astrological order?
    # For now, just sort by name after Angles (Asc, Desc, MC, IC)
    angles = {k: v for k, v in chart_data['objects'].items() if v['type']['name'] == 'Angle'}
    others = {k: v for k, v in chart_data['objects'].items() if v['type']['name'] != 'Angle'}
    
    # Define a rough order for display
    display_order = [
        'Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 
        'Uranus', 'Neptune', 'Pluto', 'Chiron', 'True North Node', 
        'True South Node', 'Asc', 'MC', 'IC', 'Desc', 'Part of Fortune', 
        'Vertex', 'True Lilith' # Add others as needed
    ]
    
    # Create a map for lookup
    obj_by_name = {v['name']: v for v in chart_data['objects'].values()}
    sorted_objects = []
    processed_names = set()

    # Add objects in display_order first
    for name in display_order:
        if name in obj_by_name:
            sorted_objects.append(obj_by_name[name])
            processed_names.add(name)

    # Add any remaining objects not in the specific order, sorted by name
    remaining_objects = sorted(
        [v for name, v in obj_by_name.items() if name not in processed_names],
        key=lambda x: x['name']
    )
    sorted_objects.extend(remaining_objects)


    # Build a map for easy lookup by ID later (needed for aspects)
    object_map = {str(obj['index']): obj for obj in chart_data['objects'].values()}


    for obj in sorted_objects:
        obj_name = obj.get('name', 'Unknown Object')
        obj_type = obj.get('type', {}).get('name', 'N/A')
        output_lines.append(f"\n* {obj_name} ({obj_type})")

        sign_info = obj.get('sign', {})
        sign_name = sign_info.get('name', 'N/A')
        sign_element = sign_info.get('element', 'N/A')
        sign_modality = sign_info.get('modality', 'N/A')
        
        long_fmt = obj.get('longitude', {}).get('formatted', 'N/A')
        sign_long_fmt = obj.get('sign_longitude', {}).get('formatted', 'N/A')
        output_lines.append(f"  Position: {sign_long_fmt} {sign_name} ({sign_element}, {sign_modality})")
        output_lines.append(f"  Zodiac Longitude: {long_fmt}")

        house_info = obj.get('house', {})
        house_name = house_info.get('name', 'N/A')
        output_lines.append(f"  House: {house_name}")

        decan_info = obj.get('decan', {})
        decan_name = decan_info.get('name', 'N/A')
        output_lines.append(f"  Decan: {decan_name}")

        # Optional fields check
        if 'latitude' in obj:
            lat_fmt = obj['latitude'].get('formatted', 'N/A')
            output_lines.append(f"  Latitude: {lat_fmt}")
        
        decl_fmt = obj.get('declination', {}).get('formatted', 'N/A')
        output_lines.append(f"  Declination: {decl_fmt}" + (" (Out of Bounds)" if obj.get('out_of_bounds') else ""))

        if 'speed' in obj and 'movement' in obj:
            speed = obj.get('speed', 0.0)
            move_fmt = obj.get('movement', {}).get('formatted', 'N/A')
            output_lines.append(f"  Movement: {move_fmt} (Speed: {speed:.4f}°/day)") # Adjust precision as needed

        if 'distance' in obj:
            dist = obj.get('distance', 0.0)
            output_lines.append(f"  Distance: {dist:.4f} AU")

        if 'in_sect' in obj: # Only applies to traditional planets
            output_lines.append(f"  In Sect: {'Yes' if obj['in_sect'] else 'No'}")
            
        if 'dignities' in obj and obj['dignities'] and obj['dignities'].get('formatted'):
            dignities_str = ", ".join(obj['dignities']['formatted'])
            output_lines.append(f"  Dignities/Debilities: {dignities_str}")
            
        # Specific info for eclipses
        if obj_type == 'Eclipse':
             eclipse_type_info = obj.get('eclipse_type', {})
             eclipse_fmt = eclipse_type_info.get('formatted', 'N/A')
             eclipse_date_info = obj.get('date_time', {})
             eclipse_date = eclipse_date_info.get('datetime', 'N/A')
             output_lines.append(f"  Eclipse Type: {eclipse_fmt}")
             output_lines.append(f"  Eclipse Date: {eclipse_date}")


    output_lines.append("-" * 25) # Separator

    # --- 4. Houses ---
    output_lines.append("--- Houses (Cusps) ---")
    # Sort houses by number
    sorted_houses = sorted(chart_data['houses'].values(), key=lambda h: h['number'])
    
    for house in sorted_houses:
        house_name = house.get('name', 'Unknown House')
        output_lines.append(f"\n* {house_name} Cusp:")

        sign_info = house.get('sign', {})
        sign_name = sign_info.get('name', 'N/A')
        sign_element = sign_info.get('element', 'N/A')
        sign_modality = sign_info.get('modality', 'N/A')
        
        long_fmt = house.get('longitude', {}).get('formatted', 'N/A')
        sign_long_fmt = house.get('sign_longitude', {}).get('formatted', 'N/A')
        output_lines.append(f"  Position: {sign_long_fmt} {sign_name} ({sign_element}, {sign_modality})")
        output_lines.append(f"  Zodiac Longitude: {long_fmt}")
        
        size = house.get('size', 0.0)
        output_lines.append(f"  Size: {size:.2f}°") # Size of the house

    output_lines.append("-" * 25) # Separator

    # --- 5. Aspects ---
    output_lines.append("--- Aspects ---")
    processed_aspects = set() # To avoid printing duplicates like Sun-Moon and Moon-Sun

    # Iterate through all possible active objects that have aspects listed
    for active_id_str, passive_dict in chart_data.get('aspects', {}).items():
        # Iterate through all passive objects aspected by the active one
        for passive_id_str, aspect_details in passive_dict.items():
            
            # Create a unique identifier for the pair, regardless of order
            # Convert IDs to strings ensures consistent sorting if one is int and other str
            pair = tuple(sorted((active_id_str, passive_id_str))) 

            if pair in processed_aspects:
                continue # Skip if we've already processed this pair

            processed_aspects.add(pair) # Mark this pair as processed

            # Get object names from the map created earlier
            active_obj = object_map.get(active_id_str)
            passive_obj = object_map.get(passive_id_str)

            if not active_obj or not passive_obj:
                continue # Should not happen with valid data, but safety check

            active_name = active_obj.get('name', f'ID {active_id_str}')
            passive_name = passive_obj.get('name', f'ID {passive_id_str}')
            
            aspect_type = aspect_details.get('type', 'N/A')
            orb = aspect_details.get('orb', 0.0)
            diff_fmt = aspect_details.get('difference', {}).get('formatted', 'N/A')
            move_fmt = aspect_details.get('movement', {}).get('formatted', 'N/A')
            cond_fmt = aspect_details.get('condition', {}).get('formatted', 'N/A') # Associate/Dissociate

            # Format the aspect line
            # Example: Sun Conjunction Moon (Orb: 5.23°, Diff: +05°14'02", Applying, Associate)
            output_lines.append(
                f"* {active_name} {aspect_type} {passive_name} "
                f"(Orb: {orb:.2f}°, Diff: {diff_fmt}, {move_fmt}, {cond_fmt})"
            )

    if not processed_aspects:
         output_lines.append("  (No major aspects listed or calculable in source data)")
         
    output_lines.append("-" * 25) # Separator

    # --- 6. Weightings (Elements, Modalities, Quadrants) ---
    output_lines.append("--- Chart Weightings ---")
    weightings = chart_data.get('weightings', {})
    
    # Elements
    output_lines.append("\nElements:")
    elements = weightings.get('elements', {})
    for element, obj_list in elements.items():
        output_lines.append(f"  {element.capitalize()}: {len(obj_list)} objects")
        # Optionally list objects: ", ".join([object_map[str(oid)]['name'] for oid in obj_list])

    # Modalities
    output_lines.append("\nModalities:")
    modalities = weightings.get('modalities', {})
    for modality, obj_list in modalities.items():
         output_lines.append(f"  {modality.capitalize()}: {len(obj_list)} objects")

    # Quadrants
    output_lines.append("\nQuadrants (based on object count):")
    quadrants = weightings.get('quadrants', {})
    quadrant_names = { # Map keys to descriptive names
         'first': 'First (Houses 1-3)', 
         'second': 'Second (Houses 4-6)', 
         'third': 'Third (Houses 7-9)', 
         'fourth': 'Fourth (Houses 10-12)'
    }
    for quadrant_key, obj_list in quadrants.items():
         quad_name = quadrant_names.get(quadrant_key, quadrant_key.capitalize())
         output_lines.append(f"  {quad_name}: {len(obj_list)} objects")

    output_lines.append("-" * 25) # Separator
    output_lines.append("--- End of Natal Chart ---")

    return "\n".join(output_lines)

if __name__ == "__main__":
    subject_data_file = "src/natal_reader/subjects/hayden_brown.json"
    with open(subject_data_file, 'r') as f:
        subject_data = json.load(f)

    dob = datetime.strptime(subject_data.get('date_of_birth'), '%Y-%m-%d %H:%M:%S')
    latitude = subject_data['birthplace']['latitude']
    longitude = subject_data['birthplace']['longitude']
    
    natal_chart = get_natal_chart(dob, latitude, longitude)
    with open("natal_chart.txt", "w") as f:
        f.write(natal_chart)