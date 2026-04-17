# userdic-py

`userdic-ng`（Ruby 実装）を Python に移植した、日本語 IME ユーザー辞書変換ツールです。

## 必要環境

- Python 3.9 以上

## インストール

### 1) Python パッケージとして使う（推奨）

```bash
pip install .
```

インストール後は `userdic-py` コマンドが使えます。

### 2) `make install` でローカル配置する

`/usr/local/bin` にコマンド、`/usr/local/lib/userdic-py` にライブラリを配置します。

```bash
make install
```

別のインストール先を使う場合:

```bash
make install PREFIX=/path/to/prefix
```

削除する場合:

```bash
make uninstall
```

## 使い方

```bash
userdic-py [--input-encoding ENCODING] [--output-encoding ENCODING] <from> <to> < input > output
```

リポジトリを直接実行する場合は、従来どおり `./userdic.py` でも動作します。

```bash
./userdic.py [--input-encoding ENCODING] [--output-encoding ENCODING] <from> <to> < input > output
```

`<from>` / `<to>` には次を指定できます。

- `mozc`
- `google`
- `anthy`
- `canna`
- `atok`
- `msime`
- `wnn`
- `apple`
- `generic`

`--input-encoding` / `--output-encoding` には Python の codec 名を指定します。
例: `utf-8`, `utf-16`, `utf-16-le`, `cp932`, `euc_jp`

## 使用例

```bash
userdic-py generic mozc < generic.txt > mozc.txt
```

```bash
userdic-py --input-encoding cp932 --output-encoding utf-8 msime generic < msime.txt > generic.txt
```

## 仕様メモ

- 入力エンコーディング未指定時は `utf-16` / `cp932` / `euc_jp` / `utf-8` の順で読み取りを試行します。
- 出力エンコーディング未指定時の既定値:
  - `msime`, `atok`: `utf-16`
  - `wnn`, `canna`: `euc_jp`
  - その他テキスト形式: `utf-8`
- `apple` は plist(XML) 形式を読み書きします。
- `apple` 入出力では `--input-encoding` / `--output-encoding` は利用できません。
