from audioop import reverse
import math
from dataclasses import dataclass
from functools import total_ordering
from typing import Sequence, overload, Union
from copy import deepcopy

import manim.utils.color as colors  # type: ignore
import manim
from manim import (
    Arrow,
    Create,
    DashedLine,
    Dot,
    FadeIn,
    FadeOut,
    ImageMobject,
    Line,
    MovingCameraScene,
    Polygon,
    ReplacementTransform,
    Restore,
    Scene,
    ShowPassingFlash,
    Transform,
    Uncreate,
    VGroup,
    CurvedArrow,
    VMobject,
    Rotate,
    PI,
)


@dataclass
@total_ordering
class Point(Sequence[float]):
    x: float
    y: float
    z: float

    @overload
    def __getitem__(self, i: int) -> float:
        pass

    @overload
    def __getitem__(self, i: slice) -> Sequence[float]:
        pass

    def __getitem__(self, i: Union[int, slice]) -> Union[float, Sequence[float]]:
        return [self.x, self.y, self.z][i]

    def __len__(self) -> int:
        return 3

    def __setitem__(self, i: int, v: float) -> None:
        if i == 0:
            self.x = v
        elif i == 1:
            self.y = v
        elif i == 2:
            self.z = v
        else:
            raise KeyError()

    def __lt__(self, other: "Point") -> bool:
        return [self.x, self.y, self.z] < [other.x, other.y, other.z]


fill_color = colors.BLUE_D
stroke_color = colors.BLUE_E
hull_color = colors.PURE_RED
highlight_color = colors.RED

# For two points `a` and `b`, return True if the entire polygon is on one side
# of the AB line. Otherwise, return False.
def convexCheck(a: Point, b: Point, points: list[Point]) -> bool:

    check = 0  # -1 => on left side, 0 => on the line, 1 => on the right side
    if a.x == b.x:

        for p in points:

            if p.x < a.x:

                if check == 1:
                    return False
                else:
                    check = -1

            elif p.x > a.x:

                if check == -1:
                    return False
                else:
                    check = 1

        return True

    else:
        c = Point(a.x - b.x, a.y - b.y, a.z - b.z)
        for p in points:
            d = Point(p.x - b.x, p.y - b.y, p.z - b.z)
            if c.x * d.y - c.y * d.x < 0:  # cross product
                if check == 1:
                    return False
                else:
                    check = -1

            elif c.x * d.y - c.y * d.x > 0:
                if check == -1:
                    return False
                else:
                    check = 1
        return True


# Flips between a and b points, sets the coordinates in the points list
def flip(a: Point, b: Point, points: list[Point]) -> None:
    i = points.index(a) + 1

    if a.x == b.x:
        while i % len(points) != points.index(b):

            d = points[i % len(points)].x - b.x  # distance
            points[i % len(points)].x += 2 * d

            i += 1
    else:
        m = (b.y - a.y) / (b.x - a.x)  # slope
        c = (b.x * a.y - a.x * b.y) / (b.x - a.x)  # intercept

        while i % len(points) != points.index(b):

            d = (points[i % len(points)].x + (points[i % len(points)].y - c) * m) / (
                1 + m * m
            )  # distance

            points[i % len(points)].x = 2 * d - points[i % len(points)].x
            points[i % len(points)].y = 2 * d * m - points[i % len(points)].y + 2 * c

            i += 1


# Project points in `points` between the indices a and b on the line defined by the point a and b
def projectPointsOnLine(a: int, b: int, points: list[Point]) -> list[Point]:
    c = b
    if a > b:
        c = b + len(points)
    result = []
    v1 = Point(
        points[a].x - points[b].x,
        points[a].y - points[b].y,
        points[a].z - points[b].z,
    )
    v1Length = math.sqrt(v1.x**2 + v1.y**2 + v1.z**2)
    for p in (points * 2)[a + 1 : c]:
        v2 = Point(p.x - points[b].x, p.y - points[b].y, p.z - points[b].z)
        dotProduct = v1.x * v2.x + v1.y * v2.y + v1.z * v2.z
        lengthfactor = dotProduct / (v1Length**2)
        if lengthfactor < 0:
            lengthfactor = 0
        elif lengthfactor > 1:
            lengthfactor = 1
        projectedP = [x * lengthfactor + y for x, y in zip(v1, points[b])]
        result.append(Point(*projectedP))
    return result


def rotateList(l: list[Point], first_index: int) -> list[Point]:
    return l[first_index:] + l[:first_index]


# Returns the points of the convex hull of the polygon defined by the given list
def getHullPoints(points: list[Point]) -> list[Point]:

    hull_points = []
    first = min(points)
    first_index = points.index(first)
    hull_points.append(points[first_index])
    last = first_index
    i = first_index + 1

    while i != first_index:
        if convexCheck(points[last], points[i], points):
            hull_points += projectPointsOnLine(last, i, points)
            hull_points.append(points[i])
            last = i
        i = (i + 1) % len(points)
    hull_points += projectPointsOnLine(last, first_index, points)
    hull_points = rotateList(hull_points, len(points) - first_index)
    return hull_points


# Calculates camera scale from the polygon's size
def getCameraWidth(points: list[Point]) -> float:

    multiplier = 2  # <- modify this to change scale

    return (max(points).x - min(points).x) * multiplier


# Finds a flip and executes it, and returns whether the polygon is concave after the flip
def findFlip(points: list[Point]) -> bool:
    c = 2
    i = 0
    while c <= len(points) / 2:
        while i <= len(points) - 1:
            if convexCheck(points[i], points[(i + c) % len(points)], points):
                flip(points[i], points[(i + c) % len(points)], points)

                return True
            i += 1
        c += 1
        i = 0
    print("It's convex!")
    return False


# Generates dashed lines between the given points, returns the lines in a VGroup
def generateDashedLines(points: list[Point]) -> VGroup:

    storage = []

    for i in range(len(points)):
        storage.append(DashedLine(points[i - 1], points[i], color=stroke_color))

    return VGroup(*storage)


# Finds the midpoint of the line segment defind by a and b points
def findMidPoint(a: Point, b: Point) -> Point:
    return Point(*((c + d) / 2 for c, d in zip(a, b)))


# Main class, contains all animations
class CreateConcavePolygon(MovingCameraScene):  # type: ignore
    def construct(self) -> None:
        # --- Create Frank ---
        Frank_points = [
            Point(1, 3, 0),
            Point(0, 2, 0),
            Point(0, 0, 0),
            Point(-3, 0, 0),
            Point(-1, -1, 0),
            Point(0, -3, 0),
            Point(1, -1, 0),
            Point(4, 0, 0),
            Point(2, 1, 0),
        ]
        concave = Polygon(*Frank_points, color=stroke_color)
        concave.set_fill(fill_color, opacity=0.75)
        concave.save_state()
        self.play(FadeIn(concave), run_time=2)
        self.wait(2)


        # --- Dragging Frank's points to make him convex (Cheating) ---
        convex_frank = [
            Point(1, 3, 0),
            Point(0, 3, 0),
            Point(-2, 1.5, 0),
            Point(-3, 0, 0),
            Point(-2.5, -2, 0),
            Point(0, -3, 0),
            Point(3.5, -3, 0),
            Point(4, 0, 0),
            Point(3, 2.5, 0),
        ]
        wrong_convex = Polygon(*convex_frank, color=stroke_color)
        wrong_convex.set_fill(fill_color, opacity=0.75)
        self.play(Transform(concave, wrong_convex))  # Frank -> Deformed Frank
        self.wait(3)
        self.play(Restore(concave))  # Deformed Frank -> Frank


        # --- Demonstrate flip ---
        self.play(
            self.camera.frame.animate.move_to([2.5, 1.5, 0.0]).set(
                width=10
            )
        )
        axis = Line(Frank_points[0], Frank_points[7], color=colors.RED)
        self.play(Create(axis))
        orig = deepcopy(Frank_points[8])
        flip(Frank_points[7], Frank_points[0], Frank_points)
        dashed = DashedLine(orig, Frank_points[8], color=colors.RED)
        self.play(Create(dashed))
        dot = Dot(Frank_points[8], color=colors.RED)
        self.add(dot)
        #self.play(Rotate(dashed, angle=0, run_time=0)) #To do fix: wtf Calling this function somehow reverses the animation of uncreate. (As it turns out each dash uncreates in the wrong direction.)
        #self.play(Uncreate(axis, run_time=0))
        axis2 = Line(Frank_points[0], Frank_points[7], color=colors.RED)
        flipped = Polygon(*Frank_points, color=stroke_color)
        flipped.set_fill(fill_color, opacity=0.75)
        self.play(
            manim.AnimationGroup(
                Uncreate(axis, run_time=0),
                Create(axis2, run_time=0.00000000000000001, rate_func=manim.rate_functions.linear), #I don't konw why this works but OH MY GOD this took way too long!
                Uncreate(dashed, run_time=1, reverse = False, rate_func=manim.rate_functions.linear), #New discovery: If the uncreate's rate function is not specified, then even though the transfrom's rate function is set to linear it will be smooth.
                Transform(concave, flipped, run_time=1, rate_func=manim.rate_functions.linear),
                lag_ratio=0.05,
            )
        )
        self.remove(dot)
        self.play(Uncreate(axis2))
        return


        # --- Flip Frank, killing him ---
        flip(Frank_points[0], Frank_points[4], Frank_points)  # Flip randonly

        self_intersect = Polygon(
            *Frank_points, color=stroke_color
        )  # Create self-intersecting "polygon"
        self_intersect.set_fill(fill_color, opacity=0.75)
        self.play(Transform(concave, self_intersect))  # Execute flip
        self.wait(0.5)
        dashed = generateDashedLines(
            Frank_points
        )  # Generate dashed outline of the filpped polygon
        self.play(
            ReplacementTransform(concave, dashed)
        )  # Show dashed oultine (probably buggy, but looks cool)
        self.play(FadeOut(dashed))  # Fade out dashed outline
        self.wait(1)


        # --- Create Frank2 ---
        Frank_2_points = [  # Define the points for Frank 2
            Point(0, 4, 0),
            Point(-1, 0, 0),
            Point(-1, 2, 0),
            Point(-2, 3, 0),
            Point(-3, 1, 0),
            Point(-1, -1, 0),
            Point(-5, -1, 0),
            Point(-3, -2, 0),
            Point(2, 0, 0),
            Point(0, 1, 0),
        ]
        concave = Polygon(*Frank_2_points, color=stroke_color)  # Create Frank 2
        concave.set_fill(fill_color, opacity=0.75)
        concave.save_state()
        copy_of_frank_2 = Polygon(*Frank_2_points, color=highlight_color)
        self.play(
            self.camera.frame.animate.move_to(concave).set(
                width=getCameraWidth(Frank_2_points)
            )
        )
        self.play(Create(concave))  # Show Frank 2


        # --- Create Frank2's hull ---
        hull = Polygon(*getHullPoints(Frank_2_points))
        hull.set_stroke(hull_color)
        self.bring_to_front(hull)  # Put the hull in front of the polygon
        self.play(Create(hull))
        self.wait(2)
        self.play(
            self.camera.frame.animate.move_to([-3.8, 2.2, 0.0]).set(
                width=22
            )
        )

        # --- Automatically convexifies Frank2 ---
        while findFlip(Frank_2_points):

            # Create the polygon after the flip
            flipped = Polygon(
                *Frank_2_points, color=stroke_color
            )
            flipped.set_fill(fill_color, opacity=0.75)

            # Recalculate the hull after the flip
            flipped_hull = Polygon(
                *getHullPoints(Frank_2_points)
            )
            flipped_hull.set_stroke(hull_color)

            self.play(
                Transform(concave, flipped),
                Transform(
                    hull,
                    flipped_hull,
                ),
            )


        # --- Reset Frank 2 ---
        Frank_2_points = [
            Point(0, 4, 0),
            Point(-1, 0, 0),
            Point(-1, 2, 0),
            Point(-2, 3, 0),
            Point(-3, 1, 0),
            Point(-1, -1, 0),
            Point(-5, -1, 0),
            Point(-3, -2, 0),
            Point(2, 0, 0),
            Point(0, 1, 0),
        ]
        self.play(Uncreate(hull), Restore(concave))
        self.play(
            self.camera.frame.animate.move_to(concave).set(
                width=getCameraWidth(Frank_2_points)
            )
        )


        # --- Show that perimeter is constant ---
        self.play(
            ShowPassingFlash(
                copy_of_frank_2.copy().set_color(highlight_color),
                run_time=2,
                time_width=1,
            )
        )  
        self.wait(2)
        prev_lines = VMobject(color=highlight_color).set_points_as_corners([
            Frank_2_points[0],
            Frank_2_points[9],
            Frank_2_points[8],
        ])
        point_before_flip = deepcopy(Frank_2_points[9])
        flip(Frank_2_points[8], Frank_2_points[0], Frank_2_points)
        flipped = Polygon(*Frank_2_points, color=stroke_color)
        flipped.set_fill(fill_color, opacity=0.75)
        self.play(Create(prev_lines))
        self.wait(1)
        self.play(Transform(concave, flipped))
        arrow_a = CurvedArrow(
            findMidPoint(Frank_2_points[0], point_before_flip),
            findMidPoint(Frank_2_points[0], Frank_2_points[9]),
            color=highlight_color,
        )
        arrow_b = CurvedArrow(
            findMidPoint(point_before_flip, Frank_2_points[8]),
            findMidPoint(Frank_2_points[8], Frank_2_points[9]),
            radius=-1,
            color=highlight_color,
        )
        self.play(Create(arrow_a))
        self.play(Create(arrow_b))
        self.wait(2)


class Image(Scene):  # type: ignore
    def construct(self) -> None:

        image = ImageMobject(r"D:\Sebi\Árpád\matek\SoME\erdos.jpg")
        image.height = 10
        self.play(FadeIn(image))
        self.wait(5)
