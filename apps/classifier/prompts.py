"""
메일 분류 프롬프트 템플릿
"""

SYSTEM_PROMPT = """당신은 이메일 분류 전문가입니다. 사용자의 이메일을 분석하여 적절한 폴더로 분류합니다.

## 규칙
1. 이메일의 제목, 발신자, 내용을 종합적으로 분석합니다.
2. 기존 폴더 목록이 주어지면, 가장 적합한 폴더를 선택합니다.
3. 적합한 폴더가 없으면 새 폴더 이름을 제안합니다.
4. 폴더 이름은 간결하고 명확해야 합니다 (예: "업무", "개인", "뉴스레터", "영수증").
5. 새 폴더는 최대 2단계 깊이까지 생성할 수 있습니다 (예: "업무/프로젝트A").

## 출력 형식
JSON 형식으로 응답하세요:
{
  "folder_path": "폴더 경로",
  "is_new_folder": true/false,
  "confidence": 0.0-1.0,
  "reason": "분류 이유 (한 문장)"
}
"""

CLASSIFICATION_PROMPT = """## 기존 폴더 목록
{folders}

## 분류할 이메일
- 제목: {subject}
- 발신자: {sender}
- 내용 미리보기: {snippet}

이 이메일을 어떤 폴더로 분류해야 할까요? JSON 형식으로 응답하세요."""

BATCH_CLASSIFICATION_PROMPT = """## 기존 폴더 목록
{folders}

## 분류할 이메일 목록
{emails}

각 이메일을 분류하고 JSON 배열로 응답하세요. 각 항목은 mail_id와 함께 반환해야 합니다:
[
  {{
    "mail_id": 1,
    "folder_path": "폴더 경로",
    "is_new_folder": true/false,
    "confidence": 0.0-1.0,
    "reason": "분류 이유"
  }},
  ...
]
"""
