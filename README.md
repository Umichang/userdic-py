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
- `dctx`
- `apple`
- `generic`

## 例

```bash
./userdic.py generic mozc < generic.txt > mozc.txt
```

## 実装方針

- 品詞変換表は `userdic_py/hinshi` を読み込みます（`make install` 時にも同梱されます）。
- 旧実装に合わせ、入力時は `utf-16`, `cp932`, `euc_jp`, `utf-8` の順でデコードを試行します（`msime` 入力時のみ `utf-16`, `utf-8`, `cp932`, `euc_jp` の順）。
- `apple` 形式は plist(XML) を読み書きします。
- `dctx` は Microsoft IME 追加辞書サービス向けの Office IME 2010 オープン拡張辞書(XML)として、UTF-16LE で入出力します。ルート要素は `<ns1:Dictionary xmlns:ns1="http://www.microsoft.com/ime/dctx" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">` です。
