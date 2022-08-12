import math
import random
from copy import deepcopy
from dataclasses import dataclass
from functools import total_ordering
from typing import Sequence, Union, overload

import manim  # type: ignore
import manim.utils.color as colors  # type: ignore
from manim import (
    PI,
    ArcPolygon,
    Arrow,
    Circle,
    Create,
    CurvedArrow,
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
    Rotate,
    Scene,
    ShowPassingFlash,
    Text,
    Transform,
    Uncreate,
    Unwrite,
    VGroup,
    VMobject,
    Write,
    register_font,
)


@dataclass
@total_ordering
class Point(Sequence[float]):
    x: float
    y: float
    z: float

    def distanceFrom(self, p) -> float:
        return math.sqrt((self.x - p.x)**2 + (self.y - p.y)**2 + (self.z - p.z)**2)
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
        points[b].x - points[a].x,
        points[b].y - points[a].y,
        points[b].z - points[a].z,
    )
    v1Length = math.sqrt(v1.x**2 + v1.y**2 + v1.z**2)
    prev_lengthfactor = 0.0
    for p in (points * 2)[a + 1 : c]:
        v2 = Point(p.x - points[a].x, p.y - points[a].y, p.z - points[a].z)
        dotProduct = v1.x * v2.x + v1.y * v2.y + v1.z * v2.z
        lengthfactor = dotProduct / (v1Length**2)
        if lengthfactor < prev_lengthfactor:
            lengthfactor = prev_lengthfactor
        elif lengthfactor > 1:
            lengthfactor = 1
        prev_lengthfactor = lengthfactor
        projectedP = [x * lengthfactor + y for x, y in zip(v1, points[a])]
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
        self.play(self.camera.frame.animate.move_to([2.5, 1.5, 0.0]).set(width=10))
        axis = Line(Frank_points[0], Frank_points[7], color=colors.RED)
        self.play(Create(axis))
        orig = deepcopy(Frank_points[8])
        flip(Frank_points[7], Frank_points[0], Frank_points)
        dashed = DashedLine(orig, Frank_points[8], color=colors.RED)
        self.play(Create(dashed))
        dot = Dot(Frank_points[8], color=colors.RED)
        self.add(dot)
        # self.play(Rotate(dashed, angle=0, run_time=0)) #To do fix: wtf Calling this function somehow reverses the animation of uncreate. (As it turns out each dash uncreates in the wrong direction.)
        # self.play(Uncreate(axis, run_time=0))
        axis2 = Line(Frank_points[0], Frank_points[7], color=colors.RED)
        flipped = Polygon(*Frank_points, color=stroke_color)
        flipped.set_fill(fill_color, opacity=0.75)
        self.play(
            manim.AnimationGroup(
                Uncreate(axis, run_time=0),
                Create(
                    axis2,
                    run_time=0.00000000000000001,
                    rate_func=manim.rate_functions.linear,
                ),  # Bring axis to front. I don't konw why this works but OH MY GOD this took way too long! (these attempts failed: self.bring_to_front(axis), self.bring_to_back(concave), changing the z coordinates)
                Uncreate(
                    dashed,
                    run_time=1,
                    reverse=False,
                    rate_func=manim.rate_functions.linear,
                ),  # New discovery: If the uncreate's rate function is not specified, then even though the transfrom's rate function is set to linear it will be smooth.
                Transform(
                    concave,
                    flipped,
                    run_time=1,
                    rate_func=manim.rate_functions.linear,
                ),
                lag_ratio=0.05,
            )
        )
        self.remove(dot)
        self.play(Uncreate(axis2))
        self.play(self.camera.frame.animate.move_to([0, 0, 0.0]).set(width=128 / 9))

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
        hull_points = getHullPoints(Frank_2_points)
        # rubber band animation
        band_points = []
        band_center = Point(-1, 0, 0)
        # project each hull point onto a circle
        for p in hull_points:
            length = math.sqrt((p.x - band_center.x) ** 2 + (p.y - band_center.y) ** 2)
            band_points.append(
                Point(*[(x - y) / length * 4.5 + y for x, y in zip(p, band_center)])
            )
        band = ArcPolygon(*band_points, color=hull_color)
        band.make_smooth()
        for arc in band.submobjects:
            self.play(Uncreate(arc, run_time=0))  # render bugs without this
        hull = Polygon(*hull_points)
        hull.set_stroke(hull_color)
        self.play(Create(band))
        self.play(Transform(band, hull), rate_func=manim.rate_functions.ease_out_elastic)
        self.wait(2)
        self.play(self.camera.frame.animate.move_to([-3.8, 2.2, 0.0]).set(width=22))
        self.remove(band)

        # --- Automatically convexifies Frank2 ---
        while findFlip(Frank_2_points):

            # Create the polygon after the flip
            flipped = Polygon(*Frank_2_points, color=stroke_color)
            flipped.set_fill(fill_color, opacity=0.75)

            # Recalculate the hull after the flip
            flipped_hull = Polygon(*getHullPoints(Frank_2_points))
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
        prev_lines = VMobject(color=highlight_color).set_points_as_corners(
            [
                Frank_2_points[0],
                Frank_2_points[9],
                Frank_2_points[8],
            ]
        )
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
        self.play(
            Uncreate(prev_lines),
            Uncreate(arrow_a),
            Uncreate(arrow_b),
            Restore(concave),
        )
        self.wait(2)

        # --- Show that distance increases ---
        inner_point = Point(1, 0, 0)
        inner_dot = Dot(inner_point, color=colors.GREEN)
        prev_dot = Dot(point_before_flip, color=colors.RED)
        next_dot = Dot(Frank_2_points[9], color=colors.RED)
        axis = Line(Frank_2_points[0], Frank_2_points[8], color=colors.RED)
        axis.set_length(100)
        self.play(FadeIn(inner_dot))
        self.wait(2)
        self.play(FadeIn(prev_dot))
        self.play(FadeIn(next_dot))
        self.play(FadeIn(axis))
        self.play(Transform(concave, flipped))
        self.wait(2)
        intersect_point = Point(1.56, 0.88, 0)
        # create the entire line as one object to make the create animation smooth
        full_line = Line(inner_point, Frank_2_points[9], color=colors.GREEN)
        other_line = Line(inner_point, point_before_flip, color=colors.YELLOW)
        inner_dot2 = Dot(inner_point, color=colors.GREEN)
        prev_dot2 = Dot(point_before_flip, color=colors.RED)
        next_dot2 = Dot(Frank_2_points[9], color=colors.RED)
        self.play(
            Create(full_line), Create(other_line),
            FadeOut(
                inner_dot,
                prev_dot,
                next_dot,
            ),
            FadeIn(inner_dot2, run_time=0.00000000000000000000001),
            FadeIn(prev_dot2, run_time=0.00000000000000000000001),
            FadeIn(next_dot2, run_time=0.00000000000000000000001),
            )
        line_half_1 = Line(inner_point, intersect_point, color=colors.GREEN)
        line_half_2 = Line(intersect_point, Frank_2_points[9], color=colors.GREEN)
        self.add(line_half_1, line_half_2)
        self.remove(full_line)
        self.remove(next_dot2)
        self.add(next_dot2)
        self.wait(1)
        line_half_2_next = Line(intersect_point, point_before_flip, color=colors.GREEN)
        line_half_2_dashed = DashedLine(
            intersect_point, Frank_2_points[9], color=colors.GREEN
        )
        self.add(line_half_2_dashed)
        inner_dot3 = Dot(inner_point, color=colors.GREEN)
        prev_dot3 = Dot(point_before_flip, color=colors.RED)
        next_dot3 = Dot(Frank_2_points[9], color=colors.RED)
        self.play(
            Transform(line_half_2, line_half_2_next),
            FadeOut(
                inner_dot2,
                prev_dot2,
                next_dot2,
            ),
            FadeIn(inner_dot3, run_time=0.00000000000000000000001),
            FadeIn(prev_dot3, run_time=0.00000000000000000000001),
            FadeIn(next_dot3, run_time=0.00000000000000000000001),
        )
        self.wait(2)
        inequality = manim.Text("+ ≥").rotate(-PI / 2).move_to([-5, 1, 0])
        line_half_1_copy = line_half_1.copy()
        line_half_2_next_copy = line_half_2_next.copy()
        other_line_copy = other_line.copy()
        self.play(
            FadeIn(inequality),
            ReplacementTransform(
                line_half_1.copy(),
                line_half_1_copy.move_to([-4, 1.35, 0]).rotate(-1),
            ),
            ReplacementTransform(
                line_half_2_next.copy(),
                line_half_2_next_copy.move_to([-6.3, 1.35, 0]).rotate(0.085),
            ),
            ReplacementTransform(
                other_line.copy(),
                other_line_copy.move_to([-5, 0, 0]).rotate(0.8),
            ),
        )
        self.wait(5)
        self.play(
            FadeOut(
                line_half_1,
                line_half_1_copy,
                line_half_2,
                line_half_2_next,
                line_half_2_next_copy,
                line_half_2_dashed,
                other_line,
                other_line_copy,
                inequality,
                #inner_dot3,
                prev_dot3,
                next_dot3,
                axis,
            ),
        )
        self.wait(2)
        #self.play(Uncreate(concave))

        # --- show vertex can't get farther than perimeter/2 ---
        Frank_2_extended_points = [
            Point(-3.224768843, 0.305669231, 0),
            Point(-7.3477603878, 0.3363404141, 0),
            Point(-9.3469458029, 0.3934164889, 0),
            Point(-10.7600924158, 0.3384924263, 0),
            Point(-12.4281440321, 0.059216225, 0),
            Point(-9.6133959371, -0.2186203491, 0),
            Point(-5.6142604062, -0.3017768587, 0),
            Point(-3.3784287974, -0.2692650573, 0),
            Point(2, 0, 0),
            Point(-0.2263518348, 0.2082246565, 0),
        ]
        frank_2_extended = Polygon(*Frank_2_extended_points, color=stroke_color)
        frank_2_extended.set_fill(fill_color, opacity=0.75)
        segment = Line(start=inner_point, end=Frank_2_points[4], color=colors.ORANGE)
        segment2 = Line(start=inner_point, end=Frank_2_extended_points[4], color=colors.ORANGE)
        dot = Dot(Frank_2_points[4], color= colors.GREEN)
        dot2 = Dot(Frank_2_extended_points[4], color= colors.GREEN)
        inner_dot4 = Dot(inner_point, color=colors.GREEN)
        self.play(Create(segment), FadeIn(dot), FadeIn(inner_dot4, run_time=0.00000000000000000000001),)
        self.play(self.camera.frame.animate.move_to([-4.8, 0.2, 0.0]).set(width=18))
        self.play(
            Transform(concave, frank_2_extended), 
            Transform(dot, dot2), 
            Transform(segment, segment2),  
        )
        self.remove(inner_dot3)
        self.wait(2)
        self.play(
            ShowPassingFlash(
                VMobject(color=highlight_color).set_points_as_corners(
                [
                    Frank_2_extended_points[4],
                    Frank_2_extended_points[5],
                    Frank_2_extended_points[6],
                    Frank_2_extended_points[7],
                    Frank_2_extended_points[8],
                ]),
                run_time=2,
                time_width=1,
            )
        )
        self.play(Uncreate(segment), FadeOut(dot,inner_dot4))
        # --- show limit exits ---
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
        Frank_2_convex_points = deepcopy(Frank_2_points)
        frank_2 = Polygon(*Frank_2_points, color=stroke_color)
        frank_2.set_fill(fill_color, opacity=0.75)
        self.play(ReplacementTransform(concave, frank_2))
        self.wait(2)
        while findFlip(Frank_2_convex_points):
            something_needs = " to be here I guess"
        frank_2_convex = Polygon(*Frank_2_convex_points, color=colors.YELLOW)
        self.play(self.camera.frame.animate.move_to([0.8, 0.2, 0.0]).set(width=32))
        dot_points = [Point(0, 0, 0), Point(-2, 1, 0), Point(-3, -1.5, 0)]
        dots = VGroup(*[Dot(x, color=colors.GREEN) for x in dot_points])
        self.play(FadeIn(dots))
        DELTA = 1
        arrows = VGroup(*[
            Arrow(
                    dot_points[x], 
                    [
                        dot_points[x].x+dot_points[x].distanceFrom(Frank_2_convex_points[DELTA]),
                        dot_points[x].y,
                        0
                    ],
                    color=colors.ORANGE
                ) 
            for x in range(len(dot_points))]
        )
        text0 = (
            Text("d₁", color=colors.ORANGE)
            .scale(0.8)
            .next_to(arrows[0])
            .shift([-0.2, 0, 0])
        )
        text1 = (
            Text("d₂", color=colors.ORANGE)
            .scale(0.8)
            .next_to(arrows[1])
            .shift([-0.2, 0, 0])
        )
        text2 = (
            Text("d₃", color=colors.ORANGE)
            .scale(0.8)
            .next_to(arrows[2])
            .shift([-0.2, 0, 0])
        )
        circles = VGroup(*[
            Circle(
                radius=x.distanceFrom(Frank_2_convex_points[DELTA]),
                arc_center=x, 
                color=colors.ORANGE
            )
            for x in dot_points
        ])
        self.play(Create(arrows, lag_ratio=0), Write(text0), Write(text1), Write(text2)) # I have no clue why the texts don't work in one Write(), but I'm too tired to care at this point.
        self.wait(2)
        self.play(Unwrite(text0), Unwrite(text1), Unwrite(text2))
        self.play(
                    *[Rotate(arrows[x], angle=2*PI, about_point=dot_points[x]) for x in range(3)], 
                    Create(circles, lag_ratio=0)
                )
        self.wait(2)
        approached = [Dot(Frank_2_convex_points[DELTA], color=colors.TEAL)]
        self.play(FadeIn(approached[-1]))
        self.wait(1)
        self.play(Uncreate(circles, lag_ratio=0))
        self.wait(1)
        for i in range(DELTA+1, len(Frank_2_points)+DELTA):
            print(i)
            approached.append(Dot(Frank_2_convex_points[i % len(Frank_2_convex_points)], color=colors.TEAL))
            arrowsb = VGroup(*[
                Arrow(
                        dot_points[x], 
                        [
                            dot_points[x].x+dot_points[x].distanceFrom(Frank_2_convex_points[i%len(Frank_2_convex_points)]),
                            dot_points[x].y,
                            0
                        ],
                        color=colors.ORANGE
                    )
                for x in range(3)]
            )
            circles = VGroup(*[
                Circle(
                    radius=x.distanceFrom(Frank_2_convex_points[i%len(Frank_2_convex_points)]),
                    arc_center=x, 
                    color=colors.ORANGE
                )
                for x in dot_points
            ])
            
            self.play(Transform(arrows, arrowsb, run_time=0.3))
            self.play(
                    *[Rotate(arrows[x], angle=2*PI, about_point=dot_points[x], run_time=0.7) for x in range(3)], 
                    Create(circles, lag_ratio=0, run_time=0.7)
                )
            self.play(FadeIn(approached[-1], run_time=0.4))
            self.play(Uncreate(circles, lag_ratio=0, run_time=0.5))
        self.wait(1)
        self.play(Create(frank_2_convex))
        self.play(Uncreate(arrows), FadeOut(dots), *[FadeOut(x) for x in approached])
        self.play(
            self.camera.frame.animate.move_to(frank_2).set(
                width=getCameraWidth(Frank_2_convex_points)
            )
        )
        self.wait(1)
        self.play(Uncreate(frank_2), Uncreate(frank_2_convex))
        

        # --- convexity tolerance ---
        self.play(self.camera.frame.animate.move_to([0, 0, 0]).set(width=128 / 9))
        with register_font("./assets/font/NewRocker-Regular.ttf"):
            a = Text("CONVEXITY TOLERANCE", font="New Rocker", font_size=70)
        self.play(Write(a, run_time=0.8))
        self.wait(1)
        self.play(Unwrite(a, run_time=0.5))
        dots = VGroup(
            Dot([0, 1, 0]),
            Dot([-3, 0, 0]),
            Dot([3, -1, 0]),
        )
        segments = VMobject(color=colors.BLUE_D).set_points_as_corners(
            [
                [-3, 0, 0],
                [0, 1, 0],
                [3, -1, 0],
            ]
        )
        self.play(FadeIn(dots))
        self.bring_to_back(segments)
        self.play(Create(segments))
        middots = VGroup(
            Dot([-1.5, 0.5, 0]),
            Dot([1.5, 0, 0]),
        )
        self.wait(1)
        self.play(FadeIn(middots))
        line = Line([-1.5, 0.5, 0], [1.5, 0, 0], color=colors.PURPLE_D)
        line.set_length(30)
        self.bring_to_back(line)
        self.play(Create(line, run_time=2))
        circle_group = manim.Group(
            Circle(radius=0.7397954428741, arc_center=[-3, 0, 0], color=colors.GREEN_E),
            Circle(radius=0.7397954428741, arc_center=[0, 1, 0], color=colors.GREEN_E),
            Circle(radius=0.7397954428741, arc_center=[3, -1, 0], color=colors.GREEN_E),
        )
        self.play(*[Create(x) for x in circle_group])
        r1 = Line([-3, 0, 0], [-3, 0.7397954428741, 0], color=colors.ORANGE)
        r2 = Line([0, 1, 0], [0, 1.7397954428741, 0], color=colors.ORANGE)
        r3 = Line([3, -1, 0], [3, -1 + 0.7397954428741, 0], color=colors.ORANGE)
        self.play(
            Create(r1),
            Create(r2),
            Create(r3),
        )
        text1 = Text("r₁", color=colors.ORANGE).scale(0.5)
        text1.move_to([0.2, 1 + 0.35, 0])
        text2 = Text("r₁", color=colors.ORANGE).scale(0.5)
        text2.move_to([-3 + 0.2, 0.35, 0])
        text3 = Text("r₁", color=colors.ORANGE).scale(0.5)
        text3.move_to([3 + 0.2, -1 + 0.35, 0])
        self.play(
            Write(text1),
            Write(text2),
            Write(text3),
        )
        self.wait(2)
        self.play(
            Unwrite(text1),
            Unwrite(text2),
            Unwrite(text3),
            Uncreate(r1),
            Uncreate(r2),
            Uncreate(r3),
            *[Uncreate(x) for x in circle_group],
            Uncreate(line),
            FadeOut(dots, middots),
            Uncreate(segments),
        )
        self.wait(2)
        Eduard_points = [
            # Point(1, 3, 0),
            Point(0, 3, 0),
            Point(-2, 1.5, 0),
            Point(-3, 0, 0),
            Point(-2.5, -2, 0),
            Point(0, -3, 0),
            Point(3.5, -3, 0),
            Point(4, 0, 0),
            Point(3, 2.5, 0),
        ]
        Eduard = Polygon(*Eduard_points, color=stroke_color)
        self.play(Create(Eduard))
        radiuses = []
        epsilon = 999999999.0
        for i in range(len(Eduard_points)):
            m1 = findMidPoint(
                Eduard_points[(i - 1) % len(Eduard_points)], Eduard_points[(i)]
            )
            m2 = findMidPoint(
                Eduard_points[(i + 1) % len(Eduard_points)], Eduard_points[(i)]
            )
            line = Line(m1, m2, color=colors.PURPLE_D)
            line.set_length(20)
            v1 = Point(
                m1.x - m2.x,
                m1.y - m2.y,
                m1.z - m2.z,
            )
            v1Length = math.sqrt(v1.x**2 + v1.y**2 + v1.z**2)
            v2 = Point(Eduard_points[(i)].x - m2.x, Eduard_points[(i)].y - m2.y, 0)
            dotProduct = v1.x * v2.x + v1.y * v2.y + v1.z * v2.z
            projectedP = Point(
                *[x * dotProduct / (v1Length**2) + y for x, y in zip(v1, m2)]
            )
            v3 = Point(
                projectedP.x - Eduard_points[i].x,
                projectedP.y - Eduard_points[i].y,
                projectedP.z - Eduard_points[i].z,
            )
            v3_length = math.sqrt(v3.x**2 + v3.y**2 + v3.z**2)
            epsilon = min(epsilon, v3_length)
            circle_group = manim.Group(
                Circle(
                    radius=v3_length,
                    arc_center=Eduard_points[(i - 1) % len(Eduard_points)],
                    color=colors.GREEN_E,
                ),
                Circle(
                    radius=v3_length, arc_center=Eduard_points[i], color=colors.GREEN_E
                ),
                Circle(
                    radius=v3_length,
                    arc_center=Eduard_points[(i + 1) % len(Eduard_points)],
                    color=colors.GREEN_E,
                ),
            )
            r1 = Line(Eduard_points[i], projectedP, color=colors.ORANGE)
            radiuses.append(r1)
            self.play(
                Create(line, run_time=0.8),
                *[Create(x, run_time=0.8) for x in circle_group],
            )
            self.play(Create(r1, run_time=0.2))
            self.play(
                *[Uncreate(x, run_time=0.5) for x in circle_group],
                Uncreate(line, run_time=0.5),
            )
        # Боже мой!
        self.wait(2)
        text0 = Text("ε", color=colors.ORANGE).scale(0.8)
        text0.move_to([-6, 3, 0])
        self.play(Write(text0))
        text1 = Text(" = Min(").scale(0.8).next_to(text0).shift([0.1, 0, 0])
        self.play(Write(text1))
        comma_shift = 0.2
        text2 = (
            Text("r₁", color=colors.ORANGE)
            .scale(0.8)
            .next_to(text1)
            .shift([-0.2, 0, 0])
        )
        text3 = Text(",").scale(0.8).next_to(text2).shift([-0.2, -comma_shift, 0])
        self.play(Transform(radiuses[0], text2), Write(text3))
        text4 = (
            Text("r₂", color=colors.ORANGE)
            .scale(0.8)
            .next_to(text3)
            .shift([-0.2, comma_shift, 0])
        )
        text5 = Text(",").scale(0.8).next_to(text4).shift([-0.2, -comma_shift, 0])
        self.play(Transform(radiuses[1], text4), Write(text5))
        text6 = (
            Text("...", color=colors.ORANGE)
            .scale(0.8)
            .next_to(text5)
            .shift([-0.2, comma_shift, 0])
        )
        text7 = Text(",").scale(0.8).next_to(text6).shift([-0.2, -comma_shift, 0])
        text8 = (
            Text("rₙ", color=colors.ORANGE)
            .scale(0.8)
            .next_to(text7)
            .shift([-0.2, comma_shift, 0])
        )
        self.play(*[Transform(x, text6) for x in radiuses[2:-1]], Write(text7))
        self.play(Transform(radiuses[-1], text8))
        text9 = Text(")").scale(0.8).next_to(text8).shift([-0.2, 0, 0])
        self.play(Write(text9))
        self.wait(2)
        self.play(
            *[
                Unwrite(t)
                for t in [text1, text2, text3, text4, text5, text6, text7, text8, text9]
                + radiuses
            ]
        )
        circles = [
            Circle(radius=epsilon, arc_center=p, color=colors.ORANGE)
            for p in Eduard_points
        ]
        self.remove(text0)
        self.play(*[ReplacementTransform(text0.copy(), c) for c in circles])
        self.wait(2)
        random.seed(3.141592)
        rage = range  # Oh Manim
        for i in rage(7):
            wiggled_points = []
            for p in Eduard_points:
                angle = random.random() * 2 * PI
                wiggled_points.append(
                    Point(
                        p.x + epsilon * math.cos(angle),
                        p.y + epsilon * math.sin(angle),
                        0
                    )
                )
            wiggled = Polygon(*wiggled_points, color=stroke_color)
            self.play(Transform(Eduard, wiggled, run_time=0.7))

        self.wait(2)
        self.play(*[Uncreate(c) for c in circles], Uncreate(Eduard))
        self.wait(2)


        # --- Proof ---
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
        frank_2 = Polygon(*Frank_2_points, color=stroke_color)
        frank_2.set_fill(fill_color, opacity=0.75)
        self.play(
            self.camera.frame.animate.move_to(frank_2).set(
                width=getCameraWidth(Frank_2_points)
            )
        )
        self.play(Create(frank_2))
        self.wait(2)
        dot_start = Dot(Frank_2_points[4], color=colors.RED)
        self.play(self.camera.frame.animate.move_to(Frank_2_points[4]).set(width=8), FadeIn(dot_start))
        hull_points = getHullPoints(Frank_2_points)
        dot_approached = Dot([-8.711058823529418,3.236235294117641,0], color=colors.GREEN)
        self.play(Create(hull))
        self.play(self.camera.frame.animate.move_to([-3.8, 2.2, 0.0]).set(width=22))
        self.wait(1)
        arrow = Arrow(
            Frank_2_points[4],
            [-8.711058823529418,3.236235294117641,0],
            color=colors.GOLD,
        )
        self.wait(1)
        self.play(FadeIn(dot_approached))
        self.wait(1)
        self.play(Create(arrow))
        self.wait(1)
        c = Circle(radius=0.5, arc_center=[-8.711058823529418,3.236235294117641,0], color=colors.ORANGE)
        self.play(Create(c))
        while findFlip(Frank_2_points):

            # Create the polygon after the flip
            flipped = Polygon(*Frank_2_points, color=stroke_color)
            flipped.set_fill(fill_color, opacity=0.75)
            dot_start_2 = Dot(Frank_2_points[4], color=colors.RED)
            arrow2 = Arrow(
                Frank_2_points[4],
                [-8.711058823529418,3.236235294117641,0],
                color=colors.GOLD,
            )
            self.play(
                Transform(frank_2, flipped),
                Transform(dot_start, dot_start_2),
                Transform(arrow, arrow2),
            )
        self.play(
            self.camera.frame.animate.move_to(Frank_2_points[4]).set(
                width=5
            )
        )
        dot_approached_highlight = Dot([-8.711058823529418,3.236235294117641,0], color=colors.YELLOW_C)
        self.wait(1)
        self.play(FadeIn(dot_approached_highlight))
        self.play(FadeOut(dot_approached_highlight))
        self.wait(2)
        self.play(self.camera.frame.animate.move_to([-3.8, 2.2, 0.0]).set(width=22))
        self.wait(1)
        self.play(Uncreate(frank_2, arrow),FadeOut(dot_start,dot_approached), Uncreate(c)) #For some mysterious reason c must be in a seperate Uncreate() for it to work
        self.wait(2)

#class Image(Scene):  # type: ignore
#    def construct(self) -> None:
#
#        image = ImageMobject(r"D:\Sebi\Árpád\matek\SoME\erdos.jpg")
#        image.height = 10
#        self.play(FadeIn(image))
#        self.wait(5)
