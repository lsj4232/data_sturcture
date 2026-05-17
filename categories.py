#!/usr/bin/env python3
# Hand-curated study categories for each (exam, problemNo, sqNo).
# Keyed as "회차:문제번호:설문번호" (e.g. "62회:1:1").
#
# Fields (데이터구조론 문맥):
#   toc        — 답안 목차 (풀이 구조)
#   purpose    — 자료구조/알고리즘의 의의·취지
#   article    — 관련 단원/개념명
#   elements   — 판단 요소
#   theory     — 시간/공간복잡도, 이론
#   cases      — 예시·응용 사례
#   resolution — 사안 해결 (실제 풀이 전략)
CATS = {
    "62회:1:1": {
        "toc": "1. 인접 리스트 표현\n2. DFS 알고리즘 적용\n3. 방문 순서 도출",
        "purpose": "인접 리스트는 정점 수에 비해 간선이 적은 희소(sparse) 그래프에서 인접 행렬보다 공간 효율이 높다. DFS는 한 분기를 깊이 끝까지 탐색 후 백트랙하는 그래프 순회법으로, 위상정렬·연결성판단·사이클검출 등의 기초가 된다.",
        "article": "Graph: Adjacency List / DFS",
        "elements": "정점의 인접 리스트 정렬 순서가 DFS 결과를 결정한다.",
        "theory": "인접 리스트 공간: O(V+E). DFS 시간: O(V+E), 공간: O(V) (재귀 스택+방문배열).",
        "cases": "트리 순회, 사이클 검출, 위상정렬, 강한연결요소(SCC)",
        "resolution": "정점 라벨 알파벳 순으로 인접 리스트를 유지하고, 시작 A에서 인접 첫 원소부터 재귀 호출한다.",
    },
    "62회:1:2": {
        "toc": "1. 간선 정렬 (Kruskal)\n2. Kruskal: 사이클 검사 + 채택\n3. Sollin: 각 컴포넌트의 최소 외부 간선 동시 선택\n4. 결과 비교",
        "purpose": "최소비용신장트리(MST)는 모든 정점을 연결하는 신장 트리 중 간선 가중치 합이 최소인 트리로, 네트워크 설계·클러스터링의 기초이다.",
        "article": "MST: Kruskal / Sollin (Boruvka)",
        "elements": "Kruskal: Union-Find로 사이클 검사. Sollin: 컴포넌트별 최소 간선 동시 선택, 라운드 반복.",
        "theory": "Kruskal: O(E log E). Sollin: O(E log V) (라운드마다 컴포넌트 수가 절반 이상 감소).",
        "cases": "Prim 알고리즘과 비교: Prim은 정점 기반, Kruskal·Sollin은 간선/컴포넌트 기반.",
        "resolution": "두 알고리즘 모두 동일한 MST(총 비용 53)를 도출함을 보이며, 알고리즘별 진행 과정을 표로 정리한다.",
    },
    "62회:1:3": {
        "toc": "1. Floyd의 점화식\n2. D^(0) ~ D^(5) 단계별 갱신\n3. 최단 거리표 완성",
        "purpose": "Floyd-Warshall은 음의 가중치를 허용하는(음의 사이클은 불가) 모든 쌍 최단 경로 알고리즘으로, 동적계획법의 대표 예시이다.",
        "article": "All-Pairs Shortest Path: Floyd-Warshall",
        "elements": "점화식: D^(k)[i][j] = min(D^(k-1)[i][j], D^(k-1)[i][k] + D^(k-1)[k][j])",
        "theory": "시간 O(V³), 공간 O(V²). Dijkstra |V|회 반복(O(V·E log V))보다 V가 작을 때 유리.",
        "cases": "교통망 최단 경로, 게임 그래프 분석, 전이폐포(transitive closure).",
        "resolution": "정점 5개이므로 k=1..5로 5번 행렬 갱신. 각 단계에서 변화가 있는 셀만 강조해 가독성을 높인다.",
    },
    "62회:2:1": {
        "toc": "1. 동적 크기 조정\n2. 메모리 사용 정합성 (포인터 오버헤드/캐시 효과 부수 언급)",
        "purpose": "스택은 LIFO 자료구조로 함수 호출, 식 평가, 역추적 등의 기반. 구현 방식에 따라 제약과 성능 특성이 달라진다.",
        "article": "Stack: Array vs Linked",
        "elements": "고정 크기 vs 동적 할당, 메모리 지역성, 포인터 오버헤드.",
        "theory": "두 구현 모두 push/pop이 O(1)이지만 상수 인자와 메모리 패턴이 다르다.",
        "cases": "함수 호출 스택(연결 스택형), 한정된 수식 평가(배열 스택형).",
        "resolution": "배열 스택의 약점을 기준으로 연결 스택의 보완점을 대비시켜 서술.",
    },
    "62회:2:2": {
        "toc": "1. 우선순위 규칙\n2. 토큰별 스택 상태 표 작성",
        "purpose": "중위→후위 변환은 사람이 읽기 쉬운 표기를 컴퓨터가 평가하기 쉬운 표기로 바꾸는 과정으로, 컴파일러 식 처리의 핵심.",
        "article": "Stack 응용: Infix-to-Postfix (Shunting-Yard)",
        "elements": "연산자 우선순위, 결합 방향, 괄호 처리.",
        "theory": "한 패스 O(n)에 변환 가능. 스택 최대 크기는 식의 깊이에 비례.",
        "cases": "수식 컴파일, 계산기 구현, 표현식 최적화.",
        "resolution": "토큰별 입력/스택/출력 표를 만들어 풀이 흐름을 시각적으로 검증한다.",
    },
    "62회:2:3": {
        "toc": "1. 평가 규칙 (피연산자 push, 연산자 pop 두 개 후 push)\n2. 토큰별 스택 추적",
        "purpose": "후위 평가는 괄호·우선순위 처리가 필요 없는 단순 스택 알고리즘으로, 변환 결과를 바로 실행 가능하게 한다.",
        "article": "Stack 응용: Postfix Evaluation",
        "elements": "이항 연산자의 좌·우 피연산자 순서 (먼저 pop = 우항).",
        "theory": "O(n) 시간, O(n) 공간 (피연산자 개수만큼 스택).",
        "cases": "RPN 계산기(HP), JVM 바이트코드 평가.",
        "resolution": "변수값이 미지정이므로 부분식을 기호로 표현하며 단계별 스택 상태를 기록.",
    },
    "62회:3:1": {
        "toc": "1. 삽입정렬 i=1..6 진행\n2. 퀵정렬 partition 호출별 표 작성",
        "purpose": "두 정렬은 비교 기반 정렬의 대표로, 입력 특성에 따라 성능이 크게 갈리는 점을 보이는 비교 학습 도구이다.",
        "article": "Sorting: Insertion Sort / Quick Sort",
        "elements": "삽입정렬: 부분 정렬된 데이터에 강함. 퀵정렬: 피벗 전략이 성능을 좌우.",
        "theory": "삽입정렬 평균 O(n²), 퀵정렬 평균 O(n log n).",
        "cases": "표준 라이브러리: 작은 부분배열엔 삽입정렬, 큰 배열엔 퀵·머지 하이브리드 사용.",
        "resolution": "주어진 의사코드의 partition을 충실히 따라 표의 한 행씩 채워 가는 방식이 정답을 가른다.",
    },
    "62회:3:2": {
        "toc": "1. 시간복잡도 (best/avg/worst)\n2. 입력 특성 분석\n3. 비교 횟수 추정\n4. 결론",
        "purpose": "복잡도는 대규모 입력의 점근적 거동을 비교하지만, 작은·부분정렬 입력에서는 상수 인자와 실제 비교 횟수가 결정적이다.",
        "article": "Sorting: Complexity Comparison",
        "elements": "최선/평균/최악 케이스, 안정성, 메모리.",
        "theory": "삽입정렬 최선 O(n), 퀵정렬(끝값 피벗) 최악 O(n²).",
        "cases": "Python Timsort, Java DualPivotQuicksort 의 입력 분기.",
        "resolution": "이 입력은 거의 정렬된 형태에 가까워 삽입정렬에 유리. 비교 횟수 추정으로 정량 근거 제시.",
    },
    "62회:3:3": {
        "toc": "1. 중앙값 피벗 적용 과정\n2. 호출별 표 작성\n3. 성능 개선 여부 및 이유 설명",
        "purpose": "Median-of-three 피벗은 정렬·역정렬 입력에서 퀵정렬의 최악 O(n²) 위험을 완화하는 표준 기법.",
        "article": "Quick Sort 최적화: Median-of-Three Pivot",
        "elements": "피벗 선택 비용 O(1) vs 분할 균형 이득.",
        "theory": "균형 분할이 보장되면 평균뿐 아니라 거의 모든 실제 입력에서 O(n log n) 유지.",
        "cases": "C qsort, C++ std::sort introsort 구현.",
        "resolution": "단순 끝값 피벗 대비 호출/비교 횟수 감소를 표로 비교하여 정량적 개선 효과를 입증.",
    },
    "62회:4:1": {
        "toc": "1. BST 삽입 규칙\n2. 키별 위치 결정 단계\n3. 최종 트리 그림",
        "purpose": "BST는 평균 O(log n) 탐색을 제공하는 기본 동적 사전 구조. 삽입 순서가 트리 모양과 균형을 결정.",
        "article": "Binary Search Tree (BST)",
        "elements": "좌측 부분트리 < 루트 < 우측 부분트리 불변식.",
        "theory": "균형 시 높이 O(log n), 최악(정렬 입력)에 O(n).",
        "cases": "AVL/RB 트리의 기초, std::map(레드-블랙), 데이터베이스 인덱스.",
        "resolution": "삽입 순서 26→...→37을 차례로 추적하면 균형은 아니지만 한쪽으로 치우치지도 않은 트리가 만들어진다.",
    },
    "62회:4:2": {
        "toc": "1. 배열 표현 인덱스 매핑\n2. 연결 표현 노드 구조\n3. 각 방식의 장·단점",
        "purpose": "동일한 논리 트리도 저장 방식에 따라 성능·메모리 특성이 달라진다.",
        "article": "Tree Representation: Array vs Linked",
        "elements": "공간 효율, 접근 비용, 확장성, 캐시 지역성.",
        "theory": "배열 표현은 깊이 d에 대해 O(2^d) 공간을 요구. 연결 표현은 O(n).",
        "cases": "힙은 배열 표현, BST/이진트리는 일반적으로 연결 표현.",
        "resolution": "주어진 BST가 균형이 아니라는 점을 활용해 배열 표현의 메모리 낭비 사례를 명시적으로 보인다.",
    },
    "62회:4:3": {
        "toc": "1. 전위·중위·후위 정의\n2. 레벨순서(BFS) 정의\n3. 각 결과 도출",
        "purpose": "트리 순회는 노드 처리 순서를 규정한다. 응용에 따라 전위(복사), 중위(BST 정렬값), 후위(삭제·후위계산), 레벨순서(BFS)가 선택된다.",
        "article": "Tree Traversal: 4 patterns",
        "elements": "재귀(DFS 류) 3종 vs 큐 기반(BFS) 1종.",
        "theory": "각 순회 O(n) 시간. 재귀 깊이 O(h)~O(n), 레벨순서 큐 크기 최대 O(n/2).",
        "cases": "AST 처리, 디렉터리 트리, 의사결정 트리.",
        "resolution": "BST의 중위 순회가 오름차순이라는 성질로 (3) 검증이 용이.",
    },
}
