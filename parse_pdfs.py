#!/usr/bin/env python3
import subprocess
import re
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Hand-supplied answer text. 데이터구조론 has no official answer files,
# so Claude-authored answers (defined in answers.py) are injected here.
try:
    from answers import ANSWERS as ANSWER_OVERRIDES
except ImportError:
    ANSWER_OVERRIDES = {}

# Hand-curated study categories (categories.py) and hints (hints.py).
try:
    from categories import CATS as CURATED_CATS
except ImportError:
    CURATED_CATS = {}
try:
    from hints import HINTS as CURATED_HINTS
except ImportError:
    CURATED_HINTS = {}

# Hand-supplied question text overrides — used when pdftotext misses parts
# of the stem or when OCR'd scanned PDFs need correction.
QUESTION_OVERRIDES = {}

# Hand-supplied passage (the shared problem stem before the (1)(2)(3) sub-questions).
# Used to clean up PDF extraction artifacts — PUA (Private Use Area) chars from
# subscript glyphs, broken graph/diagram descriptions, etc. Keyed by (exam, problemNo).
PASSAGE_OVERRIDES = {
    # 60회 문제-1: 공정·작업 첨자(P₀, a₀ 등)가 PUA 로 추출되며 깨짐.
    # AOE 네트워크 그래프 자체도 텍스트에 안 들어오므로 간선 목록을 함께 명시.
    ('60회', 1): (
        "아래와 같이 7개의 공정(P₀, P₁, ⋯, P₆)과 9개의 작업(a₀, a₁, ⋯, a₈)으로 "
        "구성된 프로젝트 스케줄을 표현한 AOE 네트워크가 주어졌다. 괄호의 숫자는 "
        "작업별 소요시간이다. 다음의 물음에 답하시오.\n\n"
        "[그래프 G — 간선 목록 (출발→도착, 소요시간)]\n"
        "  a₀ : P₀ → P₁ (4)        a₁ : P₀ → P₂ (2)        a₂ : P₀ → P₃ (3)\n"
        "  a₃ : P₁ → P₆ (5)        a₄ : P₁ → P₅ (3)        a₅ : P₂ → P₄ (1)\n"
        "  a₆ : P₃ → P₅ (4)        a₇ : P₄ → P₅ (2)        a₈ : P₅ → P₆ (5)\n\n"
        "(시작 공정 P₀, 종료 공정 P₆)"
    ),

    # 48회 문제-2: 명제식의 변수 x₁, x₂, x₃ 와 부정 기호 ¬ 가 PUA 로 깨져 나옴.
    # 원본 PDF 의 식: (x₁ ∧ ¬x₂) ∨ (¬x₁ ∧ ¬x₃) ∨ x₃
    ('48회', 2): (
        "명제식의 만족성(satisfiability) 문제는 식의 값이 참이 되도록 Boolean 변수에 "
        "값을 지정할 수 있는 방법이 있는지를 결정하는 문제이다. 다음은 명제식의 한 예이다.\n"
        "(단, ∧는 AND, ∨는 OR, ¬는 NOT 연산자를 나타낸다)\n\n"
        "    (x₁ ∧ ¬x₂) ∨ (¬x₁ ∧ ¬x₃) ∨ x₃"
    ),
}

# Hand-supplied complete problem text — used when both passage and sub-questions
# need to be specified together (e.g. fully scanned PDFs where the auto-parser
# can't recover structure at all). Keyed by (exam, problemNo).
# Value: dict: { 'points': N, 'passage': '...', 'subquestions': [{no,points,question}, ...] }
PROBLEM_OVERRIDES = {
    # ─── 제53회(2016) — 추출 텍스트의 줄바꿈/괄호 깨짐 보정 ───
    ('53회', 1): {
        'points': 30,
        'passage': "탐색을 효율적으로 하기 위한 다양한 탐색 트리에 관하여 다음의 물음에 답하시오.",
        'subquestions': [
            {'no': 1, 'points': 8, 'question': "다음의 원소를 차례로 삽입하였을 때 다음 각 트리의 구성 결과를 그리시오.\n  62, 45, 15, 20, 78, 88, 73, 55, 10, 40\n  1) 이진 탐색 트리(Binary Search Tree)\n  2) AVL 트리(Adelson-Velskii and Landis Tree)\n  3) 2-3 트리(2-3 Tree)"},
            {'no': 2, 'points': 8, 'question': "(1) 의 결과에 34와 32를 차례로 삽입하는 과정을 상세히 기술하시오.\n  1) 이진 탐색 트리\n  2) AVL 트리\n  3) 2-3 트리"},
            {'no': 3, 'points': 5, 'question': "(2) 의 완성된 트리로부터 32와 73을 각각 찾기 위해 발생한 키와 원소들 간의 총 비교 횟수와 트리 노드의 총 방문횟수를 구하시오. (단, 노드에 값이 여러 개인 경우에는 작은 값부터 비교한다.)\n  1) 이진 탐색 트리\n  2) AVL 트리\n  3) 2-3 트리"},
            {'no': 4, 'points': 9, 'question': "(2), (3) 의 결과에 따라 세 가지 트리의 삽입 및 탐색 성능을 논하고, 각 트리가 최적의 성능을 보이는 경우를 설명하시오."},
        ],
    },
    ('53회', 2): {
        'points': 20,
        'passage': "알고리즘 분석과 재귀에 관한 다음 물음에 답하시오.",
        'subquestions': [
            {'no': 1, 'points': 7, 'question': "주어진 동일한 문제를 해결하기 위해서는 여러 가지 알고리즘이 존재하고, 평균수행시간이나 이의 상수, 그리고 데이터의 수에 따라 어느 알고리즘이 더 좋은 알고리즘인가를 알 수 있다. 이것을 확인하기 위하여 **삽입 정렬 알고리즘과 병합 정렬 알고리즘**으로 알고리즘 선택의 중요성을 설명하시오."},
            {'no': 2, 'points': 9, 'question': "성능이 서로 다른 2 대의 컴퓨터와 서로 다른 알고리즘을 사용할 경우, 컴퓨터의 선택보다 알고리즘의 선택이 더 중요할 경우가 있다. 알고리즘 선택의 중요성을 보이기 위하여 평균수행시간을 계산하고 이를 기준으로 설명하시오.\n  (단, 컴퓨터 A 는 초당 10⁹ 개의 명령어를 실행, 삽입 정렬 알고리즘을 사용, 평균수행시간 상수 c₁ = 2.\n   컴퓨터 B 는 초당 10⁷ 개의 명령어를 실행, 병합 정렬 알고리즘을 사용, 평균수행시간 상수 c₂ = 50.\n   정렬할 데이터 수 n = 100 만 (10⁶ 개). 2¹⁰ = 10³ 으로 가정.)"},
            {'no': 3, 'points': 4, 'question': "다음은 재귀알고리즘에 대한 내용이다. 질문에 답하시오. 먼저, 재귀알고리즘을 정의하시오. 그리고, 다음은 팩토리얼 재귀알고리즘을 보여주고 있다. ① 에는 무엇이 들어가야 하는가?\n\n  AA(n)\n      // n 은 음이 아닌 정수\n      if ( n <= 1 ) then return 1\n      else return ( ① );\n  end AA()"},
        ],
    },
    ('53회', 3): {
        'points': 30,
        'passage': "정수 배열을 정렬하기 위한 안정적(Stable) 프로그램을 완성하고자 한다. 다음의 물음에 답하시오.",
        'subquestions': [
            {'no': 1, 'points': 3, 'question': "안정적인 정렬 알고리즘이란 무엇인지 설명하시오."},
            {'no': 2, 'points': 7, 'question': "삽입 정렬 프로그램(오름차순 정렬) 을 C 언어로 완성하시오.\n  1) void insertionSort(int data[], int n) { int i, j; … } 의 본체 작성.\n  2) 다음 입력 데이터의 정렬 과정을 상세히 기술하시오.\n     데이터: 1, 4, 17, 19, 5, 17, 4"},
            {'no': 3, 'points': 10, 'question': "삽입 정렬의 성능 향상을 위해 삽입 위치를 빠르게 검색하기 위한 방법으로 이진 탐색을 적용하고자 한다. (단, 개선된 삽입 정렬 또한 안정적이어야 한다.)\n  1) 다음 modifiedBinarySearch 의 빈칸 ①, ②, ③, ④ 를 완성하시오.\n     int modifiedBinarySearch(int data[], int key, int n) {\n         int first = 0;  int last = n - 1;  int middle;\n         while (first <= last) {\n             middle = (first + last) / 2;\n             if      (data[middle] == key)   ____①____\n             else if (data[middle] >  key)   ____②____\n             else                            ____③____\n         }\n         ____④____\n     }\n  2) 위 함수를 사용하도록 binaryInsertionSort(int data[], int n) 을 개선하여 작성하시오."},
            {'no': 4, 'points': 10, 'question': "(2), (3) 에서 완성된 두 삽입 정렬 프로그램들에 대해 다음 물음에 답하시오.\n  1) 각 정렬 프로그램이 안정적임을 보이시오.\n  2) 각 프로그램에서의 원소들 간의 비교 횟수를 계산하시오.\n  3) 각 정렬 프로그램의 최선·평균·최악의 경우의 성능(비교만 고려) 을 시간 복잡도로 나타내시오."},
        ],
    },
    ('53회', 4): {
        'points': 20,
        'passage': "다음은 9 개 도시 간의 거리를 나타내고 있다. (단위 = km)\n\n  서울–인천: 35     부산–대구: 106    광주–전주: 98     강릉–원주: 117\n  대전–대구: 154    전주–대전: 82     인천–전주: 247    서울–원주: 126\n  서울–대전: 150    원주–대구: 220    대전–원주: 162    광주–대전: 120\n\n(총 12 개 간선, 9 개 도시 = {서울, 인천, 부산, 대구, 광주, 전주, 강릉, 원주, 대전}.)\n각 도시와 거리에 대한 자료에 관하여 다음의 물음에 답하시오.",
        'subquestions': [
            {'no': 1, 'points': 4, 'question': "위 데이터를 가중치 그래프로 표현하시오."},
            {'no': 2, 'points': 8, 'question': "인접 리스트와 인접 행렬로 작성하시오. (단, 인접 리스트의 가중치는 무시하고, 인접 행렬의 가중치는 포함한다.)"},
            {'no': 3, 'points': 8, 'question': "서울에서 시작하는 최소거리 신장 트리를 완성하여 보여주고, 선택되는 도시의 순서와 그 도시까지의 거리를 각각 산출하시오."},
        ],
    },

    # ─── 제56회(2019) — 스캔본 PDF, pdftotext 추출 0byte. 전체 수동 입력 ───
    ('56회', 1): {
        'points': 30,
        'passage': "구간힙(interval heap)에 관한 다음 물음에 답하시오.\n\n[주어진 구간힙 — 각 노드는 (low, high) 쌍, 부모 구간이 자식 구간을 포함]\n                          (2, 30)\n                       /          \\\n                  (3, 17)          (4, 15)\n                  /      \\          /      \\\n              (4,12)  (3,11)   (5,10)   (6,15)\n              /   \\    /   \\    /   \\\n          (4,10)(5,11)(5,9)(4,7)(8,8)(7,9)",
        'subquestions': [
            {'no': 1, 'points': 5, 'question': "구간힙을 정의하고, 그 특성에 관하여 설명하시오."},
            {'no': 2, 'points': 10, 'question': "위 구간힙에 의해 정의된 최소힙(Min-heap)과 최대힙(Max-heap)을 각각 그리시오."},
            {'no': 3, 'points': 10, 'question': "위 구간힙에 40과 32를 차례대로 삽입할 때 각각의 구간힙을 그리시오."},
            {'no': 4, 'points': 5, 'question': "물음 (3)에서 마지막으로 만들어지는 구간힙에서 최소 원소를 제거한 후의 구간힙을 그리시오."},
        ],
    },
    ('56회', 2): {
        'points': 20,
        'passage': "그래프 G에 관하여 다음 물음에 답하시오.\n\n[그래프 G — 무방향 가중치 그래프, 정점 8개 (A,B,C,D,E,F,G,H)]\n  간선(가중치) :\n    A–B(1)   A–F(2)   A–G(6)\n    B–C(1)   B–D(2)   B–E(4)\n    C–E(4)   C–G(1)\n    D–E(2)   D–F(1)\n    E–F(2)   E–H(4)\n    F–H(2)   G–H(5)\n  (총 14개 간선)",
        'subquestions': [
            {'no': 1, 'points': 7, 'question': "그래프 G에 대해 프림(Prim) 알고리즘으로 최소신장트리를 구하는 과정을 나타내시오. (단, 노드 A를 시작 정점으로 선택한다.)"},
            {'no': 2, 'points': 7, 'question': "그래프 G에 대해 크루스칼(Kruskal) 알고리즘으로 최소신장트리를 구하는 과정을 나타내시오. (단, 간선 A–B를 먼저 선택한다.)"},
            {'no': 3, 'points': 6, 'question': "그래프 G에 대해 솔린(Sollin) 알고리즘으로 최소신장트리를 구하는 과정을 나타내시오."},
        ],
    },
    ('56회', 3): {
        'points': 30,
        'passage': "다음은 자료구조에서 많이 사용하고 있는 정렬 알고리즘이다. 다음 물음에 답하시오.\n\n[의사코드]\nAAASort(a[], size)\n    n ← size - 1;        // a[0] 미사용, a[1] 은 가장 큰 원소, n 은 실제 원소 수\n    for ( i ← n/2; i ≥ 2; i ← i-1 ) do {\n        BBB(a, i, n);\n    }\n    for ( i ← n; i ≥ 2; i ← i-1 ) do {\n        BBB(a, 1, i-1);\n        temp ← a[1];\n        ____(가-1)____\n        ____(가-2)____\n    }\nend AAASort()\n\nBBB(a[], h, m)\n    imsi ← a[h];\n    for ( j ← 2*h; j ≤ m; j ← 2*j ) do {\n        if ( j < m ) then\n            if ( a[j] < a[j+1] ) then j ← j+1;\n        if ( imsi ≥ a[j] ) then exit\n        else {\n            ____(나)____\n        }\n    }\n    a[j/2] ← imsi;\nend BBB()",
        'subquestions': [
            {'no': 1, 'points': 12, 'question': "위의 알고리즘 AAASort 와 BBB 를 설명하시오."},
            {'no': 2, 'points': 9, 'question': "위의 알고리즘에서 (가-1), (가-2), (나)에 들어갈 적합한 pseudo code 를 표현하시오."},
            {'no': 3, 'points': 9, 'question': "위 알고리즘의 시간복잡도를 설명하시오."},
        ],
    },
    ('56회', 4): {
        'points': 20,
        'passage': "이진트리에 관하여 다음 물음에 답하시오.",
        'subquestions': [
            {'no': 1, 'points': 10, 'question': "N 개의 노드를 가지고 있는 이진트리에서 차수(degree) 가 0 인 단말노드의 개수를 T 라고 하고, 차수가 2 인 노드의 개수를 M 이라고 하자. 이 경우, T = M + 1 이 성립함을 설명하시오."},
            {'no': 2, 'points': 10, 'question': "N 개의 노드를 가지고 있는 이진트리의 가능한 최대 깊이는 N 이고, 최소 깊이는 ⌊log₂ N⌋ + 1 임을 설명하시오."},
        ],
    },

    # ─── 제57회(2020) — 스캔본 PDF, pdftotext 추출 0byte. 전체 수동 입력 ───
    ('57회', 1): {
        'points': 30,
        'passage': "다음은 이진탐색트리(Binary Search Tree)에서 특정 키값을 갖는 노드를 삭제할 때 발생하는 3가지 상황(case1, case2, case3)을 재귀적인(Recursive) 방법으로 해결하는 함수이다. 이 함수는 이진탐색트리에서 키값(key)을 갖는 노드를 삭제한 후 갱신된 트리의 루트 노드 포인터(tree)를 반환한다. 다음 물음에 답하시오. (단, free()는 할당된 노드 공간을 해제하는 함수이다.)\n\n[코드]\ntypedef struct node * node_ptr;\nstruct node {\n    int key;\n    node_ptr left;\n    node_ptr right;\n};\n\nnode_ptr deleteBST(node_ptr tree, int key) {\n    node_ptr temp;\n    if (!tree) return tree;\n    if (key < tree->key)\n        tree->left = ___(가-1)___;\n    else if (key > tree->key)\n        tree->right = ___(가-2)___;\n    else {\n        // case1 and case2\n        if (!tree->left) {\n            ___(나-1)___;\n            free(tree);\n            return temp;\n        }\n        else if (!tree->right) {\n            ___(나-2)___;\n            free(tree);\n            return temp;\n        }\n        // case3\n        temp = findNode(___(다-1)___);\n        tree->key = temp->key;\n        ___(다-2)___;\n    }\n    return tree;\n}\n\nnode_ptr findNode(node_ptr tree) {\n    node_ptr imsi = tree;\n    while (imsi && ___(라-1)___) {\n        ___(라-2)___;\n    }\n    return imsi;\n}",
        'subquestions': [
            {'no': 1, 'points': 8, 'question': "이진탐색트리에서 노드 삭제시 트리의 형태별로 발생할 수 있는 3가지 상황(case1, case2, case3)과 해결 방법을 각각 설명하시오. (단, case3은 2가지 해결 방법을 모두 설명해야 한다.)"},
            {'no': 2, 'points': 10, 'question': "문항(1)에서 설명한 (case1)과 (case2) 상황을 재귀적으로 해결하는 코드를 빈칸 (가-1), (가-2), (나-1), (나-2)에 C언어로 작성하시오."},
            {'no': 3, 'points': 12, 'question': "문항(1)에서 설명한 (case3) 상황을 해결하는 방법을 빈칸 (다-1) ~ (라-2)에 C언어로 작성하시오. (단, 2가지 방법을 각각 작성해야 한다.)"},
        ],
    },
    ('57회', 2): {
        'points': 20,
        'passage': "다음 표는 방향 그래프(Directed Graph)의 간선(Edge)과 비용(Cost)에 관한 정보이다. 다음 물음에 답하시오.\n\n[간선·비용 목록]\n  <a, b> : 3        <a, d> : 8\n  <b, c> : 6        <c, e> : 4\n  <c, f> : 7        <d, c> : 9\n  <d, f> : 2        <e, d> : 5\n  <e, f> : 10\n\n(정점: a, b, c, d, e, f — 모두 6개. 모든 간선은 방향성을 가짐.)",
        'subquestions': [
            {'no': 1, 'points': 8, 'question': "이 그래프를 노드(a)에서 출발하여 깊이 우선 탐색(Depth First Search) 방법으로 탐색할 경우, 방문 노드 순서와 방문에 사용된 간선으로 구성되는 신장트리(DFS Spanning Tree)를 작성하고, 간선 비용의 합을 구하시오. (단, 간선 비용이 적은 노드를 우선 탐색한다.)"},
            {'no': 2, 'points': 8, 'question': "이 그래프를 노드(a)에서 출발하여 너비 우선 탐색(Breadth First Search) 방법으로 탐색할 경우, 방문 노드 순서와 방문에 사용된 간선으로 구성되는 신장트리(BFS Spanning Tree)를 작성하고, 간선 비용의 합을 구하시오. (단, 간선 비용이 적은 노드를 우선 탐색한다.)"},
            {'no': 3, 'points': 4, 'question': "이 그래프에 대한 비용 인접 행렬(Cost Adjacency Matrix)을 작성하시오."},
        ],
    },
    ('57회', 3): {
        'points': 30,
        'passage': "빠른 탐색을 하기 위한 다원 탐색 트리(m-way Search Tree)에는 B-트리와 B⁺-트리가 존재한다. 이 중 B-트리에 관한 다음 물음에 답하시오.",
        'subquestions': [
            {'no': 1, 'points': 6, 'question': "차수가 m인 B-트리의 특성 중 3가지를 설명하시오."},
            {'no': 2, 'points': 16, 'question': "다음과 같은 데이터들이 순서대로 입력될 때, 차수가 3인 B-트리를 구성하는 과정을 각 데이터별로 나타내시오.\n  데이터 삽입 순서: 12, 3, 9, 5, 10, 15, 14, 7"},
            {'no': 3, 'points': 8, 'question': "문항(2)에서 구축한 B-트리에서 다음 데이터들이 순서대로 삭제될 때, 각 데이터 삭제 후 B-트리의 구조를 데이터별로 나타내시오.\n  데이터 삭제 순서: 10, 7"},
        ],
    },
    ('57회', 4): {
        'points': 20,
        'passage': "컴파일러는 스택을 이용하여 프로그래머가 작성한 중위표기(Infix Notation) 수식을 후위표기(Postfix Notation) 수식으로 변환하여 계산을 수행한다. 다음 물음에 답하시오. (단, 스택은 오른쪽으로 커지고, +, -, *, /는 산술연산자이고 eos는 문자열의 끝이다.)",
        'subquestions': [
            {'no': 1, 'points': 10, 'question': "다음 표는 중위표기 수식  a/(b-c*d)*e+f  를 후위표기 수식으로 변환하는 과정을 보여주고 있다. 토큰(연산자 또는 피연산자) 일부를 처리한 결과를 참고하여 나머지 토큰들을 처리할 때 스택과 출력결과를 나타내시오.\n  (이미 처리된 부분: 토큰 a → 출력 a / 토큰 / → 스택 [/] / 토큰 ( → 스택 [/, (], 출력 a)"},
            {'no': 2, 'points': 6, 'question': "후위표기 수식  abc+d**e/  의 계산 과정에서 토큰 별로 처리할 때 스택을 나타내시오. (이미 처리된 부분: a → [a] / b → [a, b] / c → [a, b, c])"},
            {'no': 3, 'points': 4, 'question': "컴파일러가 중위표기 수식을 후위표기 수식으로 변환하여 계산하는 이유를 설명하시오."},
        ],
    },

    # 61회 문제-4: passage 안의 "물음 (2) ... 의 ①∼④, 물음 (3) ..." 표현이
    # parser 에 의해 잘못된 sub-question (4,2)[0점] 으로 잡힘. 전체 교체.
    ('61회', 4): {
        'points': 20,
        'passage': "아래는 이진탐색트리(Binary Search Tree)의 특정 키(노드)를 탐색, 삽입, 삭제하는 의사코드(pseudo code)이다.\n<주요 함수 및 조건>을 이용하여 다음의 물음 (1) 탐색(search)의 ①, ②, 물음 (2) 삽입(insert)의 ①∼④, 물음 (3) 삭제(remove)의 ①∼④를 완성하시오.\n\n<주요 함수 및 조건>\n- KEY(node) : node의 키 반환\n- LEFT(node) : node의 왼쪽 자식 노드 반환\n- RIGHT(node) : node의 오른쪽 자식 노드 반환\n- ISLEAF(node) : 단말노드 여부\n- DELETE() : 메모리 동적 해제\n- 비교는 '=', 치환·대입·연결은 '←' 로 표시한다.",
        'subquestions': [
            {'no': 1, 'points': 6, 'question': "탐색(search) 의사코드의 빈칸 ①, ②를 완성하시오.\nsearch(root, key)\n  if root = NULL then return NULL;\n  if key = KEY(root) then return root;\n  else if key < KEY(root) then\n    ①\n  else\n    ②"},
            {'no': 2, 'points': 6, 'question': "삽입(insert) 의사코드의 빈칸 ①∼④를 완성하시오.\ninsert(root, node)\n  if KEY(node) = KEY(root) then return;\n  else if KEY(node) < KEY(root) then\n    if LEFT(root) = NULL then ①\n    else ②\n  else\n    if RIGHT(root) = NULL then ③\n    else ④"},
            {'no': 3, 'points': 8, 'question': "삭제(remove) 의사코드의 빈칸 ①∼④를 완성하시오.\nremove(parent, node)\n  // case1: 삭제할 노드가 단말노드\n    ①  (부모의 해당 자식 포인터를 NULL)\n  // case2: 자식이 한쪽만 존재\n    ②  (부모를 child 로 직접 연결)\n  // case3: 자식이 둘 다 존재 — 두 가지 방안\n    ③ (오른쪽 부분트리의 최솟값(inorder successor) 으로 대체)\n    ④ (왼쪽 부분트리의 최댓값(inorder predecessor) 으로 대체)"},
        ],
    },
}

# (subject, exam, year, question_file, answer_file). Paths are relative to BASE_DIR.
# 데이터구조론 has no official answer files — answer_file is None for every exam,
# and Claude-authored answers are injected via ANSWER_OVERRIDES.
EXAMS = [
    ('데이터구조론', '45회', 2008, '제45회(2008)_데이터구조론.pdf', None),
    ('데이터구조론', '46회', 2009, '제46회(2009)_데이터구조론.pdf', None),
    ('데이터구조론', '47회', 2010, '제47회(2010)_데이터구조론.pdf', None),
    ('데이터구조론', '48회', 2011, '제48회(2011)_데이터구조론.pdf', None),
    ('데이터구조론', '49회', 2012, '제49회(2012)_데이터구조론.pdf', None),
    ('데이터구조론', '50회', 2013, '제50회(2013)_데이터구조론.pdf', None),
    ('데이터구조론', '51회', 2014, '제51회(2014)_데이터구조론.pdf', None),
    ('데이터구조론', '52회', 2015, '제52회(2015)_데이터구조론.pdf', None),
    ('데이터구조론', '53회', 2016, '제53회(2016)_데이터구조론.pdf', None),
    ('데이터구조론', '54회', 2017, '제54회(2017)_데이터구조론.pdf', None),
    ('데이터구조론', '55회', 2018, '제55회(2018)_데이터구조론.pdf', None),
    ('데이터구조론', '56회', 2019, '제56회(2019)_데이터구조론.pdf', None),
    ('데이터구조론', '57회', 2020, '제57회(2020)_데이터구조론.pdf', None),
    ('데이터구조론', '58회', 2021, '제58회(2021)_데이터구조론.pdf', None),
    ('데이터구조론', '59회', 2022, '제59회(2022)_데이터구조론.pdf', None),
    ('데이터구조론', '60회', 2023, '제60회(2023)_데이터구조론.pdf', None),
    ('데이터구조론', '61회', 2024, '제61회(2024)_데이터구조론.pdf', None),
    ('데이터구조론', '62회', 2025, '제62회(2025)_데이터구조론.pdf', None),
]

def extract_docx_text(filepath):
    import zipfile
    from xml.etree import ElementTree as ET
    NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    with zipfile.ZipFile(filepath) as z:
        xml = z.read('word/document.xml').decode('utf-8')
    root = ET.fromstring(xml)
    parts = []
    for para in root.iter(NS + 'p'):
        line = ''.join(t.text or '' for t in para.iter(NS + 't'))
        parts.append(line)
    return '\n'.join(parts)

def extract_pdf_text(filepath, layout=False):
    if filepath.endswith('.docx'):
        return extract_docx_text(filepath)

    # If a sibling .ocr.txt exists, prefer it (PDFs whose embedded fonts
    # don't extract via pdftotext but were OCR'd via macOS Vision API)
    base = os.path.basename(filepath)
    # Strip [N] disambiguation suffix from the OCR cache filename
    cache_base = re.sub(r'\[\d+\]\.pdf$', '.pdf', base)
    cache_path = os.path.join(os.path.dirname(filepath),
                              cache_base.replace('.pdf', '.ocr.txt'))
    if os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            text = f.read()
        # OCR consistently misreads 乙 as the Latin letter Z; restore it
        # only when followed by a Hangul josa (safe — real Latin Z won't appear
        # immediately before Korean characters in a question stem).
        text = re.sub(r'Z(?=[가-힣])', '乙', text)
        return text

    cmd = ['pdftotext']
    if layout:
        cmd.append('-layout')
    cmd += [filepath, '-']
    result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        print(f"ERROR extracting {filepath}: {result.stderr}", file=sys.stderr)
    return result.stdout

def clean_text(text, normalize_lines=False):
    # Normalize form feeds (PDF page breaks) to newlines
    text = text.replace('\x0c', '\n')
    # When using -layout mode, normalize each line (strip + collapse internal spaces)
    if normalize_lines:
        lines = []
        for line in text.split('\n'):
            stripped = line.strip()
            # Collapse multiple spaces within a line to single space
            stripped = re.sub(r' {2,}', ' ', stripped)
            lines.append(stripped)
        text = '\n'.join(lines)
    # Normalize problem-header variants to the canonical "【 문제-N 】" form:
    #   "[ 문제-1 ]" / "[ 문제-1 )" / "[문제 - 1]"  (OCR / docx)
    #   "〈 문제-1 〉"                              (특허법 docx)
    text = re.sub(r'\[\s*문제\s*-\s*(\d+)\s*[\])]', r'【 문제-\1 】', text)
    text = re.sub(r'[〈<]\s*문제\s*-\s*(\d+)\s*[〉>]', r'【 문제-\1 】', text)
    # Normalize spacing in points notation: "(10점 )" → "(10점)"
    text = re.sub(r'\(\s*(\d+)\s*점\s*\)', r'(\1점)', text)
    # Remove page markers (question PDFs) — covers 민사소송법, 특허법, 데이터구조론
    text = re.sub(r'\d{4}년 제\d+회 변리사 2차 - (?:민사소송법|특허법|데이터구조론) - ?\d교시 \(\s*\d+\s*-\s*\d+\s*\)', '', text)
    # Cover-page boilerplate for older 데이터구조론 PDFs
    text = re.sub(r'\d{4}년도?\s*제\d+회\s*변리사\s*(?:제\s*)?2차\s*(?:국가자격)?시험\s*문제지', '', text)
    text = re.sub(r'교\s*시\s*시험과목\s*시험시간', '', text)
    text = re.sub(r'수험번호\s+성\s*명', '', text)
    text = re.sub(r'2교시\s+데이터구조론\s+120분', '', text)
    # 옛 데이터구조론 PDF (45~50회) 는 「【 A-N 】」「【 B-N 】」 형식 헤더를 쓰며
    # OCR을 거치면 다양한 변형이 생긴다. 실제 관찰된 패턴:
    #   【 A-1 】 (text PDF, 47/48/50회)
    #   [ A-1 ]   [ A11 ]    [ A1I ]    [ A-2 1     (OCR: 45/46/49회)
    #   [ B-1 ]   [ B11 ]    [ B1l ]    [ B-21
    #   [ 8-1 1   (49회: B 가 숫자 8 로 오인식)
    # 또한 점수 표기 (30점)이 같은 줄 또는 다음 줄에 위치할 수 있다.
    # A 그룹과 B 그룹이 각각 1번부터 시작하므로 등장 순서대로 1,2,3,4 번호로 재부여.
    _ab_counter = [0]
    def _renumber_ab(m):
        _ab_counter[0] += 1
        return f'【 문제-{_ab_counter[0]} 】({m.group(1)}점)'
    text = re.sub(
        r'[\[【]\s*[AB8][\s\-－0-9IilL\]】\)1]{0,6}\s*\n?\s*\(\s*(\d+)\s*점\s*\)',
        _renumber_ab,
        text,
    )
    # 53회 (and similar) PDFs: "(\n1)" → "(1)", "(\n     30점)" → "(30점)"
    text = re.sub(r'\(\s*\n\s*(\d+)\s*\)', r'(\1)', text)
    text = re.sub(r'\(\s*\n\s*(\d+\s*점)\s*\)', r'(\1)', text)
    # Remove answer file headers
    text = re.sub(r'윤곽 민사소송법 기출문제 \d+회', '', text)
    # Remove page number lines (e.g. "1쪽", "12쪽")
    text = re.sub(r'^\s*\d+쪽\s*$', '', text, flags=re.MULTILINE)
    # Remove single/double Hangul character lines (decorative sidebar chars like 단,공,력,인,업,산,국,한)
    text = re.sub(r'^\s*[가-힣]{1,2}\s*$', '', text, flags=re.MULTILINE)
    # Collapse 3+ blank lines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def parse_questions(text, exam_name, year, normalize_lines=False, subject='민사소송법'):
    text = clean_text(text, normalize_lines=normalize_lines)

    # Split by problem header: 【 문제-N 】 (Ypoints) — allow optional space
    # before the points parenthesis (62회 has "【 문제-1 】(30점)" with no space).
    parts = re.split(r'【\s*문제-(\d+)\s*】\s*\(\s*(\d+)\s*점\s*\)', text)
    # parts[0] = text before first problem (discard)
    # then groups of 3: [number, points, content]

    problems = []
    for i in range(1, len(parts), 3):
        prob_no = int(parts[i])
        prob_points = int(parts[i + 1])
        prob_body = parts[i + 2].strip()

        # Separate passage from sub-questions
        # Sub-questions start with (N) at the beginning of a line.
        # 민사소송법 uses "(1) 丙이…" (space after), 데이터구조론 uses "(1)다음의…" (no space).
        sq_split = re.split(r'\n(?=\(\d\)\s*)', prob_body)

        passage_raw = sq_split[0]
        # Strip "(다음 각 물음/설문은 독립적임/이다.)" / "(다음 각 물음은 독립적이다.)" etc.
        passage = re.sub(
            r'\(\s*다음 각 (?:물음|설문)(?:은)?\s*독립적(?:임|이다\.?)\s*\)\s*$',
            '', passage_raw).strip()
        # Also handle version without the separator (passage just ends before (1))
        passage = clean_passage(passage)

        subquestions = []
        for sq_part in sq_split[1:]:
            m = re.match(r'\((\d)\)\s*(.+)', sq_part, re.DOTALL)
            if not m:
                continue
            sq_no = int(m.group(1))
            sq_text = m.group(2).strip()

            # Extract points — check end first, then anywhere in text
            pts_m = re.search(r'\((\d+)점\)\s*$', sq_text)
            if not pts_m:
                pts_m = re.search(r'\((\d+)점\)', sq_text)
            sq_points = int(pts_m.group(1)) if pts_m else 0
            # Remove ALL occurrences of the points notation
            sq_text = re.sub(r'\s*\(\d+점\)', '', sq_text).strip()

            # Normalize whitespace within text
            sq_text = normalize_whitespace(sq_text)

            subquestions.append({
                'no': sq_no,
                'points': sq_points,
                'question': sq_text,
                'answer': ''
            })

        problems.append({
            'subject': subject,
            'exam': exam_name,
            'year': year,
            'problemNo': prob_no,
            'points': prob_points,
            'passage': normalize_whitespace(passage),
            'subquestions': subquestions
        })

    return problems

def clean_passage(text):
    # Remove any trailing sub-question-like lines that shouldn't be in passage
    # (shouldn't happen after splitting, but just in case)
    return text.strip()

def normalize_whitespace(text):
    # Collapse multiple blank lines to one
    text = re.sub(r'\n{2,}', '\n', text)
    # Remove trailing spaces on each line
    lines = [line.rstrip() for line in text.split('\n')]
    return '\n'.join(lines).strip()

def parse_answers(text, exam_name):
    text = clean_text(text)

    # Split by problem header: [문제-N] or 【 문제-N 】 (latter from normalization)
    parts = re.split(r'(?:\[문제-|【\s*문제-)(\d+)(?:\]|\s*】)', text)
    # parts[0] = before first (discard)
    # then groups of 2: [number, content]

    answer_map = {}  # key: (prob_no, sq_no) -> answer text

    for i in range(1, len(parts), 2):
        prob_no = int(parts[i])
        prob_body = parts[i + 1].strip()

        # Split by roman-numeral sub-question marker. Two flavors:
        #   Unicode roman:    "Ⅰ. 설문(1)", "Ⅱ. 설문(2)"
        #   Latin letters:    "I. 설문(1)", "II. 설문(2)" (62회 docx)
        # Anchor at line start to avoid stray "I." in body text.
        sq_parts = re.split(
            r'(?:^|\n)\s*(?:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨ]|I{1,3}|IV|V|VI{0,3}|IX|X)\s*\.\s*설문\s*\(\s*(\d+)\s*\)',
            prob_body)
        # sq_parts[0] = before first (discard)
        # then groups of 2: [number, content]

        for j in range(1, len(sq_parts), 2):
            sq_no = int(sq_parts[j])
            sq_answer = sq_parts[j + 1].strip()
            sq_answer = normalize_whitespace(sq_answer)
            key = (prob_no, sq_no)
            if key in answer_map:
                # Same sub-question split into multiple roman-numeral sections
                # (e.g. "I. 설문(1) - 1)" + "II. 설문(1) - 2)") — concatenate.
                answer_map[key] = answer_map[key] + '\n\n' + sq_answer
            else:
                answer_map[key] = sq_answer

    return answer_map

def main():
    all_problems = []

    # Preserve hand-curated `categories` and `hints` (LLM-style data) from
    # any prior data.json so re-running the parser doesn't wipe them.
    out_path = os.path.join(BASE_DIR, 'data.json')
    existing_categories = {}
    existing_hints = {}
    if os.path.exists(out_path):
        try:
            with open(out_path, 'r', encoding='utf-8') as f:
                existing = json.load(f)
            for prob in existing:
                subj = prob.get('subject', '민사소송법')
                for sq in prob.get('subquestions', []):
                    key = (subj, prob['exam'], prob['problemNo'], sq['no'])
                    if 'categories' in sq:
                        existing_categories[key] = sq['categories']
                    if 'hints' in sq:
                        existing_hints[key] = sq['hints']
        except Exception as e:
            print(f"  WARN: couldn't load existing curated data: {e}", file=sys.stderr)

    for subject, exam_name, year, q_file, a_file in EXAMS:
        q_path = os.path.join(BASE_DIR, q_file)

        print(f"Processing {subject} {exam_name}...", file=sys.stderr)
        q_text = extract_pdf_text(q_path, layout=True)
        if a_file:
            a_path = os.path.join(BASE_DIR, a_file)
            a_text = extract_pdf_text(a_path, layout=False)
        else:
            a_text = ''

        problems = parse_questions(q_text, exam_name, year, normalize_lines=True, subject=subject)
        answers = parse_answers(a_text, exam_name) if a_text else {}

        # Apply PROBLEM_OVERRIDES — replace entire problem when source is unparseable
        prob_override_nos = {pno for (ex, pno) in PROBLEM_OVERRIDES if ex == exam_name}
        if prob_override_nos:
            existing_nos = {p['problemNo'] for p in problems}
            for pno in sorted(prob_override_nos - existing_nos):
                ov = PROBLEM_OVERRIDES[(exam_name, pno)]
                problems.append({
                    'subject': subject,
                    'exam': exam_name,
                    'year': year,
                    'problemNo': pno,
                    'points': ov.get('points', 0),
                    'passage': ov.get('passage', ''),
                    'subquestions': [
                        {'no': sq['no'], 'points': sq.get('points', 0),
                         'question': sq['question'], 'answer': ''}
                        for sq in ov.get('subquestions', [])
                    ],
                })
            for prob in problems:
                if (exam_name, prob['problemNo']) in PROBLEM_OVERRIDES:
                    ov = PROBLEM_OVERRIDES[(exam_name, prob['problemNo'])]
                    if 'points' in ov:
                        prob['points'] = ov['points']
                    if 'passage' in ov:
                        prob['passage'] = ov['passage']
                    if 'subquestions' in ov:
                        prob['subquestions'] = [
                            {'no': sq['no'], 'points': sq.get('points', 0),
                             'question': sq['question'], 'answer': ''}
                            for sq in ov['subquestions']
                        ]
            problems.sort(key=lambda p: p['problemNo'])

        # Merge answers + restore preserved category data + apply overrides
        for prob in problems:
            pass_key = (exam_name, prob['problemNo'])
            if pass_key in PASSAGE_OVERRIDES:
                prob['passage'] = PASSAGE_OVERRIDES[pass_key]
            for sq in prob['subquestions']:
                key = (prob['problemNo'], sq['no'])
                if key in answers:
                    sq['answer'] = answers[key]
                ov_key = (exam_name, prob['problemNo'], sq['no'])
                if ov_key in ANSWER_OVERRIDES:
                    sq['answer'] = ANSWER_OVERRIDES[ov_key]
                if ov_key in QUESTION_OVERRIDES:
                    sq['question'] = QUESTION_OVERRIDES[ov_key]
                cat_key = (subject, exam_name, prob['problemNo'], sq['no'])
                if cat_key in existing_categories:
                    sq['categories'] = existing_categories[cat_key]
                if cat_key in existing_hints:
                    sq['hints'] = existing_hints[cat_key]
                # categories.py / hints.py 의 큐레이션 데이터가 있으면 덮어쓴다
                curated_key = f"{exam_name}:{prob['problemNo']}:{sq['no']}"
                if curated_key in CURATED_CATS:
                    sq['categories'] = CURATED_CATS[curated_key]
                if curated_key in CURATED_HINTS:
                    sq['hints'] = CURATED_HINTS[curated_key]

        all_problems.extend(problems)
        total_sq = sum(len(p['subquestions']) for p in problems)
        print(f"  {len(problems)} problems, {total_sq} sub-questions", file=sys.stderr)

    # Save data.json
    out_path = os.path.join(BASE_DIR, 'data.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(all_problems, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {out_path}", file=sys.stderr)

    # Embed into index.html as a JS variable
    html_path = os.path.join(BASE_DIR, 'index.html')
    if os.path.exists(html_path):
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()

        json_str = json.dumps(all_problems, ensure_ascii=False)
        new_data_block = f'const EXAM_DATA = {json_str};'

        # Replace the EXAM_DATA declaration line. EXAM_DATA is emitted as a single
        # line, so match `const EXAM_DATA = [` through the end of that line
        # (greedy up to first newline) — non-greedy `.*?` over the whole HTML can
        # truncate the JSON at the first `];` inside string values when the file
        # is re-embedded.
        if re.search(r'const EXAM_DATA = \[', html, re.DOTALL):
            html_new = re.sub(
                r'const EXAM_DATA = \[[^\n]*\];',
                lambda m: new_data_block,
                html,
            )
        else:
            html_new = html.replace('/* DATA_PLACEHOLDER */', new_data_block, 1)

        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_new)
        print(f"Embedded data into {html_path}", file=sys.stderr)
    else:
        print("index.html not found — skipping embed", file=sys.stderr)

    total = sum(len(p['subquestions']) for p in all_problems)
    print(f"\nDone: {len(all_problems)} problems, {total} sub-questions total", file=sys.stderr)

if __name__ == '__main__':
    main()
