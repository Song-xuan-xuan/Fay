import json
import os
import time
import uuid

from werkzeug.utils import secure_filename


BACKGROUND_DIR = os.path.join('cache_data', 'backgrounds')
METADATA_FILE = os.path.join(BACKGROUND_DIR, 'backgrounds.json')
DEFAULT_BACKGROUND_URL = '/frontend-static/images/digital-human-default.gif'
ALLOWED_BACKGROUND_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_BACKGROUND_BYTES = 8 * 1024 * 1024
IMAGE_SIGNATURES = {
    'png': (b'\x89PNG\r\n\x1a\n',),
    'jpg': (b'\xff\xd8\xff',),
    'jpeg': (b'\xff\xd8\xff',),
    'gif': (b'GIF87a', b'GIF89a'),
    'webp': (b'RIFF',),
}


def background_dir():
    return os.path.abspath(BACKGROUND_DIR)


def default_background():
    return {
        'id': 'default',
        'name': '默认背景',
        'url': DEFAULT_BACKGROUND_URL,
        'builtin': True,
    }


def list_backgrounds():
    data = _read_metadata()
    return [default_background(), *data['items']]


def get_active_background():
    data = _read_metadata()
    active = _find_background(data.get('active_id', 'default'), data)
    return active or default_background()


def get_active_id():
    return get_active_background()['id']


def save_background(file_storage, name='', content_length=None):
    extension = _background_extension(file_storage.filename)
    _validate_upload(file_storage, extension, content_length)
    os.makedirs(background_dir(), exist_ok=True)
    token = uuid.uuid4().hex
    filename = f'bg-{token}.{extension}'
    file_storage.save(os.path.join(background_dir(), filename))
    item = _new_item(token, filename, name or file_storage.filename)
    data = _read_metadata()
    data['items'].append(item)
    _write_metadata(data)
    return item


def activate_background(background_id):
    data = _read_metadata()
    active = _find_background(background_id, data)
    if not active:
        raise ValueError('背景图不存在')
    data['active_id'] = active['id']
    _write_metadata(data)
    return active


def delete_background(background_id):
    if background_id == 'default':
        raise ValueError('默认背景不能删除')
    data = _read_metadata()
    item = _remove_item(data, background_id)
    _delete_file(item)
    if data.get('active_id') == background_id:
        data['active_id'] = 'default'
    _write_metadata(data)
    return {
        'background': item,
        'active': _find_background(data['active_id'], data) or default_background(),
        'active_id': data['active_id'],
    }


def _read_metadata():
    try:
        with open(METADATA_FILE, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except Exception:
        data = {}
    items = data.get('items') if isinstance(data.get('items'), list) else []
    return {'active_id': data.get('active_id') or 'default', 'items': items}


def _write_metadata(data):
    os.makedirs(background_dir(), exist_ok=True)
    with open(METADATA_FILE, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def _find_background(background_id, data):
    if background_id == 'default':
        return default_background()
    return next((item for item in data['items'] if item.get('id') == background_id), None)


def _background_extension(filename):
    safe_name = secure_filename(filename or '')
    _, extension = os.path.splitext(safe_name)
    return extension.lower().lstrip('.')


def _validate_upload(file_storage, extension, content_length):
    if extension not in ALLOWED_BACKGROUND_EXTENSIONS:
        raise ValueError('背景图仅支持 png、jpg、jpeg、webp、gif')
    if content_length and content_length > MAX_BACKGROUND_BYTES:
        raise ValueError('背景图文件不能超过 8MB')
    header = file_storage.stream.read(12)
    file_storage.stream.seek(0)
    valid_signature = any(header.startswith(signature) for signature in IMAGE_SIGNATURES[extension])
    if not valid_signature or (extension == 'webp' and header[8:12] != b'WEBP'):
        raise ValueError('背景图文件内容不是有效图片')


def _new_item(token, filename, display_name):
    name = str(display_name or '').strip()
    if not name:
        safe_name = secure_filename(filename or '')
        name = os.path.splitext(safe_name)[0] or '背景图'
    return {
        'id': f'bg_{token[:12]}',
        'name': name[:40],
        'url': f'/backgrounds/{filename}',
        'filename': filename,
        'created_at': int(time.time()),
    }


def _remove_item(data, background_id):
    for index, item in enumerate(data['items']):
        if item.get('id') == background_id:
            return data['items'].pop(index)
    raise ValueError('背景图不存在')


def _delete_file(item):
    filename = secure_filename(item.get('filename') or '')
    if not filename:
        return
    path = os.path.join(background_dir(), filename)
    if os.path.exists(path):
        os.remove(path)
