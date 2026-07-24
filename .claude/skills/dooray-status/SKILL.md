---
name: dooray-status
description: Dooray 업무의 현재 상태만 확인한다 (제목만 함께 표시, 본문·댓글은 보여주지 않음). 사용법 /dooray-status <업무번호>. 사용자가 이 명령을 직접 호출했을 때 사용.
disable-model-invocation: true
model: sonnet
effort: low
allowed-tools:
  - PowerShell(python Dooray/dooray.py status *)
  - Bash(python Dooray/dooray.py status *)
---

저장소 루트로 이동한 뒤 실행:

```
python Dooray/dooray.py status <업무번호>
```

원본 결과만 그대로 즉시 보여준다. 요약하지 않는다. 도구 출력 상자는 터미널이 접을 수 있으니, 결과 전체를 답변 본문 코드블록에 붙여넣는다.
