#!/usr/bin/env python3

# Basic Python libraries
import datetime
import sys
import time

# Third-party libraries

# Requires rgbmatrix installed via special procedure; see README.md
from rgbmatrix import graphics
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# Libraries in this project
from displaylib import loadcell_polling, hardware, accessories

FORCE_MAX = 35 # pounds of force that maxes out color-keying


def display_loop():
  # Set up resources to display graphics on RGB matrix
  matrix = hardware.make_matrix()
  canvas = matrix.CreateFrameCanvas()
  font = hardware.make_font('./fonts/7x13.bdf')
  img = np.zeros([hardware.MATRIX_HEIGHT, hardware.MATRIX_WIDTH, 3],
                 dtype=np.uint8)

  # Create named colors for better readability later
  red = graphics.Color(255, 0, 0)
  orange = graphics.Color(255, 128, 0)
  yellow = graphics.Color(255, 255, 0)
  darkgreen = graphics.Color(0, 32, 0)
  green = graphics.Color(0, 255, 0)
  blue = graphics.Color(0, 0, 255)

  # Make colormap for visualizing force
  # https://matplotlib.org/3.1.0/tutorials/colors/colormaps.html
  turbo = plt.get_cmap('turbo')

  # Define which colors correspond to which load cell polling phases
  poll_colors = {
    loadcell_polling.PollPhase.Waiting: darkgreen,
    loadcell_polling.PollPhase.Polling: yellow,
    loadcell_polling.PollPhase.Processing: red,
    loadcell_polling.PollPhase.Unknown: blue,
  }

  # Define which colors correspond to which swim session phases
  session_colors = {
    'IDLE': red,
    'STARTING': yellow,
    'ACTIVE': green,
    'STOPPING': orange,
  }

  # Provides visual indication of the RGB matrix frame rate
  frame_index = 0

  while True:
    # Start with a blank canvas
    canvas.Clear()

    # Skip all drawing if the display is not enabled
    if accessories.display_enabled:
      # Get the current state of the load cell and its polling threads
      loadcell = loadcell_polling.coordinator.get_loadcell()
      phases = [loadcell_polling.coordinator.get_phase(p)
                for p in range(loadcell_polling.POLLING_THREADS)]

      # Black out the background image
      img[:,:,:] = 0

      if loadcell is None:
        # Blank everything except an error message if we have no laod cell state
        force_text = ''
        force_color = red
        session_text = 'LC err'
        session_color = red
      else:
        # Draw color-mapped force history on the background image
        x = hardware.MATRIX_WIDTH - 1
        for v in reversed(loadcell['sensor']['history']['values']):
          history_color_rgba = turbo(v / FORCE_MAX)
          img[21:, x, 0] = round(history_color_rgba[0] * 255)
          img[21:, x, 1] = round(history_color_rgba[1] * 255)
          img[21:, x, 2] = round(history_color_rgba[2] * 255)
          x -= 1
          if x < 0:
            break

        # Decide on text and color to display for current force
        force_text = '{:.1f} lb'.format(max(0, loadcell['sensor']['instantaneous_value']))
        force_value = loadcell['sensor']['instantaneous_value'] / FORCE_MAX
        force_color_rgba = turbo(force_value)
        force_color = graphics.Color(round(force_color_rgba[0] * 255),
                                     round(force_color_rgba[1] * 255),
                                     round(force_color_rgba[2] * 255))

        # Decide on text and color to display for session time
        session_text = str(datetime.timedelta(
          seconds=round(loadcell['session']['duration'])))
        session_color = session_colors[loadcell['session']['mode']]

      # Draw a white dot in the bottom left that scrolls to show frame redraws
      img[21 + frame_index, 0, :] = 128
      frame_index += 1
      if frame_index > 10:
        frame_index = 0

      # Draw the background image (including force history)
      pil_image = Image.fromarray(img)
      canvas.SetImage(pil_image)

      # Draw the force and session text
      graphics.DrawText(canvas, font, 0, 10, force_color, force_text)
      graphics.DrawText(canvas, font, 0, 20, session_color, session_text)

      # Draw indicators for the load cell polling threads
      for p, phase in enumerate(phases):
        graphics.DrawCircle(canvas, hardware.MATRIX_WIDTH - 3, 2 + p * 5, 2,
                            poll_colors[phase])

    # Swap buffers to render output to RGB matrix
    canvas = matrix.SwapOnVSync(canvas)

    # Wait to begin the next frame
    time.sleep(0.05)


# Entry point
if __name__ == "__main__":
  loadcell_polling.start_polling()
  accessories.start_polling()

  try:
    # Start loop
    print("Press CTRL-C to stop")
    display_loop()
  except KeyboardInterrupt:
    print("Exiting\n")
    sys.exit(0)
