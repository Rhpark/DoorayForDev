---
name: dooray-read
description: Dooray 업무 번호로 제목, 현재 상태, 본문과 첨부파일 정보를 조회한다. 사용자가 업무 읽기나 업무 내용 확인을 명시적으로 요청할 때 사용한다.
---

# Dooray 업무 읽기

저장소 루트에서 다음 명령을 실행한다.

```text
python Dooray/dooray.py read 업무번호
```

원본 결과만 그대로 즉시 보여준다. 요약하지 않는다. 도구 출력 상자는 터미널이 접을 수 있으니, 결과 전체를 답변 본문 코드블록에 붙여넣는다.

첨부파일 다운로드를 요청하면 다음 명령을 실행한다.

```text
python Dooray/dooray.py download 업무번호 파일명-또는-번호-또는-all
```
