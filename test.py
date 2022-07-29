from manim import *
import math

#manim test.py -pqm CreateCircl
    
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

        m = (b[1] - a[1]) / (b[0] - a[0]) # slope
        c = (b[0] * a[1] - a[0] * b[1]) / (b[0] - a[0]) # intercept
        for p in points:

            if (p[1] < math.floor(m * p[0] + c)): # floor due to float's inaccuracy
                if (check == 1):
                    return False
                else :
                    check = -1

            elif (p[1] > math.ceil(m * p[0] + c)): # ceil due to float's inaccuracy
                if (check == -1):
                    return False
                else:
                    check = 1

        return True

class CreateConcavePolygon(Scene):
    def construct(self):

        concave = Polygon(*points, color = GREEN)
        concave.set_fill(GREEN_B, opacity=0.75)

        self.play(FadeIn(concave), run_time = 2)
        self.wait(2)

        # Dani code:
        hull_points = []
        first = False
        for i in range(len(points)-1):
            for j in range(i+1, len(points)):
                if convexCheck(points[i], points[j]):
                    if not first:
                        hull_points.append(points[i])
                        hull_points.append(points[j])
                        i = j
                        first = True
                        continue
                    else:
                        hull_points.append(points[j])
                        continue

        hull = Polygon(*hull_points)
        hull.set_stroke(RED_E, 5)

        self.play(Create(hull))
        self.wait(10)