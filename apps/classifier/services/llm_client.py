"""
Gemini API 클라이언트 (LangChain 사용)
"""
import json
import logging
import re

from django.conf import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from rest_framework.exceptions import ValidationError

from ..prompts import BATCH_CLASSIFICATION_PROMPT, CLASSIFICATION_PROMPT, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LLMClient:
    """Gemini 2.5 Flash API 클라이언트"""

    def __init__(self):
        api_key = getattr(settings, 'GOOGLE_API_KEY', None)
        if not api_key:
            raise ValidationError({
                'code': 'LLM_NOT_CONFIGURED',
                'message': 'GOOGLE_API_KEY가 설정되지 않았습니다.'
            })

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.1,
            max_tokens=2048,
        )

    def classify_mail(self, mail_data: dict, existing_folders: list) -> dict:
        """
        단일 메일 분류

        Args:
            mail_data: {
                'id': int,
                'subject': str,
                'sender': str,
                'snippet': str
            }
            existing_folders: [{'id': int, 'path': str}, ...]

        Returns:
            dict: {
                'folder_path': str,
                'is_new_folder': bool,
                'confidence': float,
                'reason': str
            }
        """
        folders_str = self._format_folders(existing_folders)
        prompt = CLASSIFICATION_PROMPT.format(
            folders=folders_str,
            subject=mail_data.get('subject', '(제목 없음)'),
            sender=mail_data.get('sender', '(알 수 없음)'),
            snippet=mail_data.get('snippet', '')[:500]
        )

        try:
            response = self._invoke_with_retry(prompt)
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            raise ValidationError({
                'code': 'LLM_API_ERROR',
                'message': f'AI 분류 실패: {str(e)}'
            })

    def classify_mails_batch(self, mails_data: list, existing_folders: list) -> list:
        """
        배치 메일 분류 (최대 10개)

        Args:
            mails_data: [{'id': int, 'subject': str, 'sender': str, 'snippet': str}, ...]
            existing_folders: [{'id': int, 'path': str}, ...]

        Returns:
            list: [{'mail_id': int, 'folder_path': str, ...}, ...]
        """
        if len(mails_data) > 10:
            mails_data = mails_data[:10]

        folders_str = self._format_folders(existing_folders)
        emails_str = self._format_emails(mails_data)

        prompt = BATCH_CLASSIFICATION_PROMPT.format(
            folders=folders_str,
            emails=emails_str
        )

        try:
            response = self._invoke_with_retry(prompt)
            return self._parse_batch_response(response, mails_data)
        except Exception as e:
            logger.error(f"LLM batch classification failed: {e}")
            raise ValidationError({
                'code': 'LLM_API_ERROR',
                'message': f'AI 배치 분류 실패: {str(e)}'
            })

    def _invoke_with_retry(self, prompt: str, max_retries: int = 2) -> str:
        """LLM 호출 (재시도 포함)"""
        messages = [
            ("system", SYSTEM_PROMPT),
            ("human", prompt)
        ]

        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.llm.invoke(messages)
                return response.content
            except Exception as e:
                last_error = e
                logger.warning(f"LLM invoke attempt {attempt + 1} failed: {e}")
                continue

        raise last_error

    def _format_folders(self, folders: list) -> str:
        """폴더 목록 포맷팅"""
        if not folders:
            return "(폴더 없음 - 새 폴더를 제안해주세요)"
        return "\n".join([f"- {f['path']}" for f in folders])

    def _format_emails(self, mails: list) -> str:
        """이메일 목록 포맷팅"""
        result = []
        for mail in mails:
            result.append(f"""### 이메일 #{mail['id']}
- 제목: {mail.get('subject', '(제목 없음)')}
- 발신자: {mail.get('sender', '(알 수 없음)')}
- 내용: {mail.get('snippet', '')[:200]}
""")
        return "\n".join(result)

    def _parse_response(self, response: str) -> dict:
        """단일 분류 응답 파싱"""
        try:
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    'folder_path': data.get('folder_path', '미분류'),
                    'is_new_folder': data.get('is_new_folder', False),
                    'confidence': float(data.get('confidence', 0.5)),
                    'reason': data.get('reason', '')
                }
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")

        return {
            'folder_path': '미분류',
            'is_new_folder': False,
            'confidence': 0.0,
            'reason': 'AI 응답 파싱 실패'
        }

    def _parse_batch_response(self, response: str, mails_data: list) -> list:
        """배치 분류 응답 파싱"""
        try:
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                data = json.loads(json_match.group())
                results = []
                for item in data:
                    results.append({
                        'mail_id': item.get('mail_id'),
                        'folder_path': item.get('folder_path', '미분류'),
                        'is_new_folder': item.get('is_new_folder', False),
                        'confidence': float(item.get('confidence', 0.5)),
                        'reason': item.get('reason', '')
                    })
                return results
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse batch response: {e}")

        return [
            {
                'mail_id': mail['id'],
                'folder_path': '미분류',
                'is_new_folder': False,
                'confidence': 0.0,
                'reason': 'AI 응답 파싱 실패'
            }
            for mail in mails_data
        ]
