# Square Game
 
Play as Square.

This is for college.

Feedback is appreciated.

bug report please

# For Run:
linux terminal (sudo or add --user to end)

`python3 -m pip install -r requirements.txt`

windows cmd (admin or add --user to end)

`py -m pip install -r requirements.txt`

run
linux
`python3 game.py`

window `py game.py`

# For build windows exe/zip

`(py/python3) -m pip install pyinstaller`

make `output` folder if it doesn't exist

run
`cd output

`pyinstaller --noconfirm --onefile --windowed --icon "../assets/icon.ico" --add-data "../vars.py;." --add-data "../defaultUserPrefs.json;." --add-data "../levels;levels" --add-data "../assets;assets" "../game.py"`

change `--onefile` to `--onedir` for a folder (smaller in size if you zip it)

output file is `output/dist/game.exe` - or probably game.Application for mac or something
output dir is `output/dist/game/`
