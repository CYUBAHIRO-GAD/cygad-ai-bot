RESOURCES = [
    ("Arduino documentation", "https://docs.arduino.cc/"),
    ("ESP32 / ESP-IDF documentation", "https://docs.espressif.com/projects/esp-idf/en/stable/esp32/"),
    ("ESP8266 Arduino core", "https://github.com/esp8266/Arduino"),
    ("Raspberry Pi documentation", "https://www.raspberrypi.com/documentation/"),
    ("MicroPython documentation", "https://docs.micropython.org/"),
    ("PlatformIO documentation", "https://docs.platformio.org/"),
    ("KiCad", "https://www.kicad.org/"),
    ("Wokwi simulator", "https://wokwi.com/"),
    ("Tinkercad Circuits", "https://www.tinkercad.com/circuits"),
    ("LTspice", "https://www.analog.com/ltspice"),
    ("Proteus", "https://www.labcenter.com/"),
    ("Thonny Python IDE", "https://thonny.org/"),
]

def format_resources():
    return "\n".join(f"• {name}: {url}" for name, url in RESOURCES)
