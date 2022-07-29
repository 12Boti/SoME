from manim import *

#manim test.py -pqm CreateCircle

'''class Point:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
    
    points = [Point(1, 3, 0), Point(0, 2, 0), Point(0, 0, 0), Point(-3, 0, 0), Point(-1, -1, 0), Point(0, -3, 0), Point(1, -1, 0), Point(4, 0, 0),  Point(2, 1, 0)]'''

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

''''def convexCheck(a:list, b:list):
    check = 0 #-1 => smaller, 0 => equals, 1 => greater
    if (a[0] == b[0]) :
        for i in range(len(Point.points)):
            if (Point.points[i].x < a.x):
                if (check == 1):
                    return False
                else:
                    check = -1
            elif (Point.points[i].x > a.x):
                if (check == -1):
                    return False
                else:
                    check = 1
        return True 
    else:
        m = (b.y - a.y) / (b.x - a.x) # y = mx + c
        c = (b.x * a.y - a.x * b.y) / (b.x - a.x)
        for i in range(len(Point.points)):
            if (Point.points[i].y < math.floor(m * Point.points[i].x + c)):
                if (check == 1):
                    return False
                else :
                    check = -1
            elif (Point.points[i].y > math.ceil(m * Point.points[i].x + c)):
                if (check == -1):
                    return False
                else:
                    check = 1
        return True'''

class CreateConcavePolygon(Scene):
    def construct(self):

        concave = Polygon(*Point.points, color = GREEN)
        concave.set_fill(GREEN_B, opacity=0.75)

        self.play(Create(concave), run_time = 3)
        self.wait(10)