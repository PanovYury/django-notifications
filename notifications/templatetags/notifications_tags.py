""" Django notifications template tags file """

from django.urls import reverse
from django.core.cache import cache
from django.template import Library
from django.utils.html import format_html

from notifications import settings


register = Library()


def get_cached_notification_unread_count(user):
    return cache.get_or_set(
        'cache_notification_unread_count',
        user.notifications.unread().count,
        settings.get_config()['CACHE_TIMEOUT']
    )

@register.simple_tag(takes_context=True)
def notifications_unread(context):
    user = user_context(context)
    if not user:
        return ''
    return get_cached_notification_unread_count(user)


@register.filter
def has_notification(user):
    if user:
        return user.notifications.unread().exists()
    return False


# Requires vanilla-js framework - http://vanilla-js.com/
@register.simple_tag
def register_notify_callbacks(badge_class='live_notify_badge',  # pylint: disable=too-many-arguments,missing-docstring
                              menu_class='live_notify_list',
                              refresh_period=15,
                              callbacks='',
                              api_name='list',
                              fetch=5,
                              nonce=None,
                              mark_as_read=False
                              ):
    refresh_period = int(refresh_period) * 1000

    if api_name == 'list':
        api_url = reverse('notifications:live_unread_notification_list')
    elif api_name == 'count':
        api_url = reverse('notifications:live_unread_notification_count')
    else:
        return ""

    callbacks_script = ''.join([
        f"register_notifier({callback});"
        for callback in callbacks.split(',')
    ])

    definitions = """
    <script type="text/javascript"{nonce}>
        notify_badge_class='{badge_class}';
        notify_menu_class='{menu_class}';
        notify_api_url='{api_url}';
        notify_fetch_count='{fetch_count}';
        notify_unread_url='{unread_url}';
        notify_mark_all_unread_url='{mark_all_unread_url}';
        notify_refresh_period={refresh};
        notify_mark_as_read={mark_as_read};
        {callbacks_script}
    </script>
    """

    # add a nonce value to the script tag if one is provided
    nonce_str = nonce or ""

    return format_html(
        definitions,
        nonce=nonce_str,
        badge_class=badge_class,
        menu_class=menu_class,
        refresh=refresh_period,
        api_url=api_url,
        unread_url=reverse('notifications:unread'),
        mark_all_unread_url=reverse('notifications:mark_all_as_read'),
        fetch_count=fetch,
        mark_as_read=str(mark_as_read).lower(),
        callbacks_script=callbacks_script
    )


@register.simple_tag(takes_context=True)
def live_notify_badge(context, badge_class='live_notify_badge'):
    user = user_context(context)
    if not user:
        return ''

    html = "<span class='{badge_class}'>{unread}</span>"
    return format_html(html, badge_class=badge_class, unread=get_cached_notification_unread_count(user))


@register.simple_tag
def live_notify_list(list_class='live_notify_list'):
    html = "<ul class='{list_class}'></ul>"
    return format_html(html, list_class=list_class)


def user_context(context):
    if 'user' not in context:
        return None

    request = context['request']
    user = request.user

    if not user.is_authenticated:
        return None
    return user
