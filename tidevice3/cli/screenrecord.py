#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import io
import logging

import click
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pymobiledevice3.lockdown import LockdownClient

from tidevice3.api import iter_screenshot
from tidevice3.cli.cli_common import cli, pass_rsd
from tidevice3.exceptions import FatalError

logger = logging.getLogger(__name__)


def draw_text(pil_img: Image.Image, text: str):
    """ GPT生成的，效果勉强吧，不太好，总比没有的强 """
    draw = ImageDraw.Draw(pil_img)
    font = ImageFont.load_default(20)

    # Calculate the bounding box of the text
    text_bbox = font.getbbox(text)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    text_x = 20
    text_y = 50

    # Define text color and background color
    text_color = (255, 0, 0)  # Red color
    background_color = (128, 128, 128, 128)  # Gray color with 50% transparency

    # Create a rectangle background for text
    background_rectangle = [
        (text_x - 10, text_y - 10),  # Upper left corner
        (text_x + text_width + 10, text_y + text_height + 10)  # Lower right corner
    ]
    draw.rectangle(background_rectangle, fill=background_color)
    draw.text((text_x, text_y), text, fill=text_color, font=font)
    return pil_img


@cli.command("screenrecord")
@click.option("--fps", default=5, help="frame per second")
@click.option("--show-time/--no-show-time", default=True, help="show time on screen")
@click.argument("out")
@pass_rsd
def cli_screenrecord(service_provider: LockdownClient, out: str, fps: int, show_time: bool):
    """ screenrecord to mp4 """
    try:
        import imageio.v2 as imageio
    except ImportError:
        raise FatalError("Please install imageio first, pip3 install imageio[ffmpeg]")
    
    writer = imageio.get_writer(out, fps=fps, macro_block_size=1)
    n = 0
    try:
        for png_data in iter_screenshot(service_provider):
            pil_img = Image.open(io.BytesIO(png_data))
            if show_time:
                time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                draw_text(pil_img, f'Time: {time_str} Frame: {n}')
            print(".", end="", flush=True)
            frame_with_text = np.array(pil_img)
            writer.append_data(frame_with_text)
            n += 1
    except KeyboardInterrupt:
        pass
    finally:
        writer.close()
        logger.info("screenrecord saved to %s", out)
