"""Routes registration"""
from Router import Router
from AdvancedHandler import AdvancedHTTPRequestHandler


def register_routes(router: Router, handler_class: AdvancedHTTPRequestHandler):
    """Routes registration"""
    router.add_route('GET', '/api/images/?page=?', handler_class.get_images)
    router.add_route('POST', '/upload/', handler_class.post_upload)
    router.add_route('DELETE', '/delete/<image_id>',
                     handler_class.delete_image)
