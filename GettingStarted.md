# Install #
See the instructions in the [README](http://pynguin.googlecode.com/hg/README) file.

Windows users may want to look at InstallingPynguinOnWindows


# More functions video #

<a href='http://www.youtube.com/watch?feature=player_embedded&v=fjj9LTJYp5U' target='_blank'><img src='http://img.youtube.com/vi/fjj9LTJYp5U/0.jpg' width='425' height=344 /></a>


# Interface #
  * **left side** (The canvas) The pynguin lives over here. Give commands and write programs and watch the pynguin move around and draw here.

  * **top right** (Code editor) Write programs and create new functions for the pynguin here.

  * **bottom right** (Interactive console) Give commands here.


# Commands #
## draw ##
`forward(distance)` : Move the pynguin ahead by the given distance. _distance_ should be a number.

`fd(distance)` : Same as `forward(distance)`

`backward(distance)` : Move the pynguin back by the given distance.

`bk(distance)` : Same as `backward(distance)`

`lineto(x, y)` : Draw a line from the current location to the given coordinates. Line is drawn even if pen has been deactivated with `penup()`

`penup()` : Deactivate the pen. Makes the pynguin not draw while moving.

`pendown()` : Activate the pen. The pynguin will draw lines while moving.

`speed(string)` : Change how quickly the pynguin moves around the drawing. Choices available are: `'slow'`, `'medium'`, `'fast'`, `'instant'`. Note that `'instant'` really means 'as fast as possible'.

`track()` : Keep the pynguin centered in the view as it moves around. Note that it is only the main pynguin that will be tracked, even if it is a different pynguin that calls the `track()` method. To track a different pynguin, `promote()` it first.

`notrack()` : Stop tracking the main pynguin.


## turn ##
`right(degrees)` : Turn clockwise by given angle. _degrees_ should be a number.

`rt(degrees)` : Same as `right(degrees)`

`left(degrees)` : Turn counter-clockwise by given angle.

`lt(degrees)` : Same as `left(degrees)`

`turnto(degrees)` : Set the heading to the given angle.

`h(degrees)` : Same as `turnto(degrees)`

`toward(x, y)` : Turn to face the given coordinates.

See also: [GettingStarted#Properties](GettingStarted#Properties.md)



## move ##
`goto(x, y)` : Move to the given coordinates. No line is drawn, no matter what the current state of the pen is.

`xy(x, y)` : Same as `goto(x, y)`

`home()` : Move to the home location `(0, 0)`

`reset()` : Clear the canvas and set all pynguin attributes to their initial conditions.

`clear()` : Remove anything that was drawn by the main pynguin.

See also: [GettingStarted#Properties](GettingStarted#Properties.md)



## info ##
`xy()` : Return the current location as a 2-tuple.

`xyh()` : Return the current location and heading as a 3-tuple.

`h()` : Return the current heading.

`distance(x, y)` : Return the distance to the given coordinate.

`xyforward(distance)` : Return the location where the pynguin would be if it went `forward(distance)`

`onscreen()` : Return True if the pynguin is positioned on the canvas.

`viewcoords()` : Return the coordinates of the corners of the canvas as a 4-tuple `(xmin, ymin, xmax, ymax)`.

See also: [GettingStarted#Properties](GettingStarted#Properties.md)



## style ##
`color(string)` : Change the color of drawn lines. _string_ can be the name of a color (like `'red'`, `'green'`, `'blue'`) or an html-style hex color triple (like `'#FF0000'`, `'#00FF00'`, `'#0000FF'`) or choose a random color with the word `'random'`. (Can also choose a light, medium or dark random color with `'rlight'`, `'rmedium'`, or `'rdark'`)

`color(red, green, blue)` : Change the color of drawn lines. Each of _red_, _green_, and _blue_ should be an integer between 0 and 255.

`bgcolor(string)` : Set the background color. Color choices are the same as those for `color(string)`.

`bgcolor(red, green, blue)` : Set the background color.

`width(px)` : Change the width of drawn lines to the specified size. _px_ should be a number.

`fill()` : Add color to the interior space of drawn lines.

`fill(color=...)` : Start filling, and also change the fill color. The color
> parameter can be a string as in calling `color(string)` or a 3-tuple of
> (red, green, blue).

`nofill()` : Turn off filling.

`font()` : Return the current font object being used to draw text. This is a Qt font and methods can be called on it to change the font style.

`font(family=..., size=..., weight=..., italic=...)` : Some characteristics of the current font can be set this way. family is a string like 'Arial' or 'Courier', size is a number, weight is a number between 0 and 99, italic is a boolean.

# Shapes and random colors video #

<a href='http://www.youtube.com/watch?feature=player_embedded&v=7SNNQi7Lw2E' target='_blank'><img src='http://img.youtube.com/vi/7SNNQi7Lw2E/0.jpg' width='425' height=344 /></a>

## shapes ##
`circle(radius, center?)` : Draw a circle with given _radius_. If _center_ is included and is `True`, center the circle on the current location.

`arc(radius, extent, center?, move?, pie?)` : Draw a circular arc with given _radius_ and _extent_. If _center_ is `True` the arc will be centered on the initial location. If _move_ is `True` the pynguin will either go to the end of the drawn arc, or if _center_ is also `True` will finish facing towards the end of the drawn arc. If _pie_ is `True` the arc will be the circular edge of a pie-shaped figure.

`square(size, center?)` : Draw a square with side length _size_. If _center_ is included and is `True`, center the square on the current location.

`write(text)` : Draw the given _text_ string at the current location.

`avatar(string)` : Set the pynguin's onscreen representation to the given choice. Choices for _string_ include `'pynguin'`, `'arrow'`, `'robot'`, and `'turtle'`. Custom avatars can also be set this way. For help with the syntax, try using the `View -> Custom -> Add new avatar` option from the menu first.

`stamp()` : Draw a copy of the current avatar at the current location.

`stamp(string)` : Draw a copy of the given avatar at the current location. Choices for _string_ include `'pynguin'`, `'arrow'`, `'robot'`, and `'turtle'`.


# Properties #
Each Pynguin object also has a set of values that can be accessed or set.

`x` : get or set the x-coordinate

`y` : get or set the y-coordinate

`pos` : get or set both x- and y- coordinates

`heading` : get or set the heading

`ang` : Same as heading


# Multiple Pynguins #
You can have more than one pynguin active at any time. Make sure that you keep a reference to any additional pynguins so that you can control them.

`Pynguin` : instantiate or subclass this class for additional pynguin objects. Keep a reference for later use:  `p2 = Pynguin(); p2.fd(100)`

`pyn.remove()` : Pynguin method for discarding the given `Pynguin` object. Also removes everything the pynguin has drawn. If the discarded pynguin was the main pynguin, the next oldest will be promoted to be the main pynguin. That means that the non-qualified commands will control the newly promoted pynguin. For instance if p2 has been promoted, `fd(100)` will be the same as `p2.fd(100)`

`pyn.promote(other_pyn)` : Make other\_pyn be the main pynguin. Note that it is not necessary for the main pynguin to perform this command. For instance, `any_pyn.promote(any_pyn)` is a legal way for any pynguin to promote itself to be the main pynguin.

`reap()` : remove all other pynguins after first taking ownership of everything the pynguin has drawn. Note the difference between `reap()` and `remove()` is that `reap()` will leave the current drawing unchanged.


# util module #
The `util` module is pulled in to the default namespace automatically. There is no need to `import util`

## functions ##

### `choose_color()` ###
`choose_color()` : Return the RGB value of a chosen color. Provides several ways to select a color. This function is used by pynguin methods like `color()` and `bgcolor()` but it may be useful to call it directly. Note that `choose_color()` does not actually set any colors, it only returns the RGB values that can be passed to the color setting methods.

`choose_color(string)` : string can be the name of a color, like `'red'`, `'orange'`, or `'light blue'`.

`choose\_color(string): string can be one of:
  * `'random'`
  * `'rlight'`
  * `'rmedium'`
  * `'rdark'`
  * `'ralpha'`

`choose_color(r, g, b)` : As long as r, g, and b are in the range 0-255 this function will just return R, G, B and if not, it will raise a `ValueError`.

`choose_color(r, g, b, a)` : Similar to `choose_color(r, g, b)` but with an alpha (transparency) value between 0-255. As long as r, g, b, and a are in the range 0-255 will return R, G, B, A. If not, it will raise `ValueError`.


### `nudge_color()` ###
`nudge_color()` : Return the RGB values of a color that has been modified in the specified way. Note that `nudge_color()` does not actually set any colors, it only returns the RGB values that can be passed to the color setting methods.

`nudge_color(color, r=int, g=int, b=int)` : Starting from the initial color (which must be a 3-tuple as returned by the `color()` method) adjust the color by the given amounts. r, g, and b are all optional. Adds the given integer amount to the selected component. For example, if `c = color() = (100, 100, 100)` then `nudge_color(c, r=10, b=-50)` will return `(110, 100, 50)`

`nudge_color(color, r='dr%', g='dg%', b='db%') : Starting from the initial color (which must be a 3-tuple as returned by the `color()` method) adjust the color by the given percents. r, g, and b are all optional. For example, if `c = color() = (100, 100, 100)` then `nudge\_color(c, r='10%', b='150%')` will return `(10, 100, 150)`

Note that numbers and percents can be mixed freely in `nudge_color()` so that for instance, if `c = color() = (100, 100, 100)` then `nudge_color(c, r=-20, g='99%', b='105%')` will return `(80, 99, 105)`