"""
LLM API 클라이언트 (OpenAI GPT + Gemini 지원)
"""
import json
import logging
import re
import time

from django.conf import settings
from rest_framework.exceptions import ValidationError

from ..prompts import BATCH_CLASSIFICATION_PROMPT, CLASSIFICATION_PROMPT, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM API 클라이언트 (GPT 우선, Gemini 폴백) - LangChain 통합"""

    def __init__(self):
        self.llm = None
        self.provider = None

        # OpenAI API 키 확인 (우선)
        openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        google_api_key = getattr(settings, 'GOOGLE_API_KEY', None)

        if openai_api_key:
            try:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    model="gpt-5-nano",
                    api_key=openai_api_key,
                    temperature=0.1,
                    max_tokens=2048,
                )
                self.provider = 'openai'
                logger.info("LLMClient initialized with OpenAI GPT (LangChain)")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")

        # OpenAI 실패 시 Gemini로 폴백
        if self.llm is None and google_api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=google_api_key,
                    temperature=0.1,
                    max_tokens=2048,
                )
                self.provider = 'gemini'
                logger.info("LLMClient initialized with Google Gemini (LangChain)")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini: {e}")

        if self.llm is None:
            raise ValidationError({
                'code': 'LLM_NOT_CONFIGURED',
                'message': 'OPENAI_API_KEY 또는 GOOGLE_API_KEY가 설정되지 않았습니다.'
            })

    def classify_mail(self, mail_data: dict, existing_folders: list) -> dict:
        """
        단일 메일 분류
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
        배치 메일 분류 (최대 20개)
        """
        if len(mails_data) > 20:
            mails_data = mails_data[:20]

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

    def _invoke_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """LLM 호출 (재시도 포함, 지수 백오프)"""
        last_error = None

        for attempt in range(max_retries):
            try:
                return self._invoke_llm(prompt)
            except Exception as e:
                last_error = e
                error_str = str(e).lower()
                logger.warning(f"LLM invoke attempt {attempt + 1} failed ({self.provider}): {e}")

                # Rate limit 에러면 더 긴 대기
                if '429' in error_str or 'rate' in error_str or 'resource_exhausted' in error_str:
                    wait_time = (2 ** attempt) * 5  # 5초, 10초, 20초
                    logger.info(f"Rate limited, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # 일반 에러는 짧은 대기
                    time.sleep(2 ** attempt)  # 1초, 2초, 4초

        raise last_error

    def _invoke_llm(self, prompt: str) -> str:
        """LangChain 통합 LLM 호출"""
        messages = [
            ("system", SYSTEM_PROMPT),
            ("human", prompt)
        ]
        response = self.llm.invoke(messages)
        return response.content

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
