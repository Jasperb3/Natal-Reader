import json
from itertools import combinations
from immanuel import charts
from immanuel.const import chart
from immanuel.setup import settings
from immanuel.classes.serialize import ToJSON
from datetime import datetime

# Primary house system — matches the Kerykeion wheel (kerykeion_chart_utils.py);
# whole-sign houses are computed per object below as a supplement for Hellenistic
# topical work, since Hellenistic technique is whole-sign-house-based.
settings.house_system = chart.PLACIDUS

# settings.objects.append(chart.PHOLUS)
# settings.objects.append(chart.CERES)
# settings.objects.append(chart.PALLAS)
# settings.objects.append(chart.JUNO)
# settings.objects.append(chart.VESTA)
# settings.objects.append(chart.NORTH_NODE)
# settings.objects.append(chart.SOUTH_NODE)
settings.objects.append(chart.TRUE_NORTH_NODE)
settings.objects.append(chart.TRUE_SOUTH_NODE)
# settings.objects.append(chart.VERTEX)
settings.objects.append(chart.LILITH)
# settings.objects.append(chart.TRUE_LILITH)
# settings.objects.append(chart.INTERPOLATED_LILITH)
settings.objects.append(chart.SYZYGY)
settings.objects.append(chart.PART_OF_FORTUNE)
# settings.objects.append(chart.PART_OF_SPIRIT)
# settings.objects.append(chart.PART_OF_EROS)
# settings.objects.append(chart.PRE_NATAL_SOLAR_ECLIPSE)
# settings.objects.append(chart.PRE_NATAL_LUNAR_ECLIPSE)
# settings.objects.append(chart.POST_NATAL_SOLAR_ECLIPSE)
# settings.objects.append(chart.POST_NATAL_LUNAR_ECLIPSE)


SIGN_RULERS = {
    'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury',
    'Cancer': 'Moon', 'Leo': 'Sun', 'Virgo': 'Mercury',
    'Libra': 'Venus', 'Scorpio': 'Mars', 'Sagittarius': 'Jupiter',
    'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
}


def find_mutual_receptions(positions: dict[str, str]) -> list[str]:
    """positions maps traditional planet name -> sign name. Returns human-readable
    mutual reception descriptions (planet A ruled by planet B's sign and vice versa)."""
    receptions = []
    names = list(positions.keys())
    for i, planet_a_name in enumerate(names):
        sign_a = positions[planet_a_name]
        for planet_b_name in names[i + 1:]:
            sign_b = positions[planet_b_name]
            if SIGN_RULERS.get(sign_a) == planet_b_name and SIGN_RULERS.get(sign_b) == planet_a_name:
                receptions.append(f"{planet_a_name} in {sign_a} ↔ {planet_b_name} in {sign_b}")
    return receptions


def iter_unique_aspects(chart_data: dict, object_map: dict):
    """Yield each aspect pair once, deduped by object-ID pair (Immanuel's aspects
    dict is bidirectional: Sun-Moon appears under both aspects[sun][moon] and
    aspects[moon][sun])."""
    processed_pairs = set()
    for active_id_str, passive_dict in chart_data.get('aspects', {}).items():
        for passive_id_str, aspect_details in passive_dict.items():
            pair = tuple(sorted((active_id_str, passive_id_str)))
            if pair in processed_pairs:
                continue
            processed_pairs.add(pair)

            active_obj = object_map.get(active_id_str)
            passive_obj = object_map.get(passive_id_str)
            if not active_obj or not passive_obj:
                continue

            yield active_obj, passive_obj, aspect_details


def get_natal_chart(dob: datetime, latitude: float, longitude: float, timezone: str | None = None) -> str:
    subject = charts.Subject(dob, latitude, longitude, timezone=timezone)
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
    julian_day = date_time_info.get("julian")
    output_lines.append(f"Julian Day: {julian_day:.5f}" if julian_day is not None else "Julian Day: N/A")
    output_lines.append(f"Sidereal Time: {date_time_info.get('sidereal_time', 'N/A')}")
    
    lat = coords_info.get("latitude", {})
    lon = coords_info.get("longitude", {})
    output_lines.append(f"Birth Location: Latitude {lat.get('formatted', 'N/A')}, Longitude {lon.get('formatted', 'N/A')}")
    output_lines.append("-" * 25) # Separator

    # --- 2. Chart Details ---
    output_lines.append("--- Chart Details ---")
    output_lines.append(
        f"House System: {chart_data.get('house_system', 'N/A')} "
        "(primary; whole-sign houses provided per object for Hellenistic topics)"
    )
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
    
    # Define a rough order for display (mirrors kerykeion chart objects)
    display_order = [
        'Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn',
        'Uranus', 'Neptune', 'Pluto', 'Chiron', 'True North Node',
        'True South Node', 'Lilith', 'Asc', 'MC', 'IC', 'Desc'
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

    # Whole-sign houses (supplementary, for Hellenistic topical work) are counted
    # from the Ascendant's sign, regardless of the Placidus cusps used above.
    asc_sign_number = obj_by_name.get('Asc', {}).get('sign', {}).get('number')

    def _ordinal(n: int) -> str:
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

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
        obj_sign_number = sign_info.get('number')
        if asc_sign_number and obj_sign_number:
            whole_sign_house = ((obj_sign_number - asc_sign_number) % 12) + 1
            output_lines.append(f"  House: {house_name} (Placidus) | {_ordinal(whole_sign_house)} (whole sign)")
        else:
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

    unique_aspects = list(iter_unique_aspects(chart_data, object_map))

    for active_obj, passive_obj, aspect_details in unique_aspects:
        active_name = active_obj.get('name', 'Unknown')
        passive_name = passive_obj.get('name', 'Unknown')

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

    if not unique_aspects:
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

    # --- 7. Pre-computed Patterns ---
    output_lines.append("--- Pre-computed Patterns ---")

    # Chart Ruler Identification
    asc_obj = obj_by_name.get('Asc')
    if asc_obj:
        asc_sign = asc_obj.get('sign', {}).get('name', 'Unknown')
        chart_ruler_name = SIGN_RULERS.get(asc_sign, 'Unknown')
        chart_ruler_obj = obj_by_name.get(chart_ruler_name)

        if chart_ruler_obj:
            ruler_sign = chart_ruler_obj.get('sign', {}).get('name', 'N/A')
            ruler_house = chart_ruler_obj.get('house', {}).get('name', 'N/A')
            ruler_dignities = chart_ruler_obj.get('dignities', {}).get('formatted', [])
            ruler_dignities_str = ", ".join(ruler_dignities) if ruler_dignities else "None"
            ruler_sect = "In Sect" if chart_ruler_obj.get('in_sect', False) else "Out of Sect"

            output_lines.append(f"\nChart Ruler: {chart_ruler_name} (ruler of {asc_sign} Ascendant)")
            output_lines.append(f"  Placed in: {ruler_sign} in {ruler_house}")
            output_lines.append(f"  Dignities: {ruler_dignities_str}")
            output_lines.append(f"  Sect Status: {ruler_sect}")

    # Stellium Detection (3+ planets in same sign or house)
    # Only count actual planets, exclude angles and points
    planet_names = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter',
                   'Saturn', 'Uranus', 'Neptune', 'Pluto']
    planets = [obj for obj in sorted_objects if obj.get('name') in planet_names]

    # Group by sign
    sign_groups = {}
    for planet in planets:
        sign = planet.get('sign', {}).get('name', 'Unknown')
        if sign not in sign_groups:
            sign_groups[sign] = []
        sign_groups[sign].append(planet.get('name'))

    # Group by house
    house_groups = {}
    for planet in planets:
        house = planet.get('house', {}).get('name', 'Unknown')
        if house not in house_groups:
            house_groups[house] = []
        house_groups[house].append(planet.get('name'))

    # Sign and house stelliums are distinct findings and are both reported, even
    # when the same planets form both (that coincidence is itself significant).
    sign_stelliums = [
        (sign, frozenset(planet_list))
        for sign, planet_list in sign_groups.items()
        if len(planet_list) >= 3
    ]
    house_stelliums = [
        (house, frozenset(planet_list))
        for house, planet_list in house_groups.items()
        if len(planet_list) >= 3
    ]

    stelliums_found = []
    for sign, members in sign_stelliums:
        same_as_house = any(members == house_members for _, house_members in house_stelliums)
        suffix = " — same planets by sign and house" if same_as_house else ""
        stelliums_found.append(f"Sign stellium: {sign} ({', '.join(sorted(members))}){suffix}")

    for house, members in house_stelliums:
        same_as_sign = any(members == sign_members for _, sign_members in sign_stelliums)
        suffix = " — same planets by sign and house" if same_as_sign else ""
        stelliums_found.append(f"House stellium: {house} ({', '.join(sorted(members))}){suffix}")

    output_lines.append(f"\nStelliums Detected: {len(stelliums_found)}")
    if stelliums_found:
        for stellium in stelliums_found:
            output_lines.append(f"  - {stellium}")
    else:
        output_lines.append("  None")

    # Hemisphere Balance
    eastern_houses = ['1st House', '2nd House', '3rd House', '10th House', '11th House', '12th House']
    western_houses = ['4th House', '5th House', '6th House', '7th House', '8th House', '9th House']
    northern_houses = ['1st House', '2nd House', '3rd House', '4th House', '5th House', '6th House']
    southern_houses = ['7th House', '8th House', '9th House', '10th House', '11th House', '12th House']

    east_count = sum(1 for p in planets if p.get('house', {}).get('name') in eastern_houses)
    west_count = sum(1 for p in planets if p.get('house', {}).get('name') in western_houses)
    north_count = sum(1 for p in planets if p.get('house', {}).get('name') in northern_houses)
    south_count = sum(1 for p in planets if p.get('house', {}).get('name') in southern_houses)

    output_lines.append("\nHemisphere Balance:")
    output_lines.append(f"  Eastern (Houses 10-3): {east_count} planets")
    output_lines.append(f"  Western (Houses 4-9): {west_count} planets")
    output_lines.append(f"  Northern (Houses 1-6): {north_count} planets")
    output_lines.append(f"  Southern (Houses 7-12): {south_count} planets")

    # Mutual Receptions (traditional planets only)
    traditional_planets = ['Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn']
    traditional_positions = {
        name: obj_by_name[name].get('sign', {}).get('name')
        for name in traditional_planets
        if name in obj_by_name
    }
    mutual_receptions = find_mutual_receptions(traditional_positions)

    output_lines.append(f"\nMutual Receptions: {len(mutual_receptions)}")
    if mutual_receptions:
        for reception in mutual_receptions:
            output_lines.append(f"  - {reception}")
    else:
        output_lines.append("  None")

    # Tight Aspects Summary (orb < 2°) — reuses the already-deduped unique_aspects
    # list, so this can no longer diverge from the main Aspects section (P0-1).
    tight_aspects = []
    for active_obj, passive_obj, aspect_details in unique_aspects:
        orb = aspect_details.get('orb', 999)
        if orb < 2.0:
            active_name = active_obj.get('name', 'Unknown')
            passive_name = passive_obj.get('name', 'Unknown')
            aspect_type = aspect_details.get('type', 'N/A')
            tight_aspects.append(f"{active_name} {aspect_type} {passive_name} (Orb: {orb:.2f}°)")

    output_lines.append(f"\nTight Aspects (Orb < 2°): {len(tight_aspects)}")
    if tight_aspects:
        for aspect in sorted(tight_aspects):
            output_lines.append(f"  - {aspect}")
    else:
        output_lines.append("  None")

    # Anaretic Degree Flags (29th degree of a sign — critical/urgent placements)
    anaretic_placements = [
        f"{obj.get('name')} ({obj.get('sign', {}).get('name', 'N/A')})"
        for obj in sorted_objects
        if obj.get('sign_longitude', {}).get('degrees') == 29
    ]
    output_lines.append(f"\nAnaretic Placements (29th degree): {len(anaretic_placements)}")
    if anaretic_placements:
        for placement in anaretic_placements:
            output_lines.append(f"  - {placement}")
    else:
        output_lines.append("  None detected")

    # Aspect Configurations (T-squares, grand trines, grand crosses) among the
    # 10 planets, computed from the deduped aspect list so the LLM doesn't have
    # to infer these from raw aspect lines.
    aspect_lookup = {}
    for active_obj, passive_obj, aspect_details in unique_aspects:
        a_name, p_name = active_obj.get('name'), passive_obj.get('name')
        aspect_type = aspect_details.get('type')
        if a_name and p_name and aspect_type:
            aspect_lookup[frozenset((a_name, p_name))] = aspect_type

    def _aspect_between(name_a: str, name_b: str) -> str | None:
        return aspect_lookup.get(frozenset((name_a, name_b)))

    configuration_planets = [p.get('name') for p in planets]
    t_squares = []
    grand_trines = []
    grand_crosses = []

    for a, b, c in combinations(configuration_planets, 3):
        ab, ac, bc = _aspect_between(a, b), _aspect_between(a, c), _aspect_between(b, c)
        aspects_present = [ab, ac, bc]
        if aspects_present.count('Opposition') == 1 and aspects_present.count('Square') == 2:
            t_squares.append(f"{a}, {b}, {c}")
        if ab == 'Trine' and ac == 'Trine' and bc == 'Trine':
            grand_trines.append(f"{a}, {b}, {c}")

    for four in combinations(configuration_planets, 4):
        # Of the 3 ways to split 4 planets into two diagonal (opposition) pairs,
        # check each: remaining 4 cross-connections must all be squares.
        diagonal_partitions = [
            ((four[0], four[1]), (four[2], four[3])),
            ((four[0], four[2]), (four[1], four[3])),
            ((four[0], four[3]), (four[1], four[2])),
        ]
        for (d1a, d1b), (d2a, d2b) in diagonal_partitions:
            if _aspect_between(d1a, d1b) != 'Opposition' or _aspect_between(d2a, d2b) != 'Opposition':
                continue
            sides = [(d1a, d2a), (d1a, d2b), (d1b, d2a), (d1b, d2b)]
            if all(_aspect_between(x, y) == 'Square' for x, y in sides):
                grand_crosses.append(f"{four[0]}, {four[1]}, {four[2]}, {four[3]}")
                break

    output_lines.append(f"\nAspect Configurations:")
    output_lines.append(f"  T-Squares: {len(t_squares)}")
    for config in t_squares:
        output_lines.append(f"    - {config}")
    if not t_squares:
        output_lines.append("    None detected")

    output_lines.append(f"  Grand Trines: {len(grand_trines)}")
    for config in grand_trines:
        output_lines.append(f"    - {config}")
    if not grand_trines:
        output_lines.append("    None detected")

    output_lines.append(f"  Grand Crosses: {len(grand_crosses)}")
    for config in grand_crosses:
        output_lines.append(f"    - {config}")
    if not grand_crosses:
        output_lines.append("    None detected")

    output_lines.append("-" * 25) # Separator
    output_lines.append("--- End of Natal Chart ---")

    return "\n".join(output_lines)

if __name__ == "__main__":
    subject_data_file = "src/natal_reader/subjects/john_doe.json"
    with open(subject_data_file, 'r') as f:
        subject_data = json.load(f)

    dob = datetime.strptime(subject_data.get('date_of_birth'), '%Y-%m-%d %H:%M:%S')
    latitude = subject_data['birthplace']['latitude']
    longitude = subject_data['birthplace']['longitude']
    
    natal_chart = get_natal_chart(dob, latitude, longitude)
    test_dir = "tests"
    with open(f"{test_dir}/john_doe_natal_chart.txt", "w") as f:
        f.write(natal_chart)