hammock
=======

XML-based REST API Doc Generation Tool

Usage
=======

Hammock converts an XML file containing REST API documentation into a
pretty-looking HTML file.

    python hammock.py example.xml

This will create a directory `out/` with a file `out/example.xml`.  If you
would like to output to a different directory, use:

    python hammock.py --outdir=/path/to/outdir example.xml

The target directory and all parent directories, will be created if necessary.

The generated HTML looks for a CSS file called `hammock-custom.css`.  Without
this file, the generated HTML looks very ugly.  We provide a few styles for you
to choose from.  Just copy the desired style to the output directory renaming
it to `hammock-custom.css`.

    cp styles/modern.css out/hammock-custom.css

To see your wonderful documentation:

    firefox out/example.html &
