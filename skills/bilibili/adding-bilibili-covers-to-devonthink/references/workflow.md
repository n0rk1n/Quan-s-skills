# Bilibili Bookmark 封面整理流程

## 1. 解析与预检

1. 从 `x-devonthink-item://<UUID>` 仅提取 UUID，不打开或猜测其他记录。
2. 运行脚本的 `--plan-only` 模式。
3. 要求根 UUID 指向 group，且直属子组中分别只有一个 `01 - 无封面图` 和一个 `02 - 有封面图`。
4. 检查计划中的 `selected_count` 不超过 50；计划为空时报告没有具有真实封面 URL 的可处理项并停止。

## 2. 固定单批清单

按 DEVONthink 返回顺序扫描源组 bookmark，只选择备注中具有真实 HTTP(S) URL 的前 50 个。兼容以下标签：

- `页面可见封面地址：`
- `可见封面 URL：`
- `封面 URL：`

值为 `insufficient metadata` 的记录不进入清单。清单一旦固定，下载失败、无效图片或导入失败都不从第 51 项递补。

## 3. 下载与图片验证

每个清单项以 bookmark UUID 建立独立临时目录，避免重复标题相互覆盖。临时文件的基本名称取 bookmark 的 `filename` 去除 `.webloc`；这只解决文件系统字符限制，不改变 DEVONthink 显示名称。

下载要求：

1. 使用 `curl --fail --location`，设置连接和总超时并重试瞬时失败。
2. `i0.hdslb.com` 发生 TLS 问题时，由随附脚本把主机固定替换为 `i1.hdslb.com`，保留完全相同的资源路径。代理不要手工重写或缩写该主机名。
3. 使用 `file --mime-type` 接受 WebP、JPEG、PNG 或 GIF；其他响应视为失败。
4. 下载失败项保留在源组。

## 4. 导入后再移动

对每个验证成功项保持如下顺序：

1. 以 UUID 查询目标组中是否已有备注为 `封面来源书签 UUID：<UUID>` 的 picture；存在时复用，避免重试产生重复封面。
2. 若不存在，则把图片导入 `02 - 有封面图` 并写入该来源 UUID 备注。
3. 设置 `picture.name = bookmark.name`。名称必须逐字相等；UUID 不得进入显示名称。
4. 仅在 picture 已存在于目标组后，按 bookmark UUID 从源组移动该 bookmark。

若 picture 已导入但 bookmark 移动失败，报告 `stage=move` 并停止自动重试；下次运行会用来源 UUID 复用已导入 picture。

## 5. 核验与报告

脚本输出 JSON。完成声明至少核对：

- `batch_limit = 50`
- `selected_count <= 50`
- `moved_count + failed_count = selected_count`
- 失败 bookmark 仍位于 `01 - 无封面图`
- 成功 bookmark 与同名 picture 均位于 `02 - 有封面图`
- `destination_bookmarks` 与 `destination_pictures` 的差异没有因本批扩大

报告本批选择数、成功移动数、失败数、失败阶段和源组剩余数。结束本次调用，不预取、不观察、不处理下一批。

## 常见规避理由

| 理由 | 正确处理 |
| --- | --- |
| “加 UUID 后缀才能避免重名” | UUID 解决身份；DEVONthink 显示名称仍与 bookmark 完全一致。 |
| “失败后补几个，最终仍是 50 个成功项” | 50 是固定清单上限，不是成功配额；失败不递补。 |
| “脚本很快，可以自动循环到全部完成” | 单次调用在本批输出后结束；下一批等待新的用户调用。 |
| “镜像地址很简单，可以手工改写” | 使用脚本中固定的 `i1.hdslb.com` 替换，避免主机名拼写漂移。 |
