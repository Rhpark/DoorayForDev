---
name: dooray-reply
description: Dooray 업무에 댓글을 등록한다. 사용법 /dooray-reply <업무번호> <댓글 내용>. 업무에 진행 상황이나 메모를 남길 때 사용.
disable-model-invocation: true
model: sonnet
effort: medium
---

댓글 내용을 임의로 다듬지 말고 그대로 스크래치패드 임시 파일에 쓴 뒤(셸 이스케이프 방지), 저장소 루트로 이동해 실행:

```
python Dooray/dooray.py comment <업무번호> --file <임시파일경로>
```

댓글은 API 토큰 소유자 명의로 등록된다.
