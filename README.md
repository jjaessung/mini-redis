# Mini Redis

해시맵, 이중 연결 리스트, 최소 힙을 직접 구현한 CLI 기반 인메모리
key-value 저장소입니다. Python 3.8 이상에서 외부 패키지 없이 실행할 수
있습니다.

## 실행

```bash
python main.py
```

```text
mini-redis> SET user:1 "Alice"
OK
mini-redis> GET user:1
"Alice"
mini-redis> exit
```

지원 명령어는 다음과 같습니다.

- `SET key value`
- `GET key`
- `DEL key`
- `EXISTS key`
- `DBSIZE`
- `KEYS`
- `CONFIG SET maxmemory bytes`
- `INFO memory`
- `EXPIRE key seconds`
- `TTL key`
- `exit`, `quit`

공백을 포함한 값은 큰따옴표로 감쌀 수 있습니다.

```text
mini-redis> SET greeting "hello world"
OK
```

## 구조

- `doubly_linked_list.py`: 최근 사용 항목을 앞에 두는 O(1) LRU 리스트
- `hash_map.py`: FNV-1a 해시와 체이닝 충돌 해결을 사용하는 해시맵
- `min_heap.py`: 가장 이른 만료 시각을 루트에 두는 최소 힙
- `mini_redis.py`: 자료구조를 결합한 명령 실행, 메모리 및 TTL 관리
- `main.py`: `mini-redis>` REPL 진입점
- `tests/`: 자료구조와 통합 동작 테스트

TTL 힙에서 이미 무효화된 과거 만료 레코드는 꺼낼 때 현재 레코드의 버전과
비교해 무시하는 lazy deletion 방식으로 처리합니다. 키가 실제로 삭제될 때는
데이터, 현재 TTL 정보, LRU 노드 및 `used_memory`가 함께 정리됩니다.

## 테스트

```bash
python -m unittest discover -v
```

