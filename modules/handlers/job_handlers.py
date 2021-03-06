"""Scheduled jobs of the bot"""
from datetime import datetime, timezone, timedelta
from telegram.ext import CallbackContext
from telegram.error import BadRequest, Unauthorized
from modules.debug import logger
from modules.data import config_map, PendingPost
from modules.utils import EventInfo


def clean_pending_job(context: CallbackContext):
    """Job called each day at 05:00 utc.
    Automatically rejects all pending posts that are older than the chosen amount of hours

    Args:
        context (CallbackContext): context passed by the jobqueue
    """
    info = EventInfo.from_job(context)
    admin_group_id = config_map['meme']['group_id']

    before_time = datetime.now(tz=timezone.utc) - timedelta(hours=config_map['meme']['remove_after_h'])
    pending_posts = PendingPost.get_all_pending_memes(group_id=admin_group_id, before=before_time)

    # For each pending meme older than before_time
    removed = 0
    for pending_post in pending_posts:
        message_id = pending_post.g_message_id
        try:  # deleting the message associated with the pending meme to remote
            info.bot.delete_message(chat_id=admin_group_id, message_id=message_id)
            removed += 1
            try:  # sending a notification to the user
                info.bot.send_message(
                    chat_id=pending_post.user_id,
                    text="Gli admin erano sicuramente molto impegnati e non sono riusciti a valutare lo spot in tempo")
            except (BadRequest, Unauthorized) as e:
                logger.warning("Notifying the user on /clean_pending: %s", e)
        except BadRequest as e:
            logger.error("Deleting old pending message: %s", e)
        finally:  # delete the data associated with the pending meme
            pending_post.delete_post()

    info.bot.send_message(chat_id=admin_group_id, text=f"Sono stati eliminati {removed} messaggi rimasti in sospeso")
