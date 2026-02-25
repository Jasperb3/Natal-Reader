import os
from kerykeion import AstrologicalSubject, KerykeionChartSVG
from natal_reader.utils.screenshot_util import capture_svg_screenshot

def get_kerykeion_subject(name: str, year: int, month: int, day: int, hour: int, minute: int, city: str, nation: str, longitude: float, latitude: float, timezone: str) -> AstrologicalSubject:
    subject = AstrologicalSubject(
        name,
        year,
        month,
        day,
        hour,
        minute,
        city=city,
        nation=nation,
        lng=longitude,
        lat=latitude,
        tz_str=timezone,
        online=False,
        disable_chiron_and_lilith=False
    )

    return subject



def get_kerykeion_natal_chart(subject: AstrologicalSubject, output_directory: str) -> str:
    natal_chart = KerykeionChartSVG(
        subject,
        chart_type="Natal",
        new_output_directory=output_directory,
        active_points=[
            "Sun",
            "Moon",
            "Mercury",
            "Venus",
            "Mars",
            "Jupiter",
            "Saturn",
            "Uranus",
            "Neptune",
            "Pluto",
            "True_Node",
            "Chiron",
            "Ascendant",
            "Medium_Coeli",
            "Descendant",
            "Imum_Coeli",
            "Mean_Lilith",
            "True_South_Node"
        ]
    )

    print(f"Natal chart = {natal_chart}")

    natal_chart.makeSVG()

    svg_file_path = f"{output_directory}/{subject.name} - Natal Chart.svg"
    svg_renamed_path = f"{output_directory}/{subject.name.replace(' ', '')}NatalChart.svg"
    os.rename(svg_file_path, svg_renamed_path)
    png_file_path = capture_svg_screenshot(svg_renamed_path, output_directory)
    final_png_file_path = f"{output_directory}/{subject.name.replace(' ', '')}NatalChart.png"
    os.rename(png_file_path, final_png_file_path)
    print(f"Natal chart saved to {final_png_file_path}")
    return final_png_file_path


if __name__ == "__main__":
    test_dir = "tests"
    subject = get_kerykeion_subject("John Doe", 1990, 1, 1, 0, 0, "New York", "United States", -74.006, 40.7128, "America/New_York")
    get_kerykeion_natal_chart(subject, test_dir)

