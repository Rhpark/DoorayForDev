---
name: dooray-read
description: Dooray 업무의 제목·업무 상태·내용을 조회한다. 사용법 /dooray-read <업무번호>. 사용자가 이 명령을 직접 호출했을 때 사용.
disable-model-invocation: true
model: sonnet
effort: low
---

저장소 루트로 이동한 뒤 실행:

```
python Dooray/dooray.py read <업무번호>
```

원본 결과만 그대로 즉시 보여준다. 요약하지 않는다.
첨부파일 다운로드를 원하면 `python Dooray/dooray.py download <업무번호> [파일명|번호|all]`을 실행한다.
