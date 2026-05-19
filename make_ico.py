from PIL import Image
img = Image.open(r'c:\Users\poojan\OneDrive\Desktop\Python_Apps\icon.png')
img.save(r'c:\Users\poojan\OneDrive\Desktop\Python_Apps\icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
