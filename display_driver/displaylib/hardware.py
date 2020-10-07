#!/usr/bin/env python3

# Third-party libraries

# Requires rgbmatrix installed via special procedure; see README.md
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics


MATRIX_WIDTH = 64 # pixels
MATRIX_HEIGHT = 32 # pixels


def make_matrix() -> RGBMatrix:
  options = RGBMatrixOptions()

  options.rows = MATRIX_HEIGHT
  options.cols = MATRIX_WIDTH
  options.chain_length = 1
  options.parallel = 1
  options.row_address_type = 0
  options.multiplexing = 0
  options.pwm_bits = 11
  options.brightness = 100
  options.pwm_lsb_nanoseconds = 130
  options.led_rgb_sequence = 'RGB'
  options.pixel_mapper_config = ''
  options.gpio_slowdown = 1

  return RGBMatrix(options=options)


def make_font(font_filename: str) -> graphics.Font:
  font = graphics.Font()
  font.LoadFont(font_filename)
  return font
