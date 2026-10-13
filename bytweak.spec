Name:           bytweak
Version:        1.1.5
Release:        2%{?dist}
Summary:        基于 PySide6 的简易 Fedora 系统调节工具

License:        GPLv3+
URL:            https://github.com/Maomaokuxs/bytweak

# Copr 官方 rpkg 魔法宏
Source0:        {{{ git_dir_pack }}}

BuildArch:      noarch
Requires:       python3-pyside6
Requires:       python3-libdnf5
Requires:       polkit
Requires:       grub2-tools
Requires:       pciutils
Requires:       flatpak

%description
一个为 Fedora 打造的系统调节工具，目前支持免核心破坏的系统时区修改，
针对多分辨率变体全家桶的 GRUB2 主题智能解压、安全备份与双模切换，
以及涵盖 NVIDIA/AMD/Intel 的全显卡多媒体硬件加速智能探知与一键修复引擎。

%prep
{{{ git_dir_setup_macro }}}

%build
# 强制塞入 Python 蛇头，防止被误认为 Bash 脚本
sed -i '1i #!/usr/bin/python3' app.py

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/bytweak
mkdir -p %{buildroot}%{_datadir}/applications

# 畅通无阻的平铺拷贝
cp app.py %{buildroot}%{_bindir}/bytweak
cp main.ui %{buildroot}%{_datadir}/bytweak/main.ui
cp style.qss %{buildroot}%{_datadir}/bytweak/style.qss
cp style-dark.qss %{buildroot}%{_datadir}/bytweak/style-dark.qss

# 🌟 核心增补：将业务子模块集群及其物理目录顺滑平铺导入系统静态目录
cp -r modules %{buildroot}%{_datadir}/bytweak/

# 规范化定向输出桌面启动图标
echo "[Desktop Entry]" > %{buildroot}%{_datadir}/applications/bytweak.desktop
echo "Type=Application" >> %{buildroot}%{_datadir}/applications/bytweak.desktop
echo "Name=bytweak" >> %{buildroot}%{_datadir}/applications/bytweak.desktop
echo "Comment=简易时区修改、GRUB2 智能主题全家桶与显卡加速配置" >> %{buildroot}%{_datadir}/applications/bytweak.desktop
echo "Exec=bytweak" >> %{buildroot}%{_datadir}/applications/bytweak.desktop
echo "Icon=system-run" >> %{buildroot}%{_datadir}/applications/bytweak.desktop
echo "Terminal=false" >> %{buildroot}%{_datadir}/applications/bytweak.desktop
echo "Categories=System;Settings;" >> %{buildroot}%{_datadir}/applications/bytweak.desktop
echo "StartupNotify=true" >> %{buildroot}%{_datadir}/applications/bytweak.desktop
echo "StartupWMClass=bytweak" >> %{buildroot}%{_datadir}/applications/bytweak.desktop

%files
# 无视 Git 原生权限，落地强制赋予 0755
%attr(0755, root, root) %{_bindir}/bytweak
%{_datadir}/bytweak/main.ui
%{_datadir}/bytweak/style.qss
%{_datadir}/bytweak/style-dark.qss
# 🌟 声明整个子模块目录所有权（自动剔除 pycache 干扰）
%{_datadir}/bytweak/modules/
%{_datadir}/applications/bytweak.desktop

%changelog
* Mon Jun 22 2026 biyuan <biyuan@fedoraproject.org> - 1.1.5-2
- Release bump: 新增深色主题 / 自动切换支持后重新构建。

* Mon Jun 22 2026 biyuan <biyuan@fedoraproject.org> - 1.1.5-1
- 新增 Fcitx5 输入法主题独立管理面板，支持本地主题扫描、一键切换与压缩包导入。
- 重写 Fcitx 页面 UI（布局管理器替代绝对定位），修复页面控件与鼠标页面的命名冲突。
- 在 app.py 中正式接入 FcitxManager 模块并完成冷启动渲染。
- 增强深色主题独立选择与系统配色自动切换开关，重构 classicui.conf 配置读写引擎。

* Thu Jun 18 2026 biyuan <biyuan@fedoraproject.org> - 1.1.4-1
- 【重磅】完成项目的全盘模块化低耦合解耦改造，正式确立大管家+子业务集群架构。
- 升级软件源扫描核心，引入 `rpm -E` 底层求值引擎，完美清洗并烫平 `$releasever` 及 `$basearch` 原生环境变量，终结 UI 乱码变体。
- 引入用户态单次 Sudo 提权密码令牌缓存锁，后台利用管道技术进行静默高能运转，彻底杜绝高频配置时的 Polkit 连环弹窗“密码地狱”。
- 废除脆弱的 sed 正则范围匹配，改用 100% 稳固的纯 Python 状态机内存级文件内容解析与重组，降维打击彻底终结带冒号 Copr 仓库导致的未终止正则表达式崩溃。
- 引入原子级提权覆盖策略（`cp -f`），并强制追加 `chown/chmod` 系统级安全权限校准，防范 DNF 越权警告。
- 建立时区管理中的标签文本与下拉框指针双重联动校准，攻克冷启动状态不同步的瑕疵。

* Wed Jun 17 2026 biyuan <biyuan@fedoraproject.org> - 1.1.3-1
- 【重磅】发布 1.1.3 稳定版，重构软件源管理面板，将 RPM Fusion 全家桶折叠为顶级总闸虚拟节点。
- 引入“鼠标物理点击监听（itemClicked）”与页面“可见性懒加载”技术，彻底斩断信号自扰引起的全局切页卡死。
- 废除脆弱的 dnf5 config-manager 启闭指令，改用提权下发物理级 sed 精准文本改写策略，攻克带冒号（:）的复杂 Copr RepoID 无法被 DNF5 识别的底层顽疾。

* Wed Jun 17 2026 biyuan <biyuan@fedoraproject.org> - 1.1.2-1
- 新增用户态鼠标光标样式管理面板，打通本地主题一键就地切换选单与 KDE 6 / KWin 原生级热刷新接口。
- 攻克 Xcursor 二进制协议，首创基于 TOC 导航的高清图像块贪婪提取机制，实现 2x2（标准/手型/工字/忙碌）视网膜级四宫格阵列画布预览。
- 实现外部鼠标主题压缩包智能防套娃解压、规整清洗导入及三维一体（XWayland/GTK/GSettings）无损刷新部署。

* Tue Jun 16 2026 biyuan <biyuan@fedoraproject.org> - 1.1.1-1
- 修复 Wayland (Niri/KDE) 环境下的任务栏图标分离瑕疵，补齐 StartupWMClass 映射。

* Tue Jun 16 2026 biyuan <biyuan@fedoraproject.org> - 1.1.0-1
- 【重磅】新增显卡硬件加速智能面板，支持探知 Intel/AMD/NVIDIA 显卡并一键部署 RPM Fusion 满血编解码环境。
- 【重磅】合并 GRUB 主题应用按钮，支持“外部解压安装”与“本地已存主题一键切换”双模智能调度。
- 引入 pciutils 依赖以支持底层硬件扫描。

* Tue Jun 16 2026 biyuan <biyuan@fedoraproject.org> - 1.0.0-1
- 初始版本发布，支持基本的时区修改与外部 GRUB 主题去重安装，修复文件权限与 Copr 打包流。