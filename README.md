# Control-

*Control-* is a (Linux) alternative to LEGO's Control+ application to control [42099 4x4 X-treme Off-roader][1]. The aim is to support exploration of programming capabilities of this set and Powered Up system in general.

*Control-* consists of [model definition][2] and a simple [GTK3 based UI][3] for interactive control.

For actual communication it uses (as of now) modified [bricknil][4] library. [Changes are being upstreamed][7], but until this happen, you have to use modified version.

## Obligatory screenshot

![Obligatory screenshot](https://raw.githubusercontent.com/janvrany/controlminus/master/doc/screenshot1.png "Obligatory screenshot")

## Installation

```
mkdir lego-playground
cd lego-playground
git clone https://github.com/janvrany/bricknil.git
git clone https://github.com/janvrany/controlminus.git
cd controlminus
virtualenv --system-site-packages --prompt "[control-] " -v .venv
. .venv/bin/activate
pip install -e ../bricknil
```

## Running

```
cd lego-playground/controlminus
. .venv/bin/activate
./vehicle.py
```


## Contributing

Anyone wishing to help is welcome! If you encounter a problem. please fill in a report to [github issue tracker][6].

To contribute, send PR!

## License

Copyright (c) 2020 Jan Vrany <jan.vrany (a) fit.cvut.cz>

This software is licensed under "MIT license". You may find a full license text in `LICENSE.txt`.

[1]: https://www.lego.com/en-gb/product/4x4-x-treme-off-roader-42099
[2]: https://github.com/janvrany/controlminus/blob/master/controlminus/model.py
[3]: https://github.com/janvrany/controlminus/blob/master/controlminus/ui/vehicle.py
[4]: https://github.com/janvrany/bricknil
[5]: https://github.com/virantha/bricknil
[6]: https://github.com/janvrany/controlminus/issues
[7]: https://github.com/virantha/bricknil/pulls