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

# For build
You will need a venv or the file size will be large

(replace python with py/python3)

Run this somewhere to make a venv in the folder SquareGameVenv

`python -m venv SquareGameVenv`

Then run

`SuqareGameVenv/bin/activate` (linux/mac)
`SquareGameVenv\Scripts\activate` (windows)

Then move to the SquareGame base folder (the one with game.py)

`python -m pip install pyinstaller -r requirements.txt`

make `output` folder if it doesn't exist

run
`cd output`

`pyinstaller --noconfirm --onefile --windowed --icon "../assets/icon.ico" --add-data "../defaultUserPrefs.json:." --add-data "../levels:levels" --add-data "../assets:assets" "../game.py"`

change `--onefile` to `--onedir` for a folder
if there's an error related to the `--add-data` stuff replace the `:` with `;`

output file is `output/dist/game.exe` - or probably game.Application for mac or something
output dir is `output/dist/game/`
