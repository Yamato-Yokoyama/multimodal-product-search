"""
src/hello_langgraph.py

LangGraph の最小サンプル(Issue #23)。
State → Node → Edge → compile → invoke の一連の流れを、実際のRAGロジックを
含まない単純な文字列変換で確認する。

詰まったら聞く。ここでは「何をすべきか」だけを Input/Output/なぜ で示す。
中身は自分で書く。書き方のパターンは docs/notes/langgraph-101-tutorial/01_hello_world.md
を見ながら進める(なぜLangGraphが要るかの背景は docs/notes/langgraph-101-tutorial/00_concepts.md)。

Called by: なし(単体で実行して確認する用、chainlit_hello.py と同じ位置づけ)
Depends on: langgraph
"""
from typing import TypedDict
from langgraph.graph import StateGraph, END


# ============================================================
# 見本(参考実装): 下のTODOとは別の題材(数値を+1してから2倍にするだけ)で
# State → Node → Edge → compile → invoke を一通りやっている。
# これを真似て、下の shout / add_exclamation / build_graph の TODO を埋める。
# ============================================================

class _ExampleState(TypedDict):
    # Stateはただのdict(TypedDictで型だけ決めている)。
    # キー名は自由、ここでは数値を1個持たせるだけ。
    number: int


def _add_one(state: _ExampleState) -> dict:
    # 1. state からキーで値を取り出す
    current = state["number"]
    # 2. 変換する(ここが Node の本体、今回はただの足し算)
    updated = current + 1
    # 3. state全部ではなく、更新したいキーだけを dict にして返す
    return {"number": updated}


def _double(state: _ExampleState) -> dict:
    current = state["number"]
    updated = current * 2
    return {"number": updated}


def _build_example_graph():
    # 1. StateGraph(型)でグラフの器を作る
    graph_builder = StateGraph(_ExampleState)
    # 2. ノードを登録する("名前", 関数) のペアをいくつでも足せる
    graph_builder.add_node("add_one", _add_one)
    graph_builder.add_node("double", _double)
    # 3. どのノードから始めるか指定する
    graph_builder.set_entry_point("add_one")
    # 4. ノード同士をedgeで繋ぐ(A→B の順番を決める)
    graph_builder.add_edge("add_one", "double")
    # 5. 最後のノードは組み込みの END に繋いで、グラフの終わりを明示する
    graph_builder.add_edge("double", END)
    # 6. compile() して初めて実行可能になる
    return graph_builder.compile()


def _run_example():
    """見本を実際に動かして確認する用(コメントアウトを外して単体で試せる)。

    5 を入れると、add_one で 6、double で 12 になって返るはず。
    """
    example_graph = _build_example_graph()

    print("--- グラフの構造(draw_ascii) ---")
    print(example_graph.get_graph().draw_ascii())

    result = example_graph.invoke({"number": 5})
    print(f"見本の結果: {result}")  # => {'number': 12}


# ============================================================
# ここから下が本題(Issue #23 の実際のTODO)。上の見本と同じ手順を
# 「数値の+1/2倍」ではなく「文字列を大文字にする/!!!を足す」に置き換えるだけ。
# ============================================================

# TODO 1: State を定義する
#   ヒント: TypedDict で「ノード間を流れるデータの形」を決める。
#   今回は文字列1個(キー名は自由、例: "text")を持たせるだけでいい。
class HelloState(TypedDict):
    text: str


def shout(state: HelloState) -> dict:
    """入力文字列を大文字にするノード。

    Input:
        state: HelloState。文字列のキー(例: "text")に元の文字列が入っている

    Output:
        dict。更新したいキーだけを返す(例: {"text": "大文字にした文字列"})。
        LangGraph の Node は「state 全部」ではなく「更新分の dict」だけ返せばいい

    なぜ:
        LangGraph の最小の Node は「state を受け取り、更新分の dict を返す関数」
        というだけのシンプルな契約。まずこの形に慣れる。
    """
    # TODO 2: state から文字列を取り出し、大文字にして dict で返す
    shouted_text = state["text"].upper()
    return {"text": shouted_text}


def add_exclamation(state: HelloState) -> dict:
    """文字列の末尾に "!!!" を足すノード。

    Input:
        state: HelloState

    Output:
        dict。更新した文字列

    なぜ:
        2つ目の Node を用意することで、Node 同士が Edge で繋がり、
        順番に実行される様子を確認できる(1個だけだとグラフである意味がない)。
    """
    # TODO 3: state から文字列を取り出し、末尾に "!!!" を足して dict で返す
    exlm_text = state["text"] + "!!!"
    return {"text": exlm_text}


def build_graph():
    """StateGraph を組み立てて compile する。

    Output:
        compile 済みの graph(.invoke() で実行できるオブジェクト)

    なぜ:
        Node を追加し、Edge で繋ぎ、開始点・終了点を指定して初めて
        実行可能なグラフになる。この組み立て手順自体が LangGraph の基本操作。

    ヒント(使うメソッド):
        - StateGraph(HelloState) でグラフを作る
        - .add_node("名前", 関数) でノードを登録(shout, add_exclamation の2つ)
        - .set_entry_point("名前") で最初に実行するノードを指定
        - .add_edge("ノードA", "ノードB") でA→Bの繋がりを作る
        - 最後のノードは .add_edge("ノード名", END) で終了点に繋ぐ
        - .compile() で実行可能な形にして return する
    """
    # TODO 4: 上のヒント通りに組み立てて、compile したものを返す
    graph_builder = StateGraph(HelloState)
    graph_builder.add_node("shout", shout)
    graph_builder.add_node("exclamation", add_exclamation)
    graph_builder.set_entry_point("shout")
    graph_builder.add_edge("shout", "exclamation")
    graph_builder.add_edge("exclamation", END)
    graph =  graph_builder.compile()
    return graph


if __name__ == "__main__":
    # 見本を試したい時はこちらを実行(コメントアウトを外す)
    #_run_example()

    graph = build_graph()
    # TODO 5: graph.invoke({...}) を呼んで、結果を print する
    #   入力は {"text": "hello langgraph"} のような形(Stateのキー名に合わせる)
    #   見本の _run_example() の書き方を真似ればいい
    print("=== LangGraph の結果 ===")
    input_state = {"text": "hello langgraph"}
    result = graph.invoke(input_state)
    print(f"結果: {result}")  # => {'text': 'HELLO LANGGRAPH!!!'}
    print("--- グラフの構造(draw_ascii) ---")
    print(graph.get_graph().draw_ascii())