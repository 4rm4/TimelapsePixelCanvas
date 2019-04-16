# TimelapsePixelCanvas

This is a script to create sequential screenshots of the area you want.
#### How you can use this?

Python 2.7 is required.

Install these packages:
```bash
$ pip install Pillow
$ pip install https://github.com/saltycrane/retry-decorator/archive/v0.1.2.tar.gz
```

##### Once setup, run the script:

Example:
```bash
$ python timelapse_pixel_canvas.py --start_x 0 --end_x 100 --start_y 0 --end_y 100 -s 20
```

### Parameter options: 

* **-s** or **--seconds** is the time to wait between screenshot attempts. Screenshots typically take ~30s Default: 30
* **-sx** or **--start_x** is the start of the X range.
* **-ex** or **--end_x** is the end of the X range.
* **-sy** or **--start_y** is the start of the Y range.
* **-ey** or **--end_y** is the end of the Y range.
* **-d** or **--directory** is the directory to store the output. Will create if it doesn't exist.
