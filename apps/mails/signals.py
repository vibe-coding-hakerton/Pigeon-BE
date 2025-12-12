"""메일 상태 변경 시 폴더 카운트 자동 동기화"""
from collections import defaultdict

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import Mail


def update_folder_counts(folder, mail_delta=0, unread_delta=0):
    """폴더의 mail_count와 unread_count를 업데이트"""
    if folder is None:
        return

    if mail_delta != 0:
        folder.mail_count = max(0, folder.mail_count + mail_delta)
    if unread_delta != 0:
        folder.unread_count = max(0, folder.unread_count + unread_delta)

    folder.save(update_fields=['mail_count', 'unread_count'])


@receiver(pre_save, sender=Mail)
def mail_pre_save(sender, instance, **kwargs):
    """메일 저장 전 이전 상태 캐싱"""
    if instance.pk:
        try:
            old_instance = Mail.objects.get(pk=instance.pk)
            instance._old_folder = old_instance.folder
            instance._old_is_read = old_instance.is_read
            instance._old_is_deleted = old_instance.is_deleted
        except Mail.DoesNotExist:
            instance._old_folder = None
            instance._old_is_read = None
            instance._old_is_deleted = None
    else:
        instance._old_folder = None
        instance._old_is_read = None
        instance._old_is_deleted = None


@receiver(post_save, sender=Mail)
def mail_post_save(sender, instance, created, **kwargs):
    """메일 저장 후 폴더 카운트 업데이트"""
    old_folder = getattr(instance, '_old_folder', None)
    old_is_read = getattr(instance, '_old_is_read', None)
    old_is_deleted = getattr(instance, '_old_is_deleted', None)

    if created:
        # 새 메일 생성 시
        if instance.folder and not instance.is_deleted:
            mail_delta = 1
            unread_delta = 0 if instance.is_read else 1
            update_folder_counts(instance.folder, mail_delta, unread_delta)
        return

    # 삭제 상태 변경
    if old_is_deleted != instance.is_deleted:
        if instance.is_deleted:
            # 삭제됨: 폴더에서 제거
            if instance.folder:
                mail_delta = -1
                unread_delta = 0 if instance.is_read else -1
                update_folder_counts(instance.folder, mail_delta, unread_delta)
        else:
            # 복원됨: 폴더에 추가
            if instance.folder:
                mail_delta = 1
                unread_delta = 0 if instance.is_read else 1
                update_folder_counts(instance.folder, mail_delta, unread_delta)
        return

    # 삭제된 메일은 카운트에서 제외
    if instance.is_deleted:
        return

    # 폴더 변경
    folder_changed = (
        (old_folder is None and instance.folder is not None) or
        (old_folder is not None and instance.folder is None) or
        (old_folder is not None and instance.folder is not None and old_folder.id != instance.folder.id)
    )

    if folder_changed:
        # 이전 폴더에서 감소
        if old_folder:
            mail_delta = -1
            unread_delta = 0 if instance.is_read else -1
            update_folder_counts(old_folder, mail_delta, unread_delta)

        # 새 폴더에 증가
        if instance.folder:
            mail_delta = 1
            unread_delta = 0 if instance.is_read else 1
            update_folder_counts(instance.folder, mail_delta, unread_delta)
        return

    # 읽음 상태 변경 (같은 폴더 내)
    if old_is_read is not None and old_is_read != instance.is_read:
        if instance.folder:
            # is_read: False -> True : unread -1
            # is_read: True -> False : unread +1
            unread_delta = -1 if instance.is_read else 1
            update_folder_counts(instance.folder, 0, unread_delta)


@receiver(post_delete, sender=Mail)
def mail_post_delete(sender, instance, **kwargs):
    """메일 삭제 시 폴더 카운트 감소"""
    if instance.folder and not instance.is_deleted:
        mail_delta = -1
        unread_delta = 0 if instance.is_read else -1
        update_folder_counts(instance.folder, mail_delta, unread_delta)


# =====================
# Bulk 연산 헬퍼 함수
# =====================

def bulk_move_update_counts(mails_queryset, target_folder):
    """
    bulk_move 시 폴더 카운트 업데이트
    QuerySet.update()는 signals를 트리거하지 않으므로 직접 처리
    """
    from apps.folders.models import Folder

    # 원본 폴더별 카운트 계산
    source_deltas = defaultdict(lambda: {'mail': 0, 'unread': 0})

    for mail in mails_queryset.select_related('folder'):
        if mail.folder:
            source_deltas[mail.folder.id]['mail'] -= 1
            if not mail.is_read:
                source_deltas[mail.folder.id]['unread'] -= 1

        # 대상 폴더 증가
        if target_folder:
            source_deltas[target_folder.id]['mail'] += 1
            if not mail.is_read:
                source_deltas[target_folder.id]['unread'] += 1

    # 폴더 카운트 업데이트
    for folder_id, deltas in source_deltas.items():
        try:
            folder = Folder.objects.get(id=folder_id)
            folder.mail_count = max(0, folder.mail_count + deltas['mail'])
            folder.unread_count = max(0, folder.unread_count + deltas['unread'])
            folder.save(update_fields=['mail_count', 'unread_count'])
        except Folder.DoesNotExist:
            pass


def bulk_read_update_counts(mails_queryset, new_is_read):
    """
    bulk_update로 is_read 변경 시 폴더 카운트 업데이트
    """
    from apps.folders.models import Folder

    # 폴더별 unread 변경량 계산
    folder_deltas = defaultdict(int)

    for mail in mails_queryset.select_related('folder'):
        if mail.folder and mail.is_read != new_is_read:
            # True -> False: +1, False -> True: -1
            delta = -1 if new_is_read else 1
            folder_deltas[mail.folder.id] += delta

    # 폴더 카운트 업데이트
    for folder_id, delta in folder_deltas.items():
        try:
            folder = Folder.objects.get(id=folder_id)
            folder.unread_count = max(0, folder.unread_count + delta)
            folder.save(update_fields=['unread_count'])
        except Folder.DoesNotExist:
            pass
