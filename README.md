# Controller Shape Library

Autodesk Maya向けの **Controller Shape作成・管理ツール**です。

リギングで頻繁に使用するController Shapeを視覚的に選択して生成できるほか、
任意の文字からのController作成、Shapeの結合、カラー設定、位置合わせ、
ZERO / OFFSET Groupの作成など、Controller作成時に繰り返し発生する操作の手間を削減し、効率化を目指しました。

また、新規で作成したShapeはJSONライブラリへ登録でき、
Mayaシーンに依存せず別のリグ制作でも再利用できます。

単体ツールとして使用するだけでなく、
**他のリギングツールへController生成機能を組み込みやすい構成**
**ユーザーが拡張しやすい構成**
を意識して設計しています。

---

## Preview

![Controller Shape Library](images/main_ui.png)

<!-- 操作デモGIF -->
![Demo](images/demo.gif)

---

## Features

### Visual Shape Presets

Controller Shapeを一覧から視覚的に確認しながら選択できます。

Shape名だけから探すのではなく、
実際の形状を見ながら用途に合ったControllerを選択できるようにしました。

プリセットはカテゴリごとに整理しており、
必要なShapeを素早く探して生成できます。

![Shape Presets](images/shape_presets.png)

---

### Custom Shape Library

制作中に作成したController Shapeを、
ツール内のライブラリへプリセットとして登録できます。

登録したShapeはJSONで管理されるため、
現在開いているMayaシーンには依存しません。

一度登録しておけば別のシーンでも呼び出せるため、
プロジェクトをまたいでよく使用するControllerを再利用できます。

- Shapeの保存 / 上書き
- 保存済みShapeからControllerを作成
- 登録内容の更新
- 不要なShapeの削除

![Custom Shape Library](images/library.gif)

---

### Text Controller

任意の文字からControllerを作成できます。

英字だけでなく、

- 日本語
- 数字
- 記号

などにも対応しており、
入力した文字をController Shapeとして利用できます。

通常の操作用Controllerだけでなく、
リグ内のラベルや機能を視覚的に示すControllerなど、
用途に合わせたShapeを作成できます。

![Text Controller](images/text_controller.gif)

---

### Shape Combine

複数のShapeを結合し、
1つのControllerとしてまとめることができます。

プリセットをそのまま使用するだけでなく、
複数のShapeや文字を組み合わせることで、
リグの用途に合わせたControllerを作成できます。

![Shape Combine](images/shape_combine.gif)

---

### Controller Color

Controllerのカラーをツール上から設定できます。

既存のController Toolと同じカラー操作を搭載し、
Controller作成から色分けまで同じツール内で行えるようにしています。

![Controller Color](images/color.gif)

---

### Position & Rotation Snap

選択したControllerを対象オブジェクトへ位置合わせできます。

Controller作成後に手作業でTransformを合わせる工程を減らし、
リグ構築時のセットアップを素早く行えるようにしています。

![Snap](images/snap.gif)

---

### ZERO / OFFSET Group

選択したControllerと同じ位置に
ZERO Group / OFFSET Groupを作成できます。

Controller作成後に必要になりやすい階層作成まで
同じツール内で完結できるようにしています。

![ZERO OFFSET](images/zero_offset.gif)

ZERO Group / OFFSET Groupの命名設定も任意で変更可能です。

---

## JSON Based Library

ユーザーが登録したController ShapeはJSONで管理しています。

```text
Controller Shape Library
        │
        └── Shape Library
                │
                └── user_shapes.json

## JSON Based Library

ユーザーが登録したController ShapeはJSONで管理しています。

```text
Controller Shape Library
│
└── Shape Library
    │
    └── user_shapes.json
```

## License

This project is licensed under the MIT License.

Copyright (c) 2026 Yuzuki Midoshima