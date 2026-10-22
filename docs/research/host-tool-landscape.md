# 宿主机运行时与命令行工具管理方案

记录日期：2026-10-22。只记各方案自己的官方文档或自己的源码仓库写了什么。不比较优劣，不替规格选后端。

种子名单里的方案都在管宿主机上的包、运行时或命令，没有剔除。mise 的官网把 [aqua](https://aquaproj.github.io/) 写成工具来源之一，所以 aqua 多记了一节。asdf 的介绍点了 nvm、n、rbenv、Homebrew、Nix；pyenv 的 README 说自己从 rbenv 改来，并建议 Windows 改用另一个项目 pyenv-win；nvm 的 README 点了 nvm-windows、nodist、nvs，并写明那些不是他们维护的。n、rbenv、pyenv-win、nvm-windows、nodist、nvs 只记到「被点名」，下面没有功能条目。

下面「升级」指已装的运行时或命令，管理器自己的自更新会单独写。官方页没写的，标成文档未写。

## 四类

- 一个命令管多种语言和命令行工具，靠注册表或插件：mise、asdf、proto、vfox、aqua。
- 把包装进隔离环境或 profile：Nix、Devbox、Hermit、pixi。
- 只管一种语言，或该语言的包所提供的命令：uv、pyenv、nvm、fnm、Volta、SDKMAN。
- 操作系统或用户级的包管理器，不按项目目录切换版本：winget、Scoop、Chocolatey、Homebrew、apt。

## mise

[mise 官网](https://mise.jdx.dev/) 把它写成一个 CLI：安装项目工具、设置环境变量、跑任务。平台写的是 macOS、Linux、Windows；Windows 安装示例是 `winget install jdx.mise`。

- 安装指定版本：[Dev tools](https://mise.jdx.dev/dev-tools/) 写 `mise install node@24.11.1` 安装该版本，`mise install node@24` 安装最新的 24.x。
- 多版本并存：同一页的 `mise uninstall node@22` 只删一个版本。
- 生效范围：`mise use` 把版本写进当前项目的 `mise.toml`；`mise use --global` 写到 `~/.config/mise/config.toml`；`mise exec node@24 --` 只对这一次命令生效。同一页写明 `mise use` 不能改它所在的那个 shell，激活要到下一次提示符。
- 非语言命令：官网写注册表里有 1000+ 工具，从 node 到 terraform，并点了 jq、ripgrep。[Registry](https://mise.jdx.dev/registry.html) 写短名如 `jq`、`aws-cli` 映射到后端；不在注册表里的可以用 `github:owner/repo`、`aqua:owner/repo` 这类后端标识。
- 列出已装：`mise ls --current` 显示当前目录正在用的工具（[Dev tools](https://mise.jdx.dev/dev-tools/)）。
- 平台：macOS、Linux、Windows（[官网](https://mise.jdx.dev/)）。
- 非交互：同一页写脚本和 CI 用 `mise exec --` 或 `mise run`。
- 不认识的名字：[错误页](https://mise.jdx.dev/errors.html) 写 `mise install` / `mise use` 对没有注册表条目的名字报 `not found in mise tool registry`，并可能给出 `Did you mean?`。[设置](https://mise.jdx.dev/configuration/settings.html) 写：已激活的 shell 里敲到一个找不到的命令时，`not_found_auto_install` 默认会安装当前配置点了名的那个工具；`not_found_auto_install_registry` 默认关闭，打开后只有注册表里恰好一个工具提供该命令时，才安装并写入全局配置。对不上唯一工具就跳过。
- 卸载：`mise unuse` 改配置，`mise uninstall` 删安装，`mise prune` 删没有配置再用的版本（[Dev tools](https://mise.jdx.dev/dev-tools/)）。
- 升级：`mise upgrade` 在版本请求范围内装更新的发布；`mise outdated` 列出有更新的工具。

## asdf

[介绍](https://asdf-vm.com/guide/introduction.html) 把它写成工具版本管理器：一个 `.tool-versions`，用插件扩展到各种工具和运行时。同一页写它不是系统包管理器，也不管上游依赖。

- 安装指定版本：[Versions](https://asdf-vm.com/manage/versions.html) 写 `asdf install <name> <version>`，也支持 `latest` 和 `latest:<前缀>`。
- 多版本并存：`asdf list <name>` 列出已装版本；`asdf uninstall <name> <version>` 删一个版本。
- 生效范围：`asdf set` 写当前目录的 `.tool-versions`；`asdf set -u` 写 `$HOME/.tool-versions`。环境变量 `ASDF_${TOOL}_VERSION` 盖过文件，且只在设置它的地方生效；文档示例是 `ASDF_ELIXIR_VERSION=1.4.0 mix test`。[入门](https://asdf-vm.com/guide/getting-started.html) 写查找从当前目录往上直到 `$HOME`，没有版本时执行该工具会报错。
- 非语言命令：靠插件。介绍页的例子包括 Node、Ruby、Elixir；版本页用带连字符的 `aws-sam-cli` 说明环境变量名怎么拼。[Plugins](https://asdf-vm.com/manage/plugins.html) 写用 `asdf plugin add` 从短名仓库或 Git URL 加插件。
- 列出已装：`asdf list <name>`；`asdf current`；`asdf plugin list`。
- 平台：入门页有 Linux 各发行版和 macOS 的依赖安装表，并给出 PowerShell Core 把 shims 放进 `PATH` 的配置；预编译包按操作系统和架构下载。没有单独的「支持 Windows」平台表。
- 非交互：这些页上的命令都是直接调用。文档未写关闭提示的开关。`latest` 会在执行时解析成当时的具体版本（入门页）。
- 不认识的名字：入门页写必须先装插件，工具才管得了那个名字；没有版本记录时执行会报错。未添加插件时的原句，已打开的页面没写。
- 卸载：`asdf uninstall <name> <version>`。`asdf plugin remove` 会删掉该插件安装的全部版本。
- 升级：已打开的版本页和插件页没有「把已装工具升到新版本」的命令。`asdf plugin update` 更新的是插件 Git 仓库。

## proto

[概述](https://moonrepo.dev/docs/proto) 把它写成可插拔的版本管理器。工具是编程语言、该语言的依赖或包管理器，或插件提供的自定义实现。同一页写还有 800 多个 asdf 插件。

- 安装指定版本：[install](https://moonrepo.dev/docs/proto/commands/install) 写 `proto install deno 1.31`，也接受部分版本、`latest`、`canary`。不带版本时按 `proto run` 和 shim 的规则探测。
- 多版本并存：安装目录是 `~/.proto/tools/<工具>/<版本>`。[versions](https://moonrepo.dev/docs/proto/commands/versions) 用 `--installed` 只显示已装版本。[uninstall](https://moonrepo.dev/docs/proto/commands/uninstall) 可以只删一个版本，不带版本则删全部。
- 生效范围：[pin](https://moonrepo.dev/docs/proto/commands/pin) 和 [配置](https://moonrepo.dev/docs/proto/config) 写 `.prototools` 可以在目录、`~/.proto/.prototools`（global）、`~/.prototools`（user）。`proto install --pin` 的位置可以是 closest、global、local、user。`PROTO_<工具>_VERSION` 参与探测。[run](https://moonrepo.dev/docs/proto/commands/run) 跑一次。没有「当前 shell 会话、关掉就丢」的作用域命令。
- 非语言命令：概述把自定义工具交给插件，并提到 asdf 插件。不是按任意命令名去装的包管理器。
- 列出已装：`proto versions <工具> --installed`。同页注明旧的 `proto list` 在 v0.44 删除。
- 平台：概述的编译目标表是 macOS Intel 与 ARM、Linux Intel 与 ARM（gnu 和 musl）、Windows Intel 64 位。表里没有 Windows ARM。
- 非交互：install、run 都可以带版本直接跑。配置页的 `auto-install` 默认关闭。文档未写交互确认开关。
- 不认识的名字：已打开的命令页没有写未知工具名的报错原文。
- 卸载：`proto uninstall`。
- 升级：[upgrade](https://moonrepo.dev/docs/proto/commands/upgrade) 升级或降级的是 proto 自己，不是已装的语言工具。

## vfox

[官网](https://vfox.dev/) 写它是多 SDK 版本管理器，支持 Windows（非 WSL）、Linux、macOS，配置文件是 `.vfox.toml` / `vfox.toml`。

- 安装指定版本：[Quick Start](https://vfox.dev/guides/quick-start.html) 写 `vfox install nodejs@21.5.0`。`latest` 取插件返回列表的第一个，文档不建议生产使用。
- 多版本并存：[核心命令](https://vfox.dev/usage/core-commands.html) 的 `vfox list` 可以列出一个 SDK 的多个已装版本；`vfox uninstall <sdk>@<version>` 删一个。
- 生效范围：Quick Start 写三个范围，优先级是 Project > Session > Global > System。`vfox use -p` 写当前目录 `.vfox.toml`；`-s` 只在当前 shell，关掉就清理；`-g` 是用户级默认。Unix 上不带标志默认是 Session，Windows 上默认是 Global。
- 非语言命令：靠插件。[插件命令](https://vfox.dev/usage/plugins-commands.html) 的 `vfox available` 列出可用插件。[全部命令](https://vfox.dev/usage/all-commands.html) 把 vfox 写成 runtime version management。核心文档的例子是 Node 这类 SDK，没有把「任意命令名」写成内建能力。
- 列出已装：`vfox list`。
- 平台：官网写 Windows（非 WSL）、Linux、macOS。Quick Start 给出 scoop、brew、apt、yum、安装脚本和 MSIX。
- 非交互：核心命令写 `vfox install -y` 跳过提示。[FAQ](https://vfox.dev/guides/faq.html) 写 Docker、CI 和非交互 shell 用 `vfox exec`，因为 `vfox activate` 的钩子是给交互 shell 的。
- 不认识的名字：Quick Start 写 `install` 和 `search` 会自动安装缺失的插件。名字不在可用插件里时的报错，已打开的页面没写。
- 卸载：`vfox uninstall` 删一个版本；`vfox remove` 删插件，并删该插件安装的全部运行时。
- 升级：`vfox upgrade` 升级的是 vfox 自己。FAQ 写 vfox 按目录管理版本，不能阻止 SDK 自己原地更新（例子是 `flutter upgrade`）；回到原样用 `vfox install --reinstall`。已打开的命令列表里没有「把已装 SDK 升到最新版」的命令。

## aqua

mise 官网把 aqua 列为工具来源。[aqua 官网](https://aquaproj.github.io/) 把它写成声明式 CLI 版本管理器，并写支持 Windows、macOS、Linux，本地开发和 CI 都能用。

- 安装指定版本：[文档首页](https://aquaproj.github.io/docs/) 的 `aqua.yaml` 示例是 `cli/cli@v2.2.0` 这种带版本的包名；[教程](https://aquaproj.github.io/docs/tutorial/) 写 `aqua g -i` 把包写进配置，再 `aqua i` 安装。
- 多版本并存：官网写可以安装多个版本，并按配置文件切换。
- 生效范围：[配置](https://aquaproj.github.io/docs/reference/config/) 写从当前目录向上查找 `aqua.yaml`，另外有 `AQUA_GLOBAL_CONFIG`。`aqua install` 默认不装全局配置里的包，要加 `-a`（[Usage](https://aquaproj.github.io/docs/reference/usage)）。`aqua exec` 执行一次。没有「只在本次 shell」的作用域命令。
- 非语言命令：这是它的主要对象。教程示例是 GitHub CLI 和 fzf。语言运行时只有在注册表里以 CLI 包存在时才落在这套接口上。
- 列出已装：`aqua list` 列注册表里的包；`aqua list -installed` 只列已安装的；`-a` 把全局配置也算进去。
- 平台：官网写 Windows、macOS、Linux。配置页的 `AQUA_ROOT_DIR` 默认路径分开写了 Linux/macOS 和 Windows。
- 非交互：`aqua i` 和 `aqua g -i` 不打开选择界面。不带参数的 `aqua g` 会启动交互式模糊搜索。懒安装可用 `AQUA_DISABLE_LAZY_INSTALL` 关掉。
- 不认识的名字：`aqua which` 在配置里找不到命令时，会再查 `PATH`；仍然找不到就以非零退出，错误是 `command is not found`。官网写的懒安装是：工具被执行时自动安装。那是已写进配置的工具，不是任意陌生名字。
- 卸载：`aqua remove` 从 `AQUA_ROOT_DIR/pkgs` 删除，默认不改 `aqua.yaml`，也不删 `bin` 里的链接；`-m` 可以选择删链接、删包或两者。
- 升级：`aqua update` 把最近的 `aqua.yaml` 里的包改到最新版本，文档写它不安装这些包。`aqua update-aqua` 升级 aqua 自己。

## Nix

[支持平台](https://nix.dev/manual/nix/2.28/installation/supported-platforms.html)（Nix 2.28.8 手册）写 Nix 支持 Linux（i686、x86_64、aarch64）和 macOS（x86_64、aarch64）。该页没有 Windows。

- 安装指定版本：[nix profile install](https://nix.dev/manual/nix/2.28/command-ref/new-cli/nix3-profile-install) 的例子是 `nixpkgs#hello`、`nixpkgs/release-20.09#hello`，以及钉到某一个 nixpkgs 修订的 `nixpkgs/<commit>#hello`。版本来自那一版软件包集合，不是 `工具@版本` 这种短语法。[nix-env --install](https://nix.dev/manual/nix/latest/command-ref/nix-env/install) 写可以用推导名里的版本，例如同时写出 `gcc-3.3.6` 和 `gcc-4.1.1`。
- 多版本并存：store 里可以有不同的 store path。`nix-env --install` 写，同一代 profile 里两个同名推导通常会因为文件名冲突而失败；`--preserve-installed` 不移除同名旧推导，但是否真能并存取决于包本身。
- 生效范围：`nix profile install` 装进一个 profile，可用 `--profile` 换目标。[nix develop](https://nix.dev/manual/nix/2.28/command-ref/new-cli/nix3-develop) 开一个提供构建环境的 bash，不带参数时用当前目录 flake 的 `devShells` 或 `packages`；`--command` 只跑一条命令。这些页没有写「离开目录就还原 PATH」的全局激活。
- 非语言命令：profile 的例子包括 hello、gdb、blender。Nix 管的是包，手册不把语言运行时和命令行工具分成两类。
- 列出已装：[nix profile list](https://nix.dev/manual/nix/2.28/command-ref/new-cli/nix3-profile-list) 列出 profile 里的包，可以 `--json`。
- 平台：见上面的支持平台页。没有 Windows。
- 非交互：这些命令直接安装或启动 shell，手册没写确认向导。
- 不认识的名字：已打开的手册页没有写未知包属性的报错原文。
- 卸载：[nix profile remove](https://nix.dev/manual/nix/2.28/command-ref/new-cli/nix3-profile-remove) 按名字、正则、store path 或 `--all` 从 profile 移除。
- 升级：[nix profile upgrade](https://nix.dev/manual/nix/2.28/command-ref/new-cli/nix3-profile-upgrade) 用安装时的 flake 取更新的版本。手册写这只对未锁定的 flake 引用有效；安装时如果已经钉死某一个 commit，就没有「更新的版本」可取。

## Devbox

[Devbox 文档](https://www.jetify.com/docs/devbox/) 写它用一份包清单创建隔离、可复现的 shell。包来自 Nix。缺 Nix 时，Devbox 会按系统装一份。

- 安装指定版本：[快速开始](https://www.jetify.com/docs/devbox/quickstart/) 写 `devbox add python@3.10`，不带版本则是该包的 latest。[配置](https://www.jetify.com/docs/devbox/configuration) 写在做得到的地方按 semver，`python@3` 会装主版本 3 的最新版；也可以写 nixpkgs 的 channel 或 commit。
- 多版本并存：每个项目一份 `devbox.json`，shell 之间隔开。同一份环境里把同一个包装成两个版本，已打开的文档没有写成通用能力。
- 生效范围：`devbox shell` 进入项目环境，`exit` 回到原来的 shell。[脚本](https://www.jetify.com/docs/devbox/guides/scripts) 写 `devbox run` 在装好包之后跑一条命令，然后退出。[全局](https://www.jetify.com/docs/devbox/devbox-global) 用 `devbox global add`，并把 `eval "$(devbox global shellenv)"` 放进 shell 启动文件，使全局包出现在 PATH 上。
- 非语言命令：快速开始的例子是 ripgrep；全局文档的例子是 ripgrep、vim、git。语言运行时和命令行工具都是 Nix 包。
- 列出已装：`devbox global list`。项目里要装什么写在 `devbox.json`。已打开的页没有另一个「列出项目里已安装包」的命令名。
- 平台：[devbox add](https://www.jetify.com/docs/devbox/cli-reference/devbox-add) 的平台是 `aarch64-darwin`、`aarch64-linux`、`x86_64-darwin`、`x86_64-linux`，以及会从源码构建的 `i686-linux`、`armv7l-linux`。[安装](https://www.jetify.com/docs/devbox/installing-devbox/) 写 Windows 通过 WSL2 使用，不是原生 Windows。
- 非交互：[devbox install](https://www.jetify.com/docs/devbox/cli-reference/devbox-install) 装完 `devbox.json` 里的包就退出 shell；`devbox run -q` 可以压低日志。
- 不认识的名字：快速开始写先用 `devbox search`。未知包名的报错原文，已打开的页没写。
- 卸载：配置页写 `devbox rm` 从项目移除；全局文档写 `devbox global rm`。[FAQ](https://www.jetify.com/docs/devbox/faq) 的清理是 Nix store 的垃圾回收，以及如何卸掉 Devbox 自己。
- 升级：已打开的页没有「把已装包升到更新版本」的命令。改版本是改 `devbox.json` 里的版本说明。快速开始写 `devbox.lock` 用来让其他人得到同一套包。

## Hermit

[Get Started](https://cashapp.github.io/hermit/usage/get-started/) 写在项目目录 `hermit init`，再 source `./bin/activate-hermit`，把该环境的 `bin` 放进 `PATH`。`deactivate-hermit` 退出。

- 安装指定版本：[包管理](https://cashapp.github.io/hermit/usage/management/) 写三种选择：`名字-版本`（例 `rustc-1.51.0`）、`名字@channel`（例 `rustc@nightly`），或只写名字，按 manifest 的默认、最新稳定、最新不稳定、最后一个 channel 的顺序挑。
- 多版本并存：缓存按包和版本存放（`hermit info` 的 Root 是 `~/.cache/hermit/pkg/...`）。换版本的例子是再 `hermit install` 另一个版本，之后 `rustc --version` 变成那个版本。同一环境里两个版本同时出现在 PATH 上，该页没写。
- 生效范围：一个项目目录一个环境，激活只影响当前 shell。已打开的使用文档没有全局 profile。
- 非语言命令：包管理页的例子有 protoc；[打包教程](https://cashapp.github.io/hermit/packaging/tutorial/) 的例子是 jq。语言和命令行工具都是 manifest 里的包。
- 列出已装：`hermit list`。`hermit search` 在包名和描述里找。
- 平台：[manifest schema](https://cashapp.github.io/hermit/packaging/schema/manifest/) 有 `darwin` 和 `linux` 块。Get Started 的安装是 bash 脚本。已打开的页没有 Windows。
- 非交互：`hermit install` 直接安装。文档未写确认开关。
- 不认识的名字：`hermit which` 在当前环境的 `bin` 里没有这个名字时，什么都不打印，退出码 1，即使 manifest 源里有同名包。`hermit install` 一个没有 manifest 的名字，已打开的页没写。
- 卸载：`hermit uninstall`。
- 升级：`hermit update` 同步 manifest，并更新按 channel 安装的包。`hermit upgrade` 对遵守语义化版本的包升到最新的 minor。

## pixi

[pixi 文档](https://pixi.prefix.dev/latest/) 写它可以做项目环境，也可以用 `pixi global` 安装全局工具。首页把全局工具写成隔离安装，并写它在替换 apt、homebrew、winget 的位置上。

- 安装指定版本：[全局清单](https://pixi.prefix.dev/latest/global_tools/manifest/) 写 `pixi global install "python<3.12"`，依赖可以是具体版本或通配。[全局介绍](https://pixi.prefix.dev/latest/global_tools/introduction/) 的例子是 `pixi global install --expose py3=python "python=3.12"`。[入门](https://pixi.prefix.dev/latest/getting_started/) 写项目里用 `pixi add python`，再用 `pixi run`。
- 多版本并存：全局介绍写每个包默认自己一个环境；用 `--expose` 把可执行文件暴露成另一个名字，这样多个 Python 可以同时在 PATH 上。
- 生效范围：全局工具暴露到系统 PATH，清单在用户配置目录的 `pixi-global.toml`（清单页按操作系统列了路径）。项目工具跟 `pixi.toml` 和 `pixi run`。已打开的页没有「只改当前 shell、不写清单」的作用域。
- 非语言命令：首页和全局安装页的例子包括 gh、nvim、ripgrep、terraform、ansible。同时也装 Python。
- 列出已装：入门页写 `pixi global list` 列出全部全局环境。
- 平台：[安装](https://pixi.prefix.dev/latest/installation/) 有 Linux 与 macOS 的 shell 脚本，以及 Windows 的 PowerShell 脚本、msi、winget、scoop。
- 非交互：这些安装命令直接执行。文档未写确认向导。
- 不认识的名字：已打开的页没写未知包名的报错原文。
- 卸载：入门页写 `pixi global uninstall`。
- 升级：入门页写 `pixi global update`。`pixi self-update` 升级的是 pixi 自己。

## uv

uv 的文档把两件事分开：它自己安装 Python，以及安装「提供命令行的 Python 包」。

- 安装指定版本：[Python versions](https://docs.astral.sh/uv/concepts/python-versions/) 写 `uv python install 3.12.3`，也接受 `3.12` 和版本范围。默认在找不到时自动下载，可用 `python-downloads` 或 `--no-python-downloads` 关掉。[Tools](https://docs.astral.sh/uv/concepts/tools/) 写 `uv tool install ruff==0.5.0` 或 `ruff@0.6.0`。
- 多版本并存：`uv python install 3.9 3.10 3.11` 可以一次装多个。可执行文件按 minor 放进 PATH，例如 `python3.12`；`--default` 才会再提供 `python` 和 `python3`。每个已安装的工具在自己的环境里。同名可执行文件如果不是 uv 装的，`uv tool install` 会失败，除非 `--force`。
- 生效范围：`uv python pin` 写当前目录的 `.python-version`；`uv python pin --global` 写用户配置目录。查找时当前目录和父目录优先于用户级文件，但不越过项目边界。工具环境忽略 `.python-version` 和项目的 `requires-python`。`uvx`（即 `uv tool run`）跑一次，不把工具留在 PATH 上。`uv tool install` 把可执行文件放进用户级目录。
- 非语言命令：Tools 页写工具是提供命令行接口的 Python 包。不是通用的二进制安装器。
- 列出已装：`uv python list --only-installed`。[CLI 参考](https://docs.astral.sh/uv/reference/cli/#uv-tool-list) 写 `uv tool list` 列出已安装的工具。
- 平台：Python 版本页写 uv 自带 macOS、Linux、Windows 上可下载的 CPython 和 PyPy 发行版。Windows 上安装会按 PEP 514 写注册表。
- 非交互：安装命令直接下载。文档未写确认向导。
- 不认识的名字：`uv tool run` 从命令名推断包名。Tools 页写额外依赖的版本如果冲突，解析失败并报错。一个完全不存在的包名会打印哪一句，该页没有引用。
- 卸载：CLI 参考写 `uv tool uninstall <NAME>`，也可以 `--all`。Python 版本页写卸载时会删掉对应的 Windows 注册表项；这次没有打开 `uv python uninstall` 的参数页。
- 升级：`uv python upgrade` 只把受管理的 CPython 升到最新 patch，不跨 minor。`uv tool upgrade` 在安装时给出的版本约束里升级。

## pyenv

[pyenv README](https://github.com/pyenv/pyenv/blob/master/README.md) 写它用来在多个 Python 版本之间切换。它不管 virtualenv，除非另装插件。

- 安装指定版本：`pyenv install 3.10.4`。`pyenv install 3.10` 会解析到该条版本线上最新的已知版本。大多数是从源码构建。
- 多版本并存：每个版本一个目录，`$(pyenv root)/versions/<版本>`。`pyenv global 3.11 3.12` 可以同时选中多个，命令按给出的顺序找。
- 生效范围：`pyenv shell` 只当前 shell；`pyenv local` 写当前目录的 `.python-version`，对当前目录和子目录生效；`pyenv global` 写用户级的 `$(pyenv root)/version`。选择顺序是 `PYENV_VERSION`、当前目录及父目录的 `.python-version`、全局文件。
- 非语言命令：不安装。README 写，选中的 Python 安装里没有某个可执行文件时，shim 会落到 PATH 上更后面的程序。
- 列出已装：`pyenv install -l` 列出可以安装的版本。README 没有写出「列出已安装版本」的子命令名；它指向的 `COMMANDS.md` 这次打开返回 404。
- 平台：README 有 Linux/Unix 和 macOS。Windows 一节写 pyenv 官方不支持 Windows，在 WSL 里装的也是 Linux 版 Python，并建议使用另一个项目 pyenv-win。
- 非交互：安装和切换命令直接执行。文档未写确认开关。
- 不认识的名字：接口是 Python 版本，不是任意工具名。
- 卸载：`pyenv uninstall <版本>`。
- 升级：README 的 Upgrading 升的是 pyenv 自己（`brew upgrade pyenv`、`pyenv update` 或 git）。换 Python 版本是再 `pyenv install`。

## nvm

[nvm README](https://github.com/nvm-sh/nvm/blob/master/README.md) 写它是 bash 里 source 的 shell 函数，不是一个可执行文件。`which nvm` 找不到它。

- 安装指定版本：`nvm install 14.7.0`。也接受 `node`、`lts/*` 这类别名。没有该平台的预编译包时，默认从源码编译；非 WSL 的 Windows 不能编译。
- 多版本并存：`nvm ls` 列出已安装的版本。
- 生效范围：`nvm use` 作用于当前 shell。`nvm alias default` 决定新 shell 用哪个版本。`.nvmrc` 要再执行 `nvm use` 或 `nvm install` 才会用；没有版本参数、也没有 `.nvmrc` 时，`nvm use` 退出码 127。README 另给了放进 shell 启动文件的函数，用来在进入目录时调用 `nvm use`。`nvm exec <版本> <命令>` 在子 shell 里跑一条命令。
- 非语言命令：不管。`--reinstall-packages-from` 能把一个 Node 版本上的全局 npm 包拷到另一个版本。
- 列出已装：`nvm ls`。`nvm ls-remote` 列出可安装的版本。
- 平台：README 写通过 WSL、Git Bash（MSYS）或 Cygwin 在 Windows 上的一些情况。原生 Windows 的替代品 nvm-windows、nodist、nvs 不是他们维护的。Fish 也不支持。
- 非交互：Docker 示例是直接 `nvm install`。文档未写关闭提示的开关。
- 不认识的名字：接口是 Node 版本，不是任意工具名。
- 卸载：`nvm uninstall`。
- 升级：Usage 里没有把已装的 Node 原地升级的命令。装一个更新的版本再 `nvm use`。

## fnm

[fnm README](https://github.com/Schniz/fnm/blob/master/README.md) 写它是 Rust 写的 Node 版本管理器，支持 macOS、Windows、Linux，并认 `.node-version` 和 `.nvmrc`。

- 安装指定版本：[commands.md](https://github.com/Schniz/fnm/blob/master/docs/commands.md) 写 `fnm install [VERSION]`，版本可以是部分 semver，或 `lts/名字`。另有 `--lts` 和 `--latest`。
- 多版本并存：`fnm list` 列出本地已安装的 Node 版本。
- 生效范围：`fnm default` 是 `fnm alias <版本> default` 的简写。`fnm use` 切换版本；README 写在 shell 里用 `fnm env --use-on-cd`，进入目录时按版本文件切换。`fnm exec --using=<版本>` 跑一条命令。
- 非语言命令：不管。命令列表里没有安装任意 CLI 的子命令。
- 列出已装：`fnm list`。`fnm list-remote` 列出远端版本。
- 平台：README 的功能列表写 macOS、Windows、Linux。Windows 的安装示例是 winget、Scoop、Chocolatey。
- 非交互：`fnm use --install-if-missing` 在缺少时安装。`--log-level quiet` 可以压低输出。它是单个可执行文件，不是要 source 的函数。
- 不认识的名字：接口是 Node 版本。版本未安装且没加 `--install-if-missing` 时的原句，commands.md 没有引用。
- 卸载：`fnm uninstall`。给别名时，会卸掉别名指向的那个 Node 版本，以及指向同一版本的其他别名。
- 升级：commands.md 的子命令里没有 upgrade。README 的 Upgrade 升的是 fnm 自己。

## Volta

[指南](https://docs.volta.sh/guide/) 写 Volta 管理 JavaScript 命令行工具，用 shim 选择版本，并写支持 Windows 和全部 Unix shell。

- 安装指定版本：`volta install node@22`。[install 参考](https://docs.volta.sh/reference/install/) 写参数形如 `node`、`yarn@latest` 或 `your-package@^14.4.3`，并会在本地没有缓存时取下来。`volta install` 同时把该版本设成默认。
- 多版本并存：指南写项目钉住一个 Node 后，在该目录里自动用那个版本；工具在安装时钉到当时的 Node，不随 Node 升级而重装。[list](https://docs.volta.sh/reference/list/) 能查看已安装的 Node、包管理器和带可执行文件的包。
- 生效范围：`volta install` 设置 toolchain 里的默认版本。[pin](https://docs.volta.sh/reference/pin/) 把 Node 或包管理器写进项目的 `package.json`；依赖的版本要用 `npm install` 或 `yarn add`，不能用 `volta pin`。参考里的子命令没有「只限本次 shell」。
- 非语言命令：指南的例子是 `npm install -g surge` 这类 JavaScript 包的命令。不是通用 CLI 管理器。
- 列出已装：`volta list`，可用 `--current`、`--default`，输出格式可以是 `plain`。
- 平台：指南写包含 Windows 和全部 Unix shell。
- 非交互：参考里的命令有 `--quiet`。文档没写安装确认向导。
- 不认识的名字：install 接受的是工具加可选版本。既不是 Node 或包管理器、也不是可安装包时的报错，已打开的参考页没写。
- 卸载：[命令一览](https://docs.volta.sh/reference/) 有 `uninstall`。这次没有打开该子命令页，所以不记参数。
- 升级：命令一览里没有 upgrade。换版本是再 `install` 或再 `pin`。

## SDKMAN

[用法](https://sdkman.io/usage) 写的是安装候选 SDK。例子是 Java、Scala、Groovy，列表输出里还有 Gradle、Grails、Spring Boot。`sdk list` 列出的是候选，不是任意命令。

- 安装指定版本：`sdk install scala 3.4.2`。不写版本则装该候选当前的最新稳定版。也可以把本机已有的目录登记成一个本地版本。
- 多版本并存：`sdk list groovy` 用 `*` 标出已安装的多个版本，用 `>` 标出当前在用的。
- 生效范围：`sdk use` 只切换当前终端；`sdk default` 让之后打开的 shell 使用该版本。`.sdkmanrc` 配 `sdk env` 在当前 shell 里切换；`sdkman_auto_env=true` 才在 `cd` 进目录时自动切换，并在离开时恢复默认。
- 非语言命令：候选里有构建工具。不在候选列表里的名字，用法页没写会怎样。
- 列出已装：`sdk list` 列候选；`sdk list <候选>` 里用符号标出已安装和当前版本；`sdk current` 显示正在用的版本。
- 平台：[安装](https://sdkman.io/install) 写 macOS、Linux，以及 Windows 上的 WSL 或 Git Bash。不能在原生 Windows 上安装，不再支持 Cygwin。需要 bash。
- 非交互：配置项 `sdkman_auto_answer=true`，用法页写这是 CI 偏好的设置。安装器的 `ci=true` 会打开自动回答、关掉颜色和自更新。
- 不认识的名字：已打开的用法页没有写未知候选名的报错原文。
- 卸载：`sdk uninstall scala 3.4.2`。卸的是一个版本；本地版本只去掉登记，不删磁盘上的那份安装。
- 升级：`sdk upgrade` 的示例是打印哪些已装版本落后于当前稳定版，标题下的说明是查看过时情况。该页没有写它会把新版本装上。`sdk selfupdate` 升级 SDKMAN 自己；`sdk update` 刷新候选缓存。

## winget

[WinGet 概述](https://learn.microsoft.com/en-us/windows/package-manager/winget/) 写它在 Windows 10、Windows 11 和 Windows Server 2025 上发现、安装、升级、移除和配置应用程序。命令行只支持 Windows 10 版本 1809 或更新。

- 安装指定版本：[install](https://learn.microsoft.com/en-us/windows/package-manager/winget/install) 写 `--version` 安装一个精确版本；不写则安装最高版本。例子是 `winget install --id Microsoft.PowerToys --version 0.91.1`。
- 多版本并存：概述的命令表有 `pin`。已打开的页没有写同一应用的多个版本同时可用。
- 生效范围：`--scope` 选 user 或 machine。不是按目录，也不是按本次 shell。
- 非语言命令：装的是应用。例子有 PowerToys、Visual Studio Code、PowerShell、Git。概述不把语言运行时和命令行工具分成两类。
- 列出已装：概述的命令表写 `list` 显示已安装的包。`export` 可以导出已装包的列表，`import` 再装上。
- 平台：上面的 Windows 版本。不是 macOS 或 Linux。
- 非交互：`--disable-interactivity`、`--silent`、`--accept-package-agreements`、`--accept-source-agreements`。概述写不加管理员权限时，需要提升的安装会弹出提升提示。
- 不认识的名字：install 页写，查询对不上唯一应用时，WinGet 会把搜索结果显示出来，让你收窄。概述写社区仓库没有的工具可以去提交包。零结果时的原句，已打开的页没引用。
- 卸载：概述的命令表有 `uninstall`。
- 升级：概述的命令表有 `upgrade`。

## Scoop

[scoop.sh](https://scoop.sh/) 写在 PowerShell 5.1 或更新版本里，从命令行安装程序，把它们放在 `~\scoop`，用 `~\scoop\shims` 里的 shim 放进 PATH。首页的例子有 Node.js、Python，也有 Neovim 和 VS Code。

指定版本的安装语法，Scoop 的 GitHub wiki 里有，这次不把 wiki 当依据。下面关于多版本和卸载的句子来自仓库里的命令脚本。

- 多版本并存：[`scoop-cleanup.ps1`](https://github.com/ScoopInstaller/Scoop/blob/master/libexec/scoop-cleanup.ps1) 的帮助写它通过删除旧版本来清理；当前版本以外的目录会被删掉。这说明旧版本会留在应用目录里，直到清理。[`scoop-uninstall.ps1`](https://github.com/ScoopInstaller/Scoop/blob/master/libexec/scoop-uninstall.ps1) 在卸掉当前版本后会打印 `Removing older version`。
- 生效范围：安装在用户的 `~\scoop`，或用 `-g` / `--global`（cleanup 和 uninstall 脚本都有这个开关，且要求管理员）。[`scoop-reset.ps1`](https://github.com/ScoopInstaller/Scoop/blob/master/libexec/scoop-reset.ps1) 在已安装的应用之间重做 shim；帮助示例是 `python` 和 `python27` 两个应用名。版本没有安装时，脚本报 `'<app> (<version>)' isn't installed`。不是按项目目录，也不是按本次 shell。
- 非语言命令：首页把终端程序和图形程序都当包装。shim 给终端程序，开始菜单快捷方式给图形程序。
- 列出已装：[`scoop-list.ps1`](https://github.com/ScoopInstaller/Scoop/blob/master/libexec/scoop-list.ps1) 写 `scoop list [query]` 列出已安装的应用，或名字匹配查询的那些。
- 平台：首页只写了 Windows PowerShell。
- 非交互：首页的安装命令直接执行。已打开的脚本头没写确认开关。
- 不认识的名字：首页的 `scoop search` 会区分本地 bucket 和其他已知 bucket。`scoop install` 一个不存在的名字时的原句，已打开的材料没写。
- 卸载：`scoop uninstall`，可选 `--purge` 删除持久数据。
- 升级：已打开的首页和上述脚本没有升级命令的说明。

## Chocolatey

已打开的命令页以 Windows 功能为例，例如用 DISM 安装 Windows Feature（[install](https://docs.chocolatey.org/en-us/choco/commands/install/)）。这些页没有把 macOS 或 Linux 写成支持平台。

- 安装指定版本：install 页的例子是 `choco install nodejs.install --version 0.10.35`。`--version` 的说明是安装一个指定版本，默认不指定。也可以用 `packages.config` 列出多个包和版本。
- 多版本并存：已打开的页没有写同一个包的多个版本同时安装。
- 生效范围：装到这台机器上。不是按目录或本次 shell。
- 非语言命令：例子有 git 和 nodejs。包就是包，页上不分成运行时和命令行工具。
- 列出已装：[list](https://docs.chocolatey.org/en-us/choco/commands/list/) 写 `choco list`。`-i` 把「程序和功能」里不是 Chocolatey 管的软件也算进去。打开 `useEnhancedExitCodes` 时，没有结果的退出码是 2。
- 平台：见本节开头。
- 非交互：`-y` / `--yes` / `--confirm` 在 install 和 list 页都有，说明是对提示回答是。
- 不认识的名字：list 在增强退出码下用 2 表示没有结果。install 找不到包时的原句，install 页没引用。
- 卸载：install 页把 uninstall 和 install、upgrade 并列为会在第一个包失败时停下的操作。这次没有打开 uninstall 命令页，所以不记参数。
- 升级：[upgrade](https://docs.chocolatey.org/en-us/choco/commands/upgrade/) 写升级一个或一组包；如果还没装，upgrade 会安装它。`all` 升级全部已装包。`choco pin` 或 `--except` 可以跳过。

## Homebrew

[手册](https://docs.brew.sh/Manpage) 写 Homebrew 用来安装 macOS 没有带上的 UNIX 工具，也可以在不使用 `sudo` 的情况下安装 Linux 发行版没有打包的软件。

- 安装指定版本：[Formulae Versions](https://docs.brew.sh/Versions) 写 homebrew/core 用 `foo@1.2` 这种版本化公式提供多个版本，标准包括：和当前稳定版差在 major 或 minor，而不是 patch；同时存在的版本（含主公式）一般不超过五个。[Tips](https://docs.brew.sh/Tips-and-Tricks) 的例子是 `brew install gcc@9`。想要的旧版如果没有版本化公式，手册的 `brew version-install` 会把某一历史版本抽到个人 tap 再安装。
- 多版本并存：版本页写，如果上游不允许版本化公式和主公式同时链接，就用 `keg_only :versioned_formula`，让多个版本同时装在机器上。Tips 写 `brew unlink` 和 `brew link` 用来改 prefix 里当前链接的是哪一个。
- 生效范围：公式安装到 Homebrew 的 prefix。keg-only 的公式不会自动链进 prefix。已打开的手册页没有按目录或按本次 shell 切换版本的命令。`Brewfile` 是另一份要安装的清单（手册的 `brew bundle`）。
- 非语言命令：公式是包，cask 是另一类。语言运行时也以公式存在。手册不把二者分成两套命令。
- 列出已装：`brew list` 列出已安装的公式。
- 平台：[Homebrew on Linux](https://docs.brew.sh/Homebrew-on-Linux) 写可以在 Linux 和 WSL 2 上使用，并写可以用同一个包管理器管理 macOS、Linux 和 Windows。同一页的安装步骤是 Linux 前缀 `/home/linuxbrew/.linuxbrew` 和 WSL，不是原生 Windows。
- 非交互：手册写 `brew upgrade -y` / `--no-ask` 在下载和升级前不问。`brew as-brew-user install --yes` 用于没有人登录时的脚本。
- 不认识的名字：`brew search` 对公式名和 cask token 做子串或正则搜索。`brew install` 一个不存在的公式时的原句，手册没写。
- 卸载：`brew uninstall`。`brew autoremove` 卸掉只是作为依赖装上、现在不再需要的公式。
- 升级：`brew upgrade` 升级过时且没有 pin 住的包。可以只点名一个公式或 cask。

## apt

依据是 Debian 的 [apt-get(8)](https://manpages.debian.org/unstable/apt/apt-get.8.en.html)。它管理的是这份系统的软件源里的包。手册没有把 macOS 或 Windows 写成支持平台。

- 安装指定版本：`install` 一节写，包名后面加 `=` 和版本号就选那个版本；加 `/` 和发行版或 archive 名（stable、testing、unstable）就选那个发行版里的包。版本必须是源里能定位到的。
- 多版本并存：该手册没有把「同一个包的多个版本同时安装」写成能力。
- 生效范围：这台系统上的包。不是按目录，也不是按本次 shell。
- 非语言命令：参数是包名。语言运行时和命令行工具都只是源里的包。
- 列出已装：已打开的 apt-get(8) 没有「列出已安装包」的子命令。
- 平台：Debian 的 apt-get。见本节开头。
- 非交互：`-y` / `--yes` / `--assume-yes` 对提示回答是。
- 不认识的名字：手册没有引用找不到包时的原句。
- 卸载：`remove` 卸包但留下配置；`purge` 连配置一起删。
- 升级：先 `update` 更新索引，再 `upgrade` 把已安装的包装到源里的最新版。`upgrade` 不会移除已装包，也不会装上原先没装的包。

## 功能矩阵

单元格只标有没有，以及官方文档把范围或对象收在哪里。细节和链接在上面各节。「未写」表示已打开的官方页没有写这件事。

| 方案       | 指定版本                                            | 多版本并存                      | 生效范围                                       | 非语言命令             | 列出已装                                 | 平台                                     | 非交互                     | 不认识的名字                     | 卸载                   | 升级已装工具                          |
| ---------- | --------------------------------------------------- | ------------------------------- | ---------------------------------------------- | ---------------------- | ---------------------------------------- | ---------------------------------------- | -------------------------- | -------------------------------- | ---------------------- | ------------------------------------- |
| mise       | 有                                                  | 有                              | 全局、目录、单次命令                           | 有，注册表或后端标识   | 有                                       | 三端                                     | 有，`exec`                 | 报不在注册表；可另开自动安装     | 有                     | 有                                    |
| asdf       | 有                                                  | 有                              | 全局、目录、环境变量                           | 有，先加插件           | 有                                       | 文档有 Linux、macOS 和 PowerShell 配置   | 命令可直接调用             | 未写未知插件的原句；没版本会报错 | 有                     | 未写                                  |
| proto      | 有                                                  | 有                              | 目录、用户、全局、单次运行                     | 语言、包管理器、插件   | 有                                       | 三端的列出的目标；无 Windows ARM         | 命令可直接调用             | 未写                             | 有                     | 未写；`upgrade` 只升 proto            |
| vfox       | 有                                                  | 有                              | 全局、项目、本次 shell                         | 取决于插件             | 有                                       | 三端，Windows 非 WSL                     | 有，`-y` 和 `exec`         | 未写未知插件的原句               | 有                     | 未写；`upgrade` 只升 vfox             |
| aqua       | 有，写在 YAML                                       | 有                              | 目录配置、全局配置、单次执行                   | 有，这是主对象         | 有                                       | 三端                                     | 有；不带参数的搜索是交互的 | `which` 报 command is not found  | 有                     | 有改配置的 `update`，该命令本身不安装 |
| Nix        | 有，靠包集合的修订或推导名                          | profile 里同名通常冲突          | profile；`nix develop` 是一个 shell 或一条命令 | 有，都是包             | 有                                       | Linux、macOS                             | 命令可直接调用             | 未写                             | 有                     | 有，且只对未锁定的 flake              |
| Devbox     | 有，`包@版本`                                       | 按项目隔离；同一环境未写        | 项目 shell、单次 `run`、全局 shellenv          | 有，Nix 包             | 全局有；项目看 `devbox.json`             | macOS、Linux；Windows 经 WSL2            | 有，`install` 和 `run`     | 未写                             | 有 `rm`                | 未写                                  |
| Hermit     | 有                                                  | 缓存按版本；PATH 上同时两个未写 | 项目环境，激活于当前 shell                     | 有                     | 有                                       | 文档有 darwin、linux                     | 命令可直接调用             | `which` 退出码 1；install 未写   | 有                     | 有                                    |
| pixi       | 有                                                  | 有，全局环境隔离并用别名暴露    | 全局 PATH，或项目 `pixi run`                   | 有                     | 有                                       | 三端                                     | 命令可直接调用             | 未写                             | 有                     | 有                                    |
| uv         | 有，限 Python 和 Python 包                          | 有                              | 用户、目录 pin、单次 `uvx`                     | 仅 Python 包的命令     | 有                                       | 三端                                     | 命令可直接调用             | 未写不存在包名的原句             | 工具有                 | 有，Python 只升 patch                 |
| pyenv      | 有，限 Python                                       | 有                              | 用户、目录、当前 shell                         | 无                     | 可装版本有；已装子命令名未在 README 写出 | Linux、macOS；Windows 官方不支持         | 命令可直接调用             | 不接受任意工具名                 | 有                     | 未写；升级节升的是 pyenv              |
| nvm        | 有，限 Node                                         | 有                              | 默认版本、当前 shell、单次 `exec`              | 无                     | 有                                       | POSIX；Windows 经 WSL、Git Bash、Cygwin  | 命令可直接调用             | 不接受任意工具名                 | 有                     | 未写                                  |
| fnm        | 有，限 Node                                         | 有                              | 默认、`use`、进目录、单次 `exec`               | 无                     | 有                                       | 三端                                     | 有，`--install-if-missing` | 不接受任意工具名                 | 有                     | 未写；升级节升的是 fnm                |
| Volta      | 有，限 Node、包管理器和 JS 包                       | 有，按项目 shim                 | 默认 toolchain、项目 `package.json`            | 仅 JS 工具链和包       | 有                                       | Windows 和 Unix shell                    | 有 `--quiet`               | 未写                             | 命令存在，参数未打开   | 未写                                  |
| SDKMAN     | 有，限候选 SDK                                      | 有                              | 默认、当前终端、目录 `.sdkmanrc`               | 仅候选，含部分构建工具 | 有                                       | macOS、Linux；Windows 经 WSL 或 Git Bash | 有，`sdkman_auto_answer`   | 未写                             | 有                     | `upgrade` 页只展示过时，未写会安装    |
| winget     | 有，源里的精确版本                                  | 未写                            | 用户或机器                                     | 有，应用即包           | 有                                       | 仅 Windows                               | 有                         | 不唯一时列出搜索结果             | 有                     | 有                                    |
| Scoop      | 版本参数在 reset 源码里；安装语法未以非 wiki 页核实 | 有，旧版本会留下                | 用户或 global shim                             | 有                     | 有                                       | 仅 Windows                               | 脚本直接执行               | 未写                             | 有                     | 未写                                  |
| Chocolatey | 有                                                  | 未写                            | 这台机器                                       | 有                     | 有                                       | 已打开的页是 Windows                     | 有，`-y`                   | 未写 install 的原句              | 命令被点名，参数未打开 | 有                                    |
| Homebrew   | 有，限版本化公式或抽出的历史公式                    | 有，keg-only                    | prefix，全局链接                               | 有                     | 有                                       | macOS、Linux、WSL2                       | 有，`--yes`                | 未写                             | 有                     | 有                                    |
| apt        | 有，源里的 `包=版本`                                | 未写                            | 这台系统                                       | 有                     | 未写                                     | Debian 的 apt-get                        | 有，`--assume-yes`         | 未写                             | 有                     | 有                                    |

## 文档没写清的共同缺口

- 叫出一个管理器不认识的名字时，多数官方页没有引用原句。写清楚的是 mise、aqua 的 `which`、Hermit 的 `which`、winget 在结果不唯一时的行为。单语言管理器则根本不接受任意工具名。
- 「升级已装工具」和「升级管理器自己」经常是两条不同的命令。proto、vfox、fnm、pyenv 已打开的页只写了后者，或者没写前者。
- 系统包管理器（winget、Chocolatey、Homebrew、apt）能装指定版本，但版本必须来自它们的源或公式。它们的文档没有把「按目录切换、离开目录就还原」写成能力。Scoop 的多版本留在用户目录里，用 reset 改当前 shim，同样不是按目录。
- 原生 Windows、WSL 里的 Linux、以及「文档只写了 PowerShell 配置」不是一回事。Nix 和 Devbox 的已打开页面把 Windows 排除在原生支持之外，Devbox 写的是 WSL2。pyenv 明确不支持 Windows。SDKMAN 和 nvm 要求 bash 或 WSL。asdf 有 PowerShell 配置，但没有平台支持表。
