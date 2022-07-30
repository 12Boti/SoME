from manim import *
import math

from matplotlib import image

#manim test.py -pqm CreateConcavePolygon

#The points of the concave polygon
points = [
    [1, 3, 0], 
    [0, 2, 0], 
    [0, 0, 0], 
    [-3, 0, 0], 
    [-1, -1, 0], 
    [0, -3, 0], 
    [1, -1, 0], 
    [4, 0, 0],  
    [2, 1, 0],
]

class CreateCircle(Scene):
    def construct(self):

        circle = Circle()  # create a circle

        hexagon = RegularPolygon(6)
        hexagon.set_fill(BLUE, opacity = 0.75)
        hexagon.set_stroke(GREEN, opacity = 1)

        self.play(Create(hexagon)) 
        self.play(Rotate(hexagon))
        self.play(Transform(hexagon, circle))
        self.play(circle.animate.set_fill(DARK_BROWN, opacity = 1))

# For two points `a` and `b`, return True if the entire polygon is on one side
# of the AB line. Otherwise, return False.
def convexCheck(a: list, b: list) -> bool:

    check = 0 # -1 => on left side, 0 => on the line, 1 => on the right side 
    if (a[0] == b[0]):
        
        for p in points:

            if (p[0] < a[0]):

                if (check == 1):
                    return False
                else:
                    check = -1

            elif (p[0] > a[0]):

                if (check == -1):
                    return False
                else:
                    check = 1

        return True 

    else:
        c = [a[0]-b[0], a[1]-b[1], a[2]-b[2]]
        for p in points:
            d = [p[0]-b[0], p[1]-b[1], p[2]-b[2]]
            if (c[0]*d[1] - c[1]*d[0] < 0): # cross product
                if (check == 1):
                    return False
                else :
                    check = -1

            elif c[0]*d[1] - c[1]*d[0] > 0:
                if (check == -1):
                    return False
                else:
                    check = 1
        return True

#Flips between a and b points, sets the coordinates in the points list
def flip(a: list, b: list):
    if a[0] == b[0]:
        while i % len(points) != points.index(b):

            d = points[i % len(points)][0] - b[0] # distance
            points[i % len(points)][0] += 2 * d

            i += 1
    else:
        m = (b[1] - a[1]) / (b[0] - a[0]) # slope
        c = (b[0] * a[1] - a[0] * b[1]) / (b[0] - a[0]) # intercept

        i = points.index(a) + 1
        while i % len(points) != points.index(b):

            d = (points[i % len(points)][0] + (points[i % len(points)][1] - c) * m) / (1 + m * m) # distance

            points[i % len(points)][0] = 2 * d - points[i % len(points)][0]
            points[i % len(points)][1] = 2 * d * m - points[i % len(points)][1] + 2 * c

            i += 1

#Returns the points of the polygon defined by the 
def getHullPoints(points: list) -> list:
    
   # Dani code:
    hull_points = []
    first = min(points)
    first_index = points.index(first)
    hull_points.append(points[first_index])
    last = first_index
    i = first_index + 1

    while i != first_index:
        if convexCheck(points[last], points[i]):
           hull_points.append(points[i])
           last = i
        i = (i + 1)%len(points)

    return hull_points

#Calculates camera scale from the polygon's size
def getCameraWidth(points: list) -> int:
    
    multiplyer = 3  # <- modify this to change scale multiplyer

    return (max(points)[0] - min(points)[0]) * multiplyer

def findFlip():
    c = 2
    i = 0
    while c <= len(points) / 2:
        while i <= len(points)-1:
            if convexCheck(points[i], points[(i+c) % len(points)]):
                flip(points[i], points[(i+c) % len(points)])

                return True
            i += 1
        c += 1
        i = 0
    print("It's convex!")
    return False
        

#Runned class, contains all animations
class CreateConcavePolygon(MovingCameraScene):
    def construct(self):

        concave = Polygon(*points, color = GREEN) # Create Frank
        concave.set_fill(GREEN_B, opacity=0.75)

        self.play(FadeIn(concave), run_time = 2) # Show Frank on screen
        self.wait(2)

        hull = Polygon(*getHullPoints(points)) # Create convex hull
        hull.set_stroke(RED_C)

        self.play(Create(hull)) # show the hull on screen
        self.wait(2)

        while findFlip():

          flipped = Polygon(*points, color = GREEN)
          flipped.set_fill(GREEN_B, opacity=0.75)

          flipped_hull = Polygon(*getHullPoints(points))
          flipped_hull.set_stroke(RED_C)

          self.play(
                Transform(concave, flipped),
                Transform(hull, flipped_hull,), 
              )
          self.play(self.camera.frame.animate.move_to(flipped).set(width = getCameraWidth(points)))
          self.wait(0.5)

class Image(Scene):
    def construct(self):
        
        image = ImageMobject("D:\Sebi\Árpád\matek\SoME\erdos.jpg")
        image.height = 10
        self.play(FadeIn(image))
        self.wait(5)