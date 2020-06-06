# Observatory Addon

Blender addon for experimenting with interferometry methods in radio astronomy.

The purpose of this addon is to create an interactive scene for exploring methods of radio interferometry. The addon creates properties for a virtual observatory. Operators and python functions compute a simulated visibility function and sky brightness based on the configuration of objects in the scene. A collection of antennas generates a set of baselines that determines which angular frequencies can be resolved.

![Antenna objects in the Blender scene](images/screenshot.png)

## Useful Resources

* Introductory lecture on radio interferometry:
  * Fundamentals: https://youtu.be/0TwnZhiEc3A
  * Deconvolution: https://youtu.be/mRUZ9eckHZg
* Extensive lecture on radio astronomy: https://science.nrao.edu/opportunities/courses/era/
* ALMA primer: https://almascience.eso.org/documents-and-tools/cycle6/alma-science-primer/view
* Star maps for sky backgrounds: https://svs.gsfc.nasa.gov/cgi-bin/details.cgi?aid=3572
* Map of the 21cm hydrogen emission line: https://sites.google.com/site/radioastronomydm/observations/h-line/h-line-maps
* FFT in numpy: https://numpy.org/doc/stable/reference/routines.fft.html