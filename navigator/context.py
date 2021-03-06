
import logging
from navigator.utils import session_pop

log = logging.getLogger(__name__)
from amcat.models import AmCAT

DISPLAY_COUNT = 3
ANNOUNCE_KEY = "last_announcement"
COUNT_KEY = "last_announcement_count"

def get_announcement(request):
    """
    A announcement can be placed in the amcat_system table, which will be displayed
    to each user DISPLAY_COUNT times.
    """
    announcement = AmCAT.get_instance().global_announcement
    last_announcement = request.session.get(ANNOUNCE_KEY)
    count = int(request.session.get(COUNT_KEY, 0)) + 1

    if last_announcement == announcement and count >= DISPLAY_COUNT:
        announcement = None
    elif last_announcement != announcement:
        request.session["last_announcement"] = announcement
        count = 0

    if count < DISPLAY_COUNT:
        request.session[COUNT_KEY] = count

    return announcement


# Extra context variables
def extra(request):
    announcement = get_announcement(request)
    warning = AmCAT.get_instance().server_warning
    notice = session_pop(request.session, "notice")
    if request.user.is_anonymous():
        theme = 'amcat'
    else:
        theme = getattr(request.user.get_profile(), 'theme', 'amcat').lower().replace(" ", "_")
    return locals()
