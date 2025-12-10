from rest_framework.renderers import JSONRenderer


class APIRenderer(JSONRenderer):
    """
    일관된 API 응답 형식을 위한 커스텀 Renderer

    성공 응답:
    {
        "success": true,
        "data": { ... },
        "message": "성공 메시지"
    }

    실패 응답 (exception handler에서 처리):
    {
        "success": false,
        "data": null,
        "message": "에러 메시지",
        "errors": { ... },
        "error_code": "error_code"
    }
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response') if renderer_context else None

        # 이미 포맷팅된 응답인 경우 그대로 반환 (exception handler 또는 view에서 처리)
        if isinstance(data, dict) and 'success' in data:
            return super().render(data, accepted_media_type, renderer_context)

        # 성공 응답만 처리 (에러 응답은 exception handler에서 처리)
        if response and response.status_code < 400:
            formatted_data = {
                'success': True,
                'data': data,
                'message': '요청이 성공적으로 처리되었습니다.',
            }
            return super().render(formatted_data, accepted_media_type, renderer_context)

        # 에러 응답이지만 exception handler를 거치지 않은 경우 (fallback)
        return super().render(data, accepted_media_type, renderer_context)
