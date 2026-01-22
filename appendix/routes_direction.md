## 画面遷移

```mermaid
flowchart TD

%% ============================
%% 画面ノード（ここを書き換える）
%% ============================
list_event[事象一覧]
list_info[列車一覧]
detail_info[列車詳細]
new_event[事象登録]
new_info[列車登録]
edit_event[事象編集]
edit_info[列車編集]
view_sid[駅掲示]

%% ============================
%% 遷移（ここに矢印を追加していく）
%% ============================

%% ホーム（事象一覧）からの遷移
list_event -->|列車一覧へ| list_info
list_event -->|事象登録へ| new_event
list_event -->|事象編集へ| edit_event
list_event -->|駅ごとの掲示へ| view_sid

%% 列車一覧からの遷移
list_info -->|列車編集へ| edit_info
list_info -->|アイテム選択| detail_info
list_info -->|列車登録へ| new_info
list_info -->|戻る| list_event

%% 列車登録/編集からの遷移
new_info -->|追加/戻る| list_info
edit_info -->|編集/戻る| list_info
detail_info -->|戻る| list_info

%% 事象登録/編集からの遷移
new_event -->|追加/戻る| list_event
edit_event -->|編集/戻る| list_event

%% 駅ごとの掲示画面からの遷移
view_sid -->|戻る| list_event
