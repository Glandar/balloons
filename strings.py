CONTROLS_TEXT = '''Hold:
arrows = move arrow-ball
wasd = move wasd-ball
down/s = inflate/deflate balls (if touching)
r = drain air from deposit

Press:
q = quit
f = show/hide window frame
left-alt = all air to wasd-ball
right-alt = all air to arrow-ball
space = shoot balls away from each other (if they touch)
esc = pause the game (or exit menu/level selector/text area)
del/enter/backspace = standard use in level creator/editor
m = open/close menu
l = open/close level selector
c = open/close level create/edit
j = replay highscore on current level (and stop replay)
k = replay progress on current level (and continue from replay state)
b = rotate though background designs
up/down = in-/decrease replay frame rate in replay mode
F1 = start previous level
F2 = restart current level
F3 = start next level
F4 = rotate through drawing colors
F5 = clear drawn Paths
F6 = decrease radius of vision (darkness mode)
F7 = darkness mode
F8 = increase radius of vision (darkness mode)
F9 = rotate through darkness shapes
F10 = go to random level
F11 = create new level (opens empty level)
F12 = save level state as new level

Mouse:
click/drag = draw Paths
click/drag = edit level in level creator/editor
position on top of a goal = overwrite inflate/deflate to match goal
position on remover/teleporter = show location of remove/teleport'''

INTRO_HEADERS = ["Moving air around", "Interacting balloons", "Game objects", "Darkness and drawing", "Level creation", "Profiles"]

INTRO_TEXT = [
'''In this game you control 2 balloons containing air.
These balloons are controlled using the arrow-buttons and wasd-buttons.
To move right or left you use the 'left', 'right', 'a' & 'd' key.
To jump over objects you need to use the 'up' and 'w' keys.

When you land on top of an object your balloon turns bright red.
Your balloon also turns bright red when it lands on top of the other balloon.
This means that it can 'double jump' - it can jump once while being in mid-air.
When you jump in mid-air the ball turns dark red again and you lose this ability.

To complete a level the required amount of air needs to be deposited in the green circle.
This is done by having the center of a balloon containing air touch this target.
In the upper right of your screen you can see the amount of air your balloons contain.
Before the '+' we have the amount of air in the arrow balloon.
After the '+' you can see the amount of air in the wasd balloon.

Press 'F1' to go back a level, restart with 'F2' and skip a level with 'F3'.
Completing a level will save your score (time) and advance you to the next level.

These highscores can be replayed using 'j', 'k' triggers a replay of the current position.
Pressing 'k' during a replay allows you to continue from the current position,
this invalides your score for that level. A replay can be terminated using 'j'.
''','''
When the balloons are connected they have many more possibilities.
They can push each other around and jump together which you can use to jump higher.

You can also launch the balloons away from each other if they touch.
This is done by pressing the space-bar,
the balloons fly in opposite direction with a speed proportional to their sizes.
When they touch you can also change their sizes.
This is done by flowing air from one balloon to the other.
To let air flow from the arrow balloon to the wasd balloon you press 's'.
similarly, to let air flow from the wasd balloon to the arrow balloon you press 'down'.
Often you will want to have the size of a balloon match the target amount,.
To do this, place your mouse inside a target and then press 's' or 'down'.

The alt keys can complete empty one of the balloons.
The left alt key lets all the air flow in to the wasd balloon.
The right alt key lets all the air flow in to the arrow balloon.
''',''' 
Besides the targets, there are 3 other circular elements in the game:
These are the teleporters (purple), removers (cyan) and deposits (orange).
They have no hit-box and activate when they overlap with the center of a ball.

When you activate a teleporter, the balloon will then get teleported somewhere,
if you put your mouse on the teleporter you can see where the balloon would end up.
If the balloon is too big or the place is occupied by the other balloon,
you will not get teleported. If this place becomes available while you touch the
teleporter you will be teleported. Teleported balloons do not lose their momentum.

Removers remove objects (beams) when activated. This is irreversible and can cause
a level to become impossible. In this case the level will need to be restarted.
To see what object will be removed, you can place your mouse inside the circle.

Deposits give air to the balloon when activated while the 'r' key is held.
These will come to play in later levels.
''','''
You can play the game in darkness mode for an extra challenge.
This mode can be activated in the menu of by pressing 'F7'.
To de- or increase the radius of vision press 'F6' or 'F8' respectively.
'F9' changes the shape of your field of vision to another of 5 possibilities.
To help you navigate the darkness, you can draw lines on the screen by dragging the mouse.
This lines can be removed by pressing 'F5' or restarting the level (see settings).
If you want to change the colors of the drawing you can press 'F4'.
''','''
To create a new level you press 'F11', to edit an existing level press 'c'.
To save a level press 'F12', this will not overwrite the level you are editing.
When creating/editing a level, use the mouse to select and place objects on the map.
First you select the object you want to add in the menu below,
than click on the screen to place a goal, remover or deposit (if selected).
To place a beam or teleporter you draw a line which will turn into the desired object.
Make sure to save or pin the level state before testing since the current game-state is saved.
''','''
It is possible to create multiple profiles for different people or different play-styles.
This can be done in the menu by entering a profile name and clicking "create profile".
An existing profile can be opened by selecting it from the list below or typing it out.
Each profile creates a separate folder in the game directory.
This is where the highscores and settings are saved and can be deleted or copied.
''']