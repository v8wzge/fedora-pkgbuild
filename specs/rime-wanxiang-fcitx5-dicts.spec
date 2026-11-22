%global rime_data %{_datadir}/rime-data

Name:           rime-wanxiang-fcitx5-dicts
Version:        18.2.0
Release:        1%{?dist}
Summary:        Wanxiang Rime dictionary tables for Fcitx5
License:        CC-BY-4.0
URL:            https://github.com/amzxyz/rime-wanxiang
Source0:        base-dicts.zip
Source1:        rime-wanxiang-LICENSE

BuildArch:      noarch
BuildRequires:  unzip
Requires:       librime-octagram
Conflicts:      rime-wanxiang-ibus-dicts

%description
Dictionary and grammar model tables for the Wanxiang Pinyin Rime schema on
Fcitx5 Rime. These are the Base dictionaries published on the upstream nightly
dictionary release and are consumed by rime-wanxiang-fcitx5-base.

%prep
rm -rf wanxiang-dicts
mkdir wanxiang-dicts
unzip -q %{SOURCE0} -d wanxiang-dicts

%build
# Upstream ships pre-built dictionary data.

%install
rm -rf %{buildroot}
install -d %{buildroot}%{rime_data}/dicts
cp -a wanxiang-dicts/. %{buildroot}%{rime_data}/dicts/
install -d %{buildroot}%{_licensedir}/%{name}
install -pm644 %{SOURCE1} %{buildroot}%{_licensedir}/%{name}/LICENSE

%files
%license %{_licensedir}/%{name}/LICENSE
%{rime_data}/dicts/
%{rime_data}/dicts/*

%changelog
* Sun Nov 22 2026 v8wzge <v8wzge@users.noreply.github.com> - 18.2.0-1
- Automated build from the upstream Base dictionary release
