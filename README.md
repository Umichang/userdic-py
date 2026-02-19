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

## 実装方針

- 品詞変換表はリポジトリ直下の `hinshi` を読み込みます。
- 旧実装に合わせ、入力時は `utf-16`, `cp932`, `euc_jp`, `utf-8` の順でデコードを試行します。
- `apple` 形式は plist(XML) を読み書きします。
