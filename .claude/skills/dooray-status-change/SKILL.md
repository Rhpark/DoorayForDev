---
name: dooray-status-change
description: Dooray 업무의 상태를 목록에서 선택해 변경한다. 사용법 /dooray-status-change <업무번호> (인자는 업무번호 하나뿐). 사용자가 이 명령을 직접 호출했을 때 사용.
disable-model-invocation: true
model: sonnet
effort: medium
---

1. 저장소 루트로 이동한 뒤 현재 상태와 상태 목록을 조회한다:

```
python Dooray/dooray.py status <업무번호>
python Dooray/dooray.py workflows
```

2. 사용자에게 현재 상태를 알려주고, 상태 목록을 선택지로 제시해 하나를 고르게 한다 (선택 UI가 4개까지만 보여줄 수 있으면 나눠서 제시). 현재 상태와 같은 항목은 표시에서 그 사실을 알려준다.

3. 사용자가 고른 상태로 변경한다:

```
python Dooray/dooray.py setstatus <업무번호> "<선택한 상태명>"
```

4. 출력된 변경 완료 메시지를 사용자에게 확인해준다.

이 명령은 항상 업무번호 하나만 인자로 받는다. 이미 원하는 상태명을 언급하며 호출했더라도 임의로 추측해 3번으로 건너뛰지 말고, 반드시 2번의 목록 제시 → 선택을 거친 뒤 3번을 실행한다.
