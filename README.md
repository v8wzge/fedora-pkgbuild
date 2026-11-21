# fedora-pkgbuild

面向 Fedora 的自动化 RPM 打包流水线（默认容器为 Fedora 45）。当前维护：

| 软件包 | 上游 | 跟踪目标 |
| --- | --- | --- |
| `kdesvn` | `invent.kde.org/sdk/kdesvn` | `master` 分支（Qt6/KF6） |
| `klassy` | `paulmcauley/klassy` | `6.8temp` 分支（Plasma 6.8 开发分支，Qt6） |
| `maple-font` | `subframe7536/maple-font` | 最新 release（**包含测试版**）的 `MapleMono-NF-unhinted.zip` |

每 3 天检查一次上游。git 包比较分支 HEAD commit，release 包比较 tag + asset id + 更新时间；有变化才重新构建，否则跳过。构建产物（二进制 RPM 与 SRPM）发布到 `gh-pages` 分支上的 dnf 仓库。

## 国产软件官方下载地址索引

对微信、QQ、WPS 这类**只从官方渠道分发、不适合二次打包**的软件，本仓库另外维护一份"官方下载地址索引"。工作流每 3 天探测各厂商官方页面/配置，把最新版本与官方 RPM 直链写入索引并发布到 `https://v8wzge.github.io/fedora-pkgbuild/downloads/index.json`。**索引只记录地址，RPM 本身由客户机直接从厂商 CDN 拉取**，本仓库不托管这些安装包。

客户端脚本位于 `scripts/download-index/install-from-index.sh`：

```bash
# 查看索引中的软件与版本
curl -fsSL https://raw.githubusercontent.com/v8wzge/fedora-pkgbuild/main/scripts/download-index/install-from-index.sh | bash -s -- --list

# 下载并从官方源安装（会自动匹配本机架构）
curl -fsSL https://raw.githubusercontent.com/v8wzge/fedora-pkgbuild/main/scripts/download-index/install-from-index.sh | bash -s -- wechat
# 也支持指定架构：... bash -s -- qq aarch64
```

当前索引的软件：

| 包 ID | 软件 | 版本来源 |
| --- | --- | --- |
| `wechat` | 微信 Linux 版 | `linux.weixin.qq.com` 页面 |
| `qq` | QQ Linux 版 | `im.qq.com` 的 `pcConfig.json` |
| `wps-office` | WPS Office Linux 版 | `linux.wps.cn` 下载页 |

新增软件只需在 `scripts/download-index/probes/` 添加一个探测器脚本，输出统一的 JSON（格式见 `probes/common.py`），聚合脚本会自动纳入；某个探测器失败只影响该软件，不影响其他条目。

## 仓库结构

```
.github/workflows/
  _build-git.yml         # 可复用：git 分支快照构建
  _build-release.yml     # 可复用：GitHub Release 资源构建
  build-kdesvn.yml       # 各软件包只保留一份薄配置
  build-klassy.yml
  build-maple-font.yml
  update-download-index.yml  # 国产软件官方下载地址索引（每 3 天）
scripts/                 # 通用构建/发布脚本
  download-index/        # 国产软件官方下载地址索引（探测器/聚合/客户端）
specs/                   # 符合 Fedora 打包规范的 spec 文件
extra/                   # 额外 Source 文件（如 kdesvn 中文翻译）
repo/v8wzge-fedora.repo  # 供用户安装的 dnf 源定义
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
sudo dnf install kdesvn klassy maple-font
```

仓库中的 RPM 未签名，因此 `.repo` 使用 `gpgcheck=0`。如需签名，可在 `scripts/publish-repo.sh` 前增加 `rpmsign` 步骤并把 `.repo` 改为 `gpgcheck=1` + `gpgkey=`。

## 如何升级到 Fedora 46 / 47

构建系统版本通过 GitHub 仓库变量控制，**不需要改代码**：

1. 仓库 Settings → Secrets and variables → Actions → **Variables** → New repository variable
2. 名称填写 `FEDORA_VERSION`，值填写 `46` 或 `47`
3. 删除该变量即可回到默认的 `45`

切换后下一次定时检查会把 `state` 里记录的构建系统版本与当前值比较，发现不同就重新构建全部包，生成 `.fc46` / `.fc47` 的新 RPM 并发布到同一个仓库。旧版本的 RPM 会保留，方便跨版本共存。spec 中的 `%{?dist}` 会自动变成对应版本的 dist tag。

## 说明

- 构建环境默认为 Fedora 45 容器；可用 `FEDORA_VERSION` 变量切换为 46/47。
- **kdesvn 与 Fedora 官方包的区分**：官方提供 `0:2.1.0-18.fc45`，本仓库提供的是 master 分支快照。为避免 dnf 因 release 号（`18` > `0.1`）而选中官方包，本仓库的 kdesvn 使用 `Epoch: 1`，因此快照包永远优先。可用 `rpm -q --qf '%{EPOCH}:%{VERSION}-%{RELEASE}\n' kdesvn` 查看，`1:` 开头即为本仓库快照，`0:` 开头为官方包。klassy 与 maple-font 在 Fedora 官方仓库中不存在，无此问题。
- 三个包共享同一个 `gh-pages` 分支；工作流通过 `rpm-build` 并发组串行发布，避免推送冲突。若仍有并行写入，`scripts/publish-repo.sh` 会先 rebase 再推送。
- RPM 仓库地址：<https://v8wzge.github.io/fedora-pkgbuild/>
- Maple Mono 采用 SIL OFL 1.1；`v8.0-beta.3` 等测试版会被正常打包，RPM 版本中的 `-` 会转换为 `~` 以保证版本比较正确。
- kdesvn 使用本仓库维护的完整简体中文翻译作为 `Source1`，替换上游未完成的 `po/zh_CN/kdesvn.po`。
