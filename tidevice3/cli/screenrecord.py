#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import io
import logging
import time
from typing import Any, Iterator

import click
import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pymobiledevice3.lockdown import LockdownClient

from tidevice3.api import iter_screenshot
from tidevice3.cli.cli_common import cli, pass_rsd

logger = logging.getLogger(__name__)


def limit_fps(screenshot_iterator: Iterator[Any], fps: int, debug: bool = False) -> Iterator[Any]:
    """ Limit the frame rate of the screenshot iterator to the given FPS """
    frame_duration = 1.0 / fps
    next_frame_time = time.time()
    last_screenshot = None

    for screenshot in screenshot_iterator:
        current_time = time.time()

        if current_time >= next_frame_time:
            last_screenshot = screenshot

            # Write frame to video
            if debug:
                print(".", end="", flush=True)
            yield screenshot

            # Schedule next frame
            next_frame_time += frame_duration

        # Fill in with the last image if the next frame time is still in the future
        while next_frame_time <= current_time:
            if last_screenshot is not None:
                if debug:
                    print("o", end="", flush=True)
                yield last_screenshot
            next_frame_time += frame_duration


def draw_text(pil_img: Image.Image, text: str):
    """ GPT生成的，效果勉强吧，不太好，总比没有的强 """
    draw = ImageDraw.Draw(pil_img)
    font = ImageFont.load_default()

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


def resize_for_ffmpeg(img: Image.Image) -> Image.Image:
    """
    部分机型截图的尺寸不对，所以需要resize，目前发现机型：iPhone x
    """
    w, h = img.size
    if w % 2 != 0:
        w -= 1
    if h % 2 != 0:
        h -= 1
    img = img.crop((0, 0, w, h))
    return img


@cli.command("screenrecord")
@click.option("--fps", default=5, help="frame per second")
@click.option("--show-time/--no-show-time", default=True, help="show time on screen")
@click.argument("out")
@pass_rsd
def cli_screenrecord(service_provider: LockdownClient, out: str, fps: int, show_time: bool):
    """ screenrecord to mp4 """
    writer = imageio.get_writer(out, fps=fps)
    frame_index = 0
    try:
        for png_data in limit_fps(iter_screenshot(service_provider), fps, debug=True):
            pil_img = Image.open(io.BytesIO(png_data))
            pil_img = resize_for_ffmpeg(pil_img)
            if show_time:
                time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                draw_text(pil_img, f'Time: {time_str} Frame: {frame_index}')
            
            writer.append_data(np.array(pil_img))
            frame_index += 1
    except KeyboardInterrupt:
        print("")
    finally:
        writer.close()
        logger.info("screenrecord saved to %s", out)
