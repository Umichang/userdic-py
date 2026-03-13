# userdic-py

`userdic-ng` の Ruby 実装を Python に移植した辞書変換ツールです。

## インストール

`/usr/local/bin` にコマンドをインストールするには、次を実行します（`userdic_py` 本体も `/usr/local/lib/userdic-py` に配置します）。

```bash
make install
```

別のインストール先を使う場合は `PREFIX` を指定できます。

```bash
make install PREFIX=/path/to/prefix
```

削除する場合:

```bash
make uninstall
```

## 使い方

```bash
./userdic.py <from> <to> < input > output
```

```bash
./userdic.py [--input-encoding ENCODING] [--output-encoding ENCODING] <from> <to> < input > output
```

`from` / `to` は次を指定できます。

- `mozc`
- `google`
- `anthy`
- `canna`
- `atok`
- `msime`
- `wnn`
- `apple`
- `generic`

## 例

```bash
./userdic.py generic mozc < generic.txt > mozc.txt
```

```bash
./userdic.py --input-encoding cp932 --output-encoding utf-8 msime apple < msime.txt > apple.plist
```

`--input-encoding` と `--output-encoding` には Python の codec 名を指定します。
代表例: `utf-8`, `utf-16`, `utf-16-le`, `cp932`, `euc_jp`

## 実装方針

- 品詞変換表は `userdic_py/hinshi` を読み込みます（`make install` 時にも同梱されます）。
- 入力 encoding 未指定時は `utf-16`, `cp932`, `euc_jp`, `utf-8` の順でデコードを試行します。
- 出力 encoding 未指定時は辞書形式ごとの既定値を使います。
  - `msime`, `atok`: `utf-16`
  - `wnn`, `canna`: `euc_jp`
  - その他テキスト形式: `utf-8`
- `apple` 形式は plist(XML) を読み書きします。
- `apple` 形式では `--input-encoding` / `--output-encoding` は使えません。
