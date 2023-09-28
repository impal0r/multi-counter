#----------------------------------- CONFIG -------------------------------------
# There is no kbd-layout-independent way to bind to the keys with a + and - on
#  on tkinter
# On a UK keyboard layout, these are the two keys to the right of [0]
# You can change these to the keysym of any key except the numbers
minus_key = 'minus'
plus_keys = 'plus', 'equal'
# Fonts and colours
counter_font = 'fixedsys 24'
changes_font = 'fixedsys 12'
button_font = 'fixedsys 20'

typing_colour = 'orange'
change_colour = 'green'

#----------------------------------- IMPORTS ------------------------------------
#Fix blurriness in windows high DPI settings
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
    del ctypes
except (OSError,ModuleNotFoundError):
    pass

from tkinter import *
from tkinter import messagebox

#--------------------------------- CLASSY STUFF ---------------------------------

class Change:
    def __init__(self, delta, is_null=False):
        self.delta = delta
        self.is_null = is_null
    def __str__(self):
        if self.is_null:
            return 'NULL'
        elif self.delta == 0:
            return ''
        return '{:+d}'.format(self.delta)

#------------------------------ THE ACTUAL COUNTER ------------------------------
i = 0

def increment(*args):
    global i
    i += 1
    change = Change(+1)
    update_display(i, change)
    add_change_to_stack(change)
def increment_by(n):
    global i
    old_i = i
    i += n
    if i<0: i=0
    change = Change(i-old_i)
    update_display(i, change)
    add_change_to_stack(change)
def decrement(*args):
    global i
    old_i = i
    if i>0: i -= 1
    change = Change(i-old_i)
    update_display(i, change)
    add_change_to_stack(change)
def reset(*args):
    global i
    change = Change(-i,is_null=True)
    update_display(0, change)
    add_change_to_stack(change)
    i = 0

#-------------------------------- WINDOW LAYOUT ---------------------------------
root = Tk()
root.title('count')
root.minsize(100, 100)
btn_frame = Frame(root)
down_button = Button(btn_frame, text='--', font=button_font, command=decrement)
down_button.pack(padx=10, side='left')
up_button = Button(btn_frame, text='++', font=button_font, command=increment)
up_button.pack(padx=10, pady=10, side='left')
reset_button = Button(btn_frame, text='NULL', font=button_font, command=reset)
reset_button.pack(padx=10, side='left')
last_change_frame = Frame(root)
last_change_text = Label(last_change_frame, text='', font=changes_font)
last_change_text.pack(side='left')
last_change_frame.pack(side='top', expand=1, fill='both')
number_text = Label(root, text='0', font=counter_font)
number_text.pack(pady=(0,10), side='top')
btn_frame.pack(side='top')

def update_display(n, change):
    number_text.config(text = str(n))
    last_change_text.config(fg=change_colour, text=str(change))

#----------------- HELP BUTTON / DOCUMENTATION & FEEDBACK TEXT ------------------
def help_message(*args):
    messagebox.showinfo('Help', '''The counter goes as high as you like but doesn't go below zero.
Buttons:
 ++\t\tincrement
 --\t\tdecrement
 NULL\t\treset to zero
\nKeyboard:
+/-\t\tincrement/decrement
0\t\treset to zero
1..9\t\tincrement by that number
Shift+1..9\tdecrement by that number
Hold Ctrl\t\tenter multiple-digit numbers
Ctrl+C\t\tcopy counter to clipboard
Ctrl+Z\t\tundo last change to counter''')
info_frame = Frame(root)
help_btn = Button(info_frame, text='Help', command=help_message)
help_btn.pack(side='left', padx=5)
info_text = Label(info_frame, text='', fg='green')
info_text.pack(side='left', padx=5)
info_frame.pack(side='left', padx=10, pady=10)
def clear_feedback():
    info_text.config(text='')
def flash_feedback(msg):
    info_text.config(text=msg)
    root.after(1000, clear_feedback)

#--------------------------------- KEY BINDINGS ---------------------------------
def copy_i_to_clipboard(*args):
    root.clipboard_clear()
    root.clipboard_append(str(i))
    root.update() #so value will stay in clipboard after window is closed
    flash_feedback(f"'{i}' copied to clipboard") #give user some feedback

#implementing undo
undo_stack = []
def add_change_to_stack(change):
    undo_stack.append(change)
def pop_change_from_stack():
    return undo_stack.pop()
def undo():
    global i, undo_stack
    if not undo_stack:
        return
    last_change = pop_change_from_stack()
    i -= last_change.delta
    if not undo_stack:
        update_display(0, Change(0))
    else:
        update_display(i, undo_stack[-1])
    flash_feedback('Undid last change')

#implementing holding down control to add/subtract longer numbers
held_number = ''
held_subtract = False
def update_held_number(digit, sign):
    global held_number, held_subtract
    if not held_number:
        held_subtract = sign
    #if you hold down control, type 123, then press down shift, then type 45,
    # then release control, the result will be -45
    # ie. changing the states of control and shift resets the number being entered
    if held_number and held_subtract != sign:
        held_subtract = sign
        held_number = ''
    held_number += digit
    sign = '-' if held_subtract else '+'
    last_change_text.config(fg=typing_colour, text = sign + held_number)
def reset_held_number(sign):
    global held_number
    last_change_text.config(fg=typing_colour, text = sign)
    held_number = ''
def bake_held_number():
    global held_number, held_subtract
    if not held_number:
##        last_change_text.config(text = '')
        return
    assert held_number.isdigit()
    increment_by(int(held_number) * (-1 if held_subtract else 1))
    last_change_text.config(fg=change_colour)
    held_number = ''

#key states and event handlers
control_down = False
shift_down = False
last_control_shift_event = None
numbers_down = [False for i in range(10)] #anti-repeat
def update_control_shift_state(key, is_keydown):
    global shift_down, control_down, last_control_shift_event
    is_keyup = not is_keydown
    if key == 'control' and is_keydown:
        control_down = True
##        if shift_down:
##            reset_held_number('-')
##        else:
##            reset_held_number('+')
    elif key == 'control' and is_keyup:
        control_down = False
        if not shift_down:
            bake_held_number()
    elif key == 'shift' and is_keydown:
        shift_down = True
##        if control_down:
##            reset_held_number('-')
    elif key == 'shift' and is_keyup:
        shift_down = False
        if not control_down and last_control_shift_event==('control',False):
            bake_held_number()
    else:
        raise ValueError("key should be 'shift' or 'control' "
                         "and is_keydown  should be boolean. Got: "
                         "key == '{key}' and is_keydown == {is_keydown}")
    last_control_shift_event = (key, is_keydown)
def keydown_handler(event):
    if event.keycode == 16: #shift
        update_control_shift_state('shift', True)
    elif event.keycode == 17: #control
        update_control_shift_state('control', True)
    elif event.keycode == ord('C'):
        if control_down and not shift_down:
            copy_i_to_clipboard()
    elif event.keycode == ord('Z'):
        if control_down and not shift_down:
            undo()
    elif ord('0') <= event.keycode <= ord('9'):
        if numbers_down[event.keycode-ord('0')]:
            return
        numbers_down[event.keycode-ord('0')] = True
        if control_down:#hold control to input numbers with >1 digit
            update_held_number(chr(event.keycode), shift_down)
        elif event.keycode == ord('0'):
            if not shift_down:
                reset()
        else:
            sign = -1 if shift_down else 1
            increment_by((event.keycode-ord('0')) * sign)
    elif event.keysym in plus_keys:
        increment()
    elif event.keysym == minus_key:
        decrement()
def keyup_handler(event):
    if event.keycode == 16: #shift
        update_control_shift_state('shift', False)
    elif event.keycode == 17: #control
        update_control_shift_state('control', False)
    elif ord('0') <= event.keycode <= ord('9'):
        numbers_down[event.keycode-ord('0')] = False

root.bind('<Key>', keydown_handler)
root.bind('<KeyRelease>', keyup_handler)

#--------------------------------- STAYIN ALIVE ---------------------------------
root.mainloop()
