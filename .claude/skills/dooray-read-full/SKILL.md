---
name: dooray-read-full
description: Dooray 업무의 제목·상태·내용·댓글 이력을 조회한다. 사용법 /dooray-read-full <업무번호> [개수]. 업무의 전체 맥락이나 댓글 이력까지 필요할 때 사용.
disable-model-invocation: true
model: sonnet
effort: low
allowed-tools:
  - PowerShell(python Dooray/dooray.py full *)
  - Bash(python Dooray/dooray.py full *)
---

저장소 루트로 이동한 뒤 실행 (개수 생략 시 댓글 전체, 지정 시 최신 N개):

```
python Dooray/dooray.py full <업무번호> [개수]
```

원본 결과만 그대로 즉시 보여준다. 요약하지 않는다.
첨부파일 다운로드를 원하면 `python Dooray/dooray.py download <업무번호> [파일명|번호|all]`을 실행한다.
