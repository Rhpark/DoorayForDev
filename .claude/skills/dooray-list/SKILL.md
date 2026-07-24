---
name: dooray-list
description: 완료되지 않은 Dooray 업무를 최신 등록순으로 N개 보여준다. 사용법 /dooray-list <개수>. 사용자가 이 명령을 직접 호출했을 때 사용.
disable-model-invocation: true
model: sonnet
effort: low
allowed-tools:
  - PowerShell(python Dooray/dooray.py list *)
  - Bash(python Dooray/dooray.py list *)
---

저장소 루트로 이동한 뒤 실행:

```
python Dooray/dooray.py list <개수>
```

원본 결과만 그대로 즉시 보여준다. 요약하지 않는다. 도구 출력 상자는 터미널이 접을 수 있으니, 결과 전체를 답변 본문 코드블록에 붙여넣는다.
