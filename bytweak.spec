Name:           bytweak
Version:        0.1.0
Release:        1%{?dist}
Summary:        Fedora 系统调节工具（PySide6 + QML）
License:        GPLv3+
URL:            https://github.com/Maomaokuxs/bytweak
Source0:        %{name}-%{version}.tar.gz
BuildArch:      noarch
Requires:       python3-pyside6
Requires:       python3-libdnf5
Requires:       polkit
Requires:       grub2-tools
Requires:       pciutils
Requires:       flatpak

%description
bytweak 是 Fedora 系统调节工具，提供图形化的系统设置、软件包管理、
硬件信息查看等功能。基于 PySide6 + QML 构建。

%prep
%setup -q

%build
# 无编译步骤

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/bytweak
mkdir -p %{buildroot}%{_datadir}/applications

# 入口脚本
cp app_qml.py %{buildroot}%{_datadir}/bytweak/app_qml.py
chmod 0755 %{buildroot}%{_datadir}/bytweak/app_qml.py
ln -s %{_datadir}/bytweak/app_qml.py %{buildroot}%{_bindir}/bytweak

# QML 与 Python 模块
cp -r modules %{buildroot}%{_datadir}/bytweak/
cp -r qml %{buildroot}%{_datadir}/bytweak/

# 图标
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
cp icons/bytweak.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/bytweak.svg

# 桌面启动文件
cat > %{buildroot}%{_datadir}/applications/bytweak.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=bytweak
Comment=Fedora 系统调节工具
Exec=bytweak
Icon=bytweak
Terminal=false
Categories=System;Settings;
StartupNotify=true
StartupWMClass=bytweak
EOF

%files
%attr(0755, root, root) %{_bindir}/bytweak
%{_datadir}/bytweak/
%{_datadir}/applications/bytweak.desktop
%{_datadir}/icons/hicolor/scalable/apps/bytweak.svg

%changelog
* Tue Oct 13 2026 cai <cai@example.com> - 0.1.0-1
- 首个开发版发布
