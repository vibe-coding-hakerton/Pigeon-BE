from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """커스텀 사용자 모델"""

    class GenderChoices(models.TextChoices):
        MALE = 'M', '남성'
        FEMALE = 'F', '여성'
        OTHER = 'O', '기타'

    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='사용자명',
    )
    gender = models.CharField(
        max_length=1,
        choices=GenderChoices.choices,
        blank=True,
        null=True,
        verbose_name='성별',
    )
    birth_date = models.DateField(
        blank=True,
        null=True,
        verbose_name='생년월일',
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name='전화번호',
    )

    class Meta:
        verbose_name = '사용자'
        verbose_name_plural = '사용자들'

    def __str__(self):
        return self.username
