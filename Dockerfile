# Dockerfile
#
# YAMLでもPythonでもない、Docker専用のフォーマット。上から順に実行される
# 「このイメージをどう組み立てるか」の手順書。拡張子は付けず、ファイル名を
# そのまま"Dockerfile"にするのが決まり。
#
# 背景: docs/notes/docker-101-tutorial/01_why_and_what.md

# FROM: 土台にする既製のイメージを指定する。
# python:3.11-slim は「Python 3.11がインストール済みの、最小限のLinux」という
# 公式イメージ。手元の.venvと同じ3.11系に揃えている。
FROM python:3.11-slim

# WORKDIR: これ以降のコマンドを実行する場所(コンテナ内のディレクトリ)を指定。
# 無ければ作られる。以降の相対パスは全部ここが基準になる。
WORKDIR /app

# COPY <ホスト側> <コンテナ側>: ファイルをイメージの中にコピーする。
# requirements.txtだけ先にコピーするのは、Dockerのキャッシュ機構を使うため
# (依存関係が変わらない限り、次回ビルド時にpip installをやり直さずに済む)。
COPY requirements.txt .

# RUN: イメージを組み立てる時に1回だけ実行されるコマンド。
# --no-cache-dir は、pipのキャッシュを残さずイメージを軽量に保つためのオプション。
RUN pip install --no-cache-dir -r requirements.txt

# ここで初めてコード全体をコピーする(requirements.txtは上で既にコピー済みなので
# 二重にはならない、Dockerが自動で差分だけ扱う)。
COPY . .

# ENV: コンテナ内の環境変数を設定する。
# PYTHONPATHに/app(=WORKDIRそのもの)を足しておくことで、
# "from src.rag_pipeline import ..." のような、リポジトリルート基準の絶対importが
# Chainlitの実行方式(ファイル単体をロードする方式)からでも解決できるようにする。
# これが無いと "ModuleNotFoundError: No module named 'src'" になる
# (手元で `python -m src.graph_router` に -m が要ったのと同じ種類の問題)。
ENV PYTHONPATH=/app

# EXPOSE: このコンテナが何番ポートを使うつもりかを明示する(ドキュメント的な意味合い、
# 実際にポートを開放するのは docker run 側の -p オプション)。
# Chainlitのデフォルトポートは8000。
EXPOSE 8000

# CMD: コンテナが起動した時に実行されるコマンド(1つのDockerfileにつき基本1つ)。
# --host 0.0.0.0 が無いと、コンテナ内部からしかアクセスできなくなる
# (127.0.0.1だと「コンテナの外」であるホストPCのブラウザから繋げない)。
CMD ["chainlit", "run", "src/amazon/chainlit_app.py", "--host", "0.0.0.0", "--port", "8000"]
