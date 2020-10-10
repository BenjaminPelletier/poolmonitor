from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics

font = graphics.Font()
font.LoadFont('/home/pi/poolmonitor/display_driver/fonts/7x13.bdf')

options = RGBMatrixOptions()
options.rows = 32
options.cols = 64
matrix = RGBMatrix(options=options)

print('Exited successfully')
