from django.conf import settings
from django.urls import reverse


def vote_rows_for_queue_context(votes):
    """
    Build JSON-serializable rows for RabbitMQ email tasks.
    Never pass Django model instances in context — json.dumps will fail.
    """
    rows = []
    for v in votes:
        rows.append(
            {
                "category_title": v.category.title,
                "nominee_name": v.nominee.nominee,
            }
        )
    return rows


def build_confirmation_url(token, email, request=None):
    path = reverse('awards-vote-confirm') + f'?token={token}&email={email}'
    if request is not None:
        return request.build_absolute_uri(path)

    allowed_hosts = getattr(settings, 'ALLOWED_HOSTS', []) or []
    public_host = next(
        (host for host in allowed_hosts if host not in ['*', '127.0.0.1', 'localhost']),
        None,
    )
    if public_host:
        return f'https://{public_host}{path}'
    return path

