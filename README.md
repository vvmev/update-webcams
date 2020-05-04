# Upload webcam images to FTP server

We have a number of [Grandstream GVX3610 webcams](http://www.grandstream.com/products/facility-management/hd-ip-cameras/product/gxv3610-v2-series) we're using to take regular snapshots of our museum.

While the built-in firmware does offer an FTP upload, we'd like to add some data to the images before upload. Also, we'd rather not expose the cameras to the internet at all, leaving them isolated in their own private network.

This Python script will download an image from a webcam, add some information to it using [GraphicsMagick](http://www.graphicsmagick.org), and then upload them to the FTP server.

## Installing

The Python script only needs standard Python modules, so no pip/pipenv is necessary. You will need GraphicsMagick and Ghostscript (fonts) installed in your system.

## Running

You simply invoke the script and pass the name of the config file as the only parameter.

### Docker

The Dockerfile will build a Docker image. You can run it like this:

```
docker run -it --rm -v $PWD/webcams.ini:/webcams.ini update-webcams /webcams.ini
```

## Configuration file

The [ini-style configuration file](https://docs.python.org/3.7/library/configparser.html) has all parameters necessary for running the script.

Unless noted otherwise, all parameters are required.

See the example [`webcams.ini`](./webcams.ini).

### Section [general]

* `hostname` of the FTP server. Leave blank to not upload the image to an FTP server.
* `username` and `password` for logging in to the FTP server. Required if `hostname` is set.
* `url_pattern`: a string specifying a URL for accessing the webcam images. A `{}` in the string will be replaced with the `host` parameter for each webcam.
* `archive_dir`: the name of a directory that will receive each downloaded image. The script will use each webcams `filename` parameter, and create a folder hierarchy based on that name, the current year and month, the current year, month, and day, and place the image file with the time stamp as it's filename there. Default is empty, which disables image archiving.
* `label_pattern`: a string specifying the label to be added to the image. The string will first be passed through [`strftime`](https://docs.python.org/3.7/library/datetime.html#datetime.date.strftime). A `{}` in the resulting string will be replaced with the `title` parameter for each webcam.
* `verbose`: if set to `True`, each action will be printed on stdout. Default is `False`.
* `interval`: number of seconds to wait between fetching and uploading all webcam images. Default is `0`, which means that the script will exit after one round.

### Webcam Sections

All other sections in the file are taken to define a webcam that should be processed.

* `title`: the name to be substituted into the label that is added to the image.
* `filename`: the filename to use for the upload to the FTP server.
* `host`: hostname to be substituted into the `url_pattern` to generate the URL.
* `url`: full URL to download the image from. If specified, the `host` key is ignored.