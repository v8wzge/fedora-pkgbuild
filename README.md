# fedora-pkgbuild

面向 Fedora 的自动化 RPM 打包流水线（默认容器为 Fedora 45）。当前维护：

| 软件包 | 上游 | 跟踪目标 |
| --- | --- | --- |
| `kdesvn` | `invent.kde.org/sdk/kdesvn` | `master` 分支（Qt6/KF6） |
| `klassy` | `paulmcauley/klassy` | `6.8temp` 分支（Plasma 6.8 开发分支，Qt6） |
| `maple-font` | `subframe7536/maple-font` | 最新 release（**包含测试版**）的 `MapleMono-NF-unhinted.zip` |
| `rime-wanxiang-ibus` | `amzxyz/rime-wanxiang` | 标准版 Base + 基础词典，适配 IBus Rime |
| `rime-wanxiang-fcitx5` | `amzxyz/rime-wanxiang` | 标准版 Base + 基础词典，适配 Fcitx5 Rime |
| `fcitx5-mellow-themes` | `sanweiya/fcitx5-mellow-themes` | `main` 分支快照（圆角主题） |
| `clash-verge-rev` | `clash-verge-rev/clash-verge-rev` | 最新 release 的官方 x86_64 RPM（直接镜像） |

每 3 天检查一次上游。git 包比较分支 HEAD commit，release 包比较 tag + asset id + 更新时间；有变化才重新构建，否则跳过。**所有 RPM（二进制与 SRPM）都上传到统一的 GitHub Release `packages`，`gh-pages` 分支只保存 repodata 和状态文件**，repodata 中每个包的 `location href` 指向对应的 Release 资产 URL，从而绕开 git 仓库的容量限制。旧的构建脚本 `publish-repo.sh` 已移除。

## 仓库结构

```
.github/workflows/
  _build-git.yml              # 可复用：git 分支快照构建
  _build-release.yml          # 可复用：单个 Release 资源构建
  _build-release-multi.yml    # 可复用：一个包多个 Release 资源 / 多个 spec
  _mirror-release-rpm.yml     # 可复用：直接镜像上游现成 RPM
  build-kdesvn.yml            # 各软件包只保留一份薄配置
  build-klassy.yml
  build-maple-font.yml
  build-rime-wanxiang-ibus.yml
  build-rime-wanxiang-fcitx5.yml
  build-fcitx5-mellow-themes.yml
  build-clash-verge-rev.yml
scripts/                      # 通用构建/发布脚本
  publish_release.py          # 上传 RPM 到共享 Release
  publish-release-repo.sh     # 汇总资产、生成 repodata 并发布到 gh-pages
  find_release.py             # 按资源名查找最新 Release
  find_release_asset.py       # 按文件名模式查找上游现成 RPM
specs/                        # 符合 Fedora 打包规范的 spec 文件
extra/                        # 额外 Source 文件（许可证、中文翻译等）
repo/v8wzge-fedora.repo       # 供用户安装的 dnf 源定义
```

每个软件包有独立的 state 文件、独立的并发组和独立的工作流，互不干扰。

## 如何添加新软件

1. 在 `specs/` 添加 spec 文件；git 快照包需包含以下可被替换的行：

   ```
   %global commit 0000000000000000000000000000000000000000
   %global commitdate 19700101
   Version: ...
   Release: ...%{commitdate}git%{shortcommit}%{?dist}
   ```

2. 若是 git 包，在 `scripts/versions/` 添加一个打印版本号的脚本；若是 release 包，则不需要。
3. 在 `.github/workflows/` 添加一个薄工作流调用对应的 reusable workflow：

   ```yaml
   jobs:
     build:
       uses: ./.github/workflows/_build-git.yml
       with:
         package: mypkg
         git_url: https://github.com/owner/repo.git
         branch: main
         spec: specs/mypkg.spec
         version_script: scripts/versions/mypkg.sh
   ```

4. 推送后即可。首次构建没有 state 记录，会自动执行一次。

## 如何启用

- 仓库 Settings → Pages → Build and deployment：Source 选择 **Deploy from a branch**，`gh-pages` / `/ (root)`。
- Actions 需要 `contents: write` 权限（已在 reusable workflow 中声明）；若仓库默认设置为只读，请在 Settings → Actions → Workflow permissions 中改为 `Read and write`。
- 定时触发只在默认分支上的工作流生效。

## 客户端使用

```bash
sudo curl -o /etc/yum.repos.d/v8wzge-fedora.repo \
  https://raw.githubusercontent.com/v8wzge/fedora-pkgbuild/main/repo/v8wzge-fedora.repo
sudo dnf install kdesvn klassy maple-font \
  rime-wanxiang-ibus-base rime-wanxiang-ibus-dicts \
  fcitx5-mellow-themes clash-verge-rev
```

万象拼音还有一个 Fcitx5 变体：`rime-wanxiang-fcitx5-base` + `rime-wanxiang-fcitx5-dicts`。IBus 和 Fcitx5 两套包互斥，只装其中一套。

仓库中的 RPM 未签名，因此 `.repo` 使用 `gpgcheck=0`。dnf 从 `gh-pages` 读取 repodata，再按其中的地址从 GitHub Release 下载 RPM。

## 如何升级到 Fedora 46 / 47

构建系统版本通过 GitHub 仓库变量控制，**不需要改代码**：

1. 仓库 Settings → Secrets and variables → Actions → **Variables** → New repository variable
2. 名称填写 `FEDORA_VERSION`，值填写 `46` 或 `47`
3. 删除该变量即可回到默认的 `45`

切换后下一次定时检查会把 `state` 里记录的构建系统版本与当前值比较，发现不同就重新构建全部包，生成 `.fc46` / `.fc47` 的新 RPM 并发布到同一个仓库。旧版本的 RPM 会保留，方便跨版本共存。spec 中的 `%{?dist}` 会自动变成对应版本的 dist tag。

## 说明

- 构建环境默认为 Fedora 45 容器；可用 `FEDORA_VERSION` 变量切换为 46/47。
- **kdesvn 与 Fedora 官方包的区分**：官方提供 `0:2.1.0-18.fc45`，本仓库提供的是 master 分支快照。为避免 dnf 因 release 号（`18` > `0.1`）而选中官方包，本仓库的 kdesvn 使用 `Epoch: 1`，因此快照包永远优先。可用 `rpm -q --qf '%{EPOCH}:%{VERSION}-%{RELEASE}\n' kdesvn` 查看，`1:` 开头即为本仓库快照，`0:` 开头为官方包。klassy 与 maple-font 在 Fedora 官方仓库中不存在，无此问题。
- 所有包共享同一个 `gh-pages` 分支；工作流通过 `rpm-build` 并发组串行发布，避免推送冲突。若仍有并行写入，`scripts/publish-release-repo.sh` 会先 rebase 再推送。
- RPM 仓库地址：<https://v8wzge.github.io/fedora-pkgbuild/>；RPM 二进制统一托管在 Release `packages`。
- 万象拼音的 Base 包提供 schema/Lua/OpenCC 数据，词典包提供 `dicts/` 下的词库与语法模型；Base 包会依赖同变体的词典包。`librime-lua`、`librime-octagram` 均为 Fedora `librime` 的子包，已写入依赖。IBus 变体依赖 `ibus-rime`，Fcitx5 变体依赖 `fcitx5-rime`，两套包名互斥。
- `fcitx5-mellow-themes` 上游没有 tag/release，按 `main` 分支快照打包，版本取提交日期。
- `clash-verge-rev` 不重新编译，直接镜像上游发布的 x86_64 RPM，版权归上游所有。
- Maple Mono 采用 SIL OFL 1.1；`v8.0-beta.3` 等测试版会被正常打包，RPM 版本中的 `-` 会转换为 `~` 以保证版本比较正确。
- kdesvn 使用本仓库维护的完整简体中文翻译作为 `Source1`，替换上游未完成的 `po/zh_CN/kdesvn.po`。
