from pptx import Presentation
from pptx.util import Cm
from pathlib import Path
  
# Creating presentation object
presentation = Presentation()
presentation.slide_width = Cm(6.35) # Cm(12.7) # Cm(25.4)
presentation.slide_height = Cm(4.7625) # Cm(9.525) # Cm(19.05)
  
# Creating slide layout
first_slide_layout = presentation.slide_layouts[6] 
  
""" Ref for slide types: 
0 ->  title and subtitle
1 ->  title and content
2 ->  section header
3 ->  two content
4 ->  Comparison
5 ->  Title only 
6 ->  Blank
7 ->  Content with caption
8 ->  Pic with caption
"""

left = top = Cm(0)
width = presentation.slide_width # Cm(25.4)
#height = Cm(19.05)
  
for img_path in sorted(Path(r'./').glob('frame_*.jpg'), key=lambda path: float(path.stem.rsplit("_", 1)[1])):
    slide = presentation.slides.add_slide(first_slide_layout)
    pic = slide.shapes.add_picture(str(img_path), left, top, width=width)
  
presentation.save("story.pptx")
