import json
from immanuel import charts
from immanuel.const import chart
from immanuel.setup import settings
from immanuel.classes.serialize import ToJSON
from datetime import datetime
from typing import Tuple


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


def get_current_transits(location: Tuple[float, float]) -> dict:
    transit_chart = charts.Transits(location[0], location[1])
    # result = json.loads(json.dumps(transit_chart, cls=ToJSON, indent=4))

    current_transits = []
    types = ["Planet", "Asteroid"]
    for planet_data in transit_chart.objects.values():
        if planet_data.type.name in types:
            current_transits.append(
                {
                    "name": planet_data.name,
                    "longitude": planet_data.longitude.formatted,
                    "sign": planet_data.sign.name,
                    "house": planet_data.house.name,
                    "speed": planet_data.speed,
                    "movement": planet_data.movement.formatted,
                }
            )
        elif planet_data.type.name == "Angle":
            current_transits.append(
                {
                    "name": planet_data.name,
                    "longitude": planet_data.longitude.formatted,
                    "sign": planet_data.sign.name,
                    "decan": planet_data.decan.name,
                    "house": planet_data.house.name,
                    "speed": planet_data.speed,
                    "declination": planet_data.declination.formatted,
                }
            )
    for aspect_data in transit_chart.aspects.values():
        for aspect in aspect_data.values():
            active_object = transit_chart.objects.get(aspect.active)
            passive_object = transit_chart.objects.get(aspect.passive)
            if active_object and passive_object:
                current_transits.append(
                    {
                        "name": f"{active_object.name} {aspect.type} {passive_object.name}",
                        "orb": aspect.orb,
                        "distance": aspect.distance.formatted,
                        "difference": aspect.difference.formatted,
                        "movement": aspect.movement.formatted,
                        "condition": aspect.condition.formatted,
                    }
                )

    return {
        "current_transits": current_transits,
    }


def get_transit_natal_aspects(location: Tuple[float, float], dob: datetime, birthplace: Tuple[float, float]) -> dict:
    subject = charts.Subject(dob, birthplace[0], birthplace[1])
    subject_natal = charts.Natal(subject)
    transit_chart = charts.Transits(location[0], location[1], aspects_to=subject_natal)

    transit_aspects = []
    for natal_planet_index, aspect_list in transit_chart.aspects.items():
        natal_planet_name = subject_natal.objects[natal_planet_index].name
        aspects_for_natal_planet = []
        for transit_planet_index, aspect_data in aspect_list.items():
            transit_planet_name = transit_chart.objects[transit_planet_index].name
            aspects_for_natal_planet.append(
                f"  - Transiting {transit_planet_name} {aspect_data.type} Natal {natal_planet_name} within {aspect_data.difference}"
            )
        transit_aspects.append({
            "natal_planet": natal_planet_name,
            "aspects": aspects_for_natal_planet,
        })

    transit_house_placements = []
    for transit_object_index, transit_object in transit_chart.objects.items():
        if transit_object.type.name == 'Planet':
            natal_house_index = subject_natal.house_for(transit_object)
            natal_house_name = subject_natal.houses[natal_house_index].name
            transit_planet_name = transit_object.name
            transit_house_placements.append(
                f"  - Transiting {transit_planet_name} in Natal {natal_house_name}"
            )

    return {
        "aspects": transit_aspects,
        "house_placements": transit_house_placements,
    }

def calculate_transit_data(transit_data: dict) -> str:
    """Formats the transit data for printing."""
    output = ""
    if transit_data['aspects']:
        output += "\n🌌 Transit Aspects to Natal Planets\n"
        for planet_aspects in transit_data['aspects']:
            output += f"\nTransit Aspects to Natal {planet_aspects['natal_planet']}:\n"
            for aspect in planet_aspects['aspects']:
                output += f"{aspect}\n"
    else:
        output += "\nNo Transit Aspects Found\n"

    if transit_data['house_placements']:
        output += "\nTransit Planet House Placements in Natal Chart:\n"
        for placement in transit_data['house_placements']:
            output += f"{placement}\n"
    else:
        output += "\nNo Transit House Placements Found\n"

    return output

if __name__ == "__main__":
    transit_data = get_current_transits((51.565131, -0.147709))
    natal_aspects = get_transit_natal_aspects((51.565131, -0.147709), datetime(1984, 1, 11, 18, 45, 0), (51.565131, -0.147709))
    print(transit_data)
    print(calculate_transit_data(natal_aspects))