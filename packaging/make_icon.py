from pathlib import Path
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
out = root / 'assets'
out.mkdir(exist_ok=True)
image = Image.new('RGBA', (256,256))
draw = ImageDraw.Draw(image)
draw.rounded_rectangle((6,6,250,250),radius=55,fill='#3478f6')
draw.line((128,55,128,155),fill='white',width=17)
draw.line((86,118,128,160,170,118),fill='white',width=17,joint='curve')
draw.line((65,177,65,194,191,194,191,177),fill='white',width=13,joint='curve')
image.save(out/'OpenDownload.ico',sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
