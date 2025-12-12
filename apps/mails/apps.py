from django.apps import AppConfig


class MailsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mails'
    verbose_name = '메일'

    def ready(self):
        # 메일 상태 변경 시 폴더 카운트 동기화 signals 등록
        import apps.mails.signals  # noqa: F401
