import os
import json
from kerykeion import AstrologicalSubject, Report
from immanuel import charts
from natal_reader.utils.subject_selection import get_subject_data
from datetime import datetime

subject = get_subject_data()

dob = datetime.strptime(subject["date_of_birth"], "%Y-%m-%d %H:%M:%S")


def kerykeion_house_placements():
    kerykeion_natal_subject = AstrologicalSubject(
        name=subject["name"],
        year=dob.year,
        month=dob.month,
        day=dob.day,
        hour=dob.hour,
        minute=dob.minute,
        city=subject["birthplace"]["place"],
        nation=subject["birthplace"]["country"],
        lng=subject["birthplace"]["longitude"],
        lat=subject["birthplace"]["latitude"],
        tz_str=subject["birthplace"]["timezone"]
    )

    kerykeion_report = Report(kerykeion_natal_subject)

    print(f"Kerykeion House Placements: {kerykeion_report.houses_table}")


def kerykeion_planetary_positions():
    kerykeion_natal_subject = AstrologicalSubject(
        name=subject["name"],
        year=dob.year,
        month=dob.month,
        day=dob.day,
        hour=dob.hour,
        minute=dob.minute,
        city=subject["birthplace"]["place"],
        nation=subject["birthplace"]["country"],
        lng=subject["birthplace"]["longitude"],
        lat=subject["birthplace"]["latitude"],
        tz_str=subject["birthplace"]["timezone"]
    )

    kerykeion_report = Report(kerykeion_natal_subject)

    print(f"Kerykeion Planetary Positions: {kerykeion_report.planets_table}")


def immanuel_house_placements():
    immanuel_natal_subject = charts.Subject(dob, subject["birthplace"]["latitude"], subject["birthplace"]["longitude"])
    immanuel_subject_natal = charts.Natal(immanuel_natal_subject)
    immanuel_houses_data = immanuel_subject_natal.houses

    for house in immanuel_houses_data.values():
        print(house)


def immanuel_planetary_positions():
    immanuel_natal_subject = charts.Subject(dob, subject["birthplace"]["latitude"], subject["birthplace"]["longitude"])
    immanuel_subject_natal = charts.Natal(immanuel_natal_subject)
    immanuel_planetary_positions_data = immanuel_subject_natal.objects

    for planet in immanuel_planetary_positions_data.values():
        print(planet)


def run_tests():
    # kerykeion_house_placements()
    kerykeion_planetary_positions()
    # immanuel_house_placements()
    immanuel_planetary_positions()


if __name__ == "__main__":
    run_tests()



