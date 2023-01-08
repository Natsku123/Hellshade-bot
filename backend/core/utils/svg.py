from jinja2 import Environment, FileSystemLoader
from datetime import date


def translate(value, leftMin, leftMax, rightMin, rightMax):
    # Figure out how 'wide' each range is
    leftSpan = leftMax - leftMin
    rightSpan = rightMax - rightMin

    # Convert the left range into a 0-1 range (float)
    valueScaled = float(value - leftMin) / float(leftSpan)

    # Convert the 0-1 range into a value in the right range.
    return rightMin + (valueScaled * rightSpan)


def render_ip(ip: str):
    env = Environment(
        loader=FileSystemLoader('templates')
    )
    template = env.get_template('ip_template.svg')

    return template.render(**{
        "ip": ip
    })

def render(name: str, current_exp: int, needed_exp: int, level: int, url: str):
    env = Environment(
        loader=FileSystemLoader('templates')
    )
    left_bound = -320
    right_bound = 230
    #left_limit = -255
    #right_limit = 175

    p = current_exp / needed_exp

    if p > 1:
        p = 1

    x = translate(p, 0, 1, left_bound, right_bound)

    anchor = "middle"

    template = env.get_template('discord_level_progress.svg')
    return template.render(**{
        "name": name,
        "current_exp": current_exp,
        "needed_exp": needed_exp,
        "percentage": f"{p*100:.2f}%",
        "level": level,
        "url": url,
        "anchor": anchor,
        "x": x,
        "px": p*552,
        "dt": date.today()
    })
