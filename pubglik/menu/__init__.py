"""Building menus to use with PrivateConversationHandler."""

from .callbacks import callbacks
from .messages import messages
from .answers import answers
from .buttons import buttons, optional_buttons
from .menutree import menu_tree

##############################

menu_data = {
	'callbacks': callbacks,
	'texts': messages,
	'buttons': buttons,
	'optional_buttons': optional_buttons,
	'answers': answers
}
