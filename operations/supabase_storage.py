"""Upload resident profile pictures and QR images to Supabase Storage."""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def _get_client():
    """Return Supabase client or None if not configured."""
    if not getattr(settings, 'SUPABASE_URL', None) or not getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', None):
        return None
    try:
        from supabase import create_client
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    except Exception as e:
        logger.warning('Supabase client not available: %s', e)
        return None


def upload_profile_picture(file, resident_id: int) -> str:
    """
    Upload profile image to Supabase Storage. Returns public URL or empty string on failure.
    Path: resident_{id}.{ext} (ext from file name or 'jpg').
    """
    client = _get_client()
    if not client:
        return ''
    bucket = getattr(settings, 'SUPABASE_STORAGE_BUCKET_PROFILES', 'profiles')
    name = getattr(file, 'name', '') or 'image.jpg'
    ext = name.rsplit('.', 1)[-1].lower() if '.' in name else 'jpg'
    if ext not in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
        ext = 'jpg'
    path = f'resident_{resident_id}.{ext}'
    content_type = getattr(file, 'content_type', None) or f'image/{ext}' if ext != 'jpg' else 'image/jpeg'
    try:
        file.seek(0)
        body = file.read()
        client.storage.from_(bucket).upload(
            path=path,
            file=body,
            file_options={'content-type': content_type, 'upsert': 'true'}
        )
        url = client.storage.from_(bucket).get_public_url(path)
        return url
    except Exception as e:
        logger.exception('Supabase profile upload failed for resident %s: %s', resident_id, e)
        return ''


def upload_qr_image(png_bytes: bytes, resident_id: int) -> str:
    """
    Upload QR code PNG to Supabase Storage. Returns public URL or empty string on failure.
    Path: resident_{id}.png
    """
    client = _get_client()
    if not client:
        return ''
    bucket = getattr(settings, 'SUPABASE_STORAGE_BUCKET_QR', 'qr')
    path = f'resident_{resident_id}.png'
    try:
        client.storage.from_(bucket).upload(
            path=path,
            file=png_bytes,
            file_options={'content-type': 'image/png', 'upsert': 'true'}
        )
        url = client.storage.from_(bucket).get_public_url(path)
        return url
    except Exception as e:
        logger.exception('Supabase QR upload failed for resident %s: %s', resident_id, e)
        return ''
