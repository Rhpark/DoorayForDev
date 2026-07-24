---
name: dooray-link
description: Dooray 업무의 웹 주소(URL)를 알려준다. 사용법 /dooray-link <업무번호>. 업무 링크, 웹 주소, 브라우저에서 열기를 원할 때 사용.
disable-model-invocation: true
model: sonnet
effort: low
allowed-tools:
  - PowerShell(python Dooray/dooray.py link *)
  - Bash(python Dooray/dooray.py link *)
---

저장소 루트로 이동한 뒤 실행:

```
python Dooray/dooray.py link <업무번호>
```

원본 결과만 그대로 즉시 보여준다. 요약하지 않는다.
