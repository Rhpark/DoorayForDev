---
name: dooray-status-change
description: Dooray 업무 번호의 현재 상태와 프로젝트 상태 목록을 조회한 뒤 사용자가 선택한 상태로 변경한다. 사용자가 업무 상태 변경을 명시적으로 요청할 때 사용한다.
---

# Dooray 업무 상태 변경

1. 저장소 루트에서 현재 상태와 상태 목록을 조회한다.

```text
python Dooray/dooray.py status 업무번호
python Dooray/dooray.py workflows
```

2. 사용자에게 현재 상태를 알리고 상태 목록을 선택지로 제시해 하나를 고르게 한다. 현재 상태와 같은 항목은 그 사실을 함께 알린다.

3. 사용자가 고른 상태로 변경한다.

```text
python Dooray/dooray.py setstatus 업무번호 "선택한 상태명"
```

4. 출력된 변경 완료 메시지를 사용자에게 확인한다.

업무번호 하나만 입력으로 받는다. 사용자가 원하는 상태명을 미리 언급했더라도 상태 목록 제시와 사용자 선택을 생략하지 않는다.
