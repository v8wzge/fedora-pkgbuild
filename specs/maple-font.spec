%global fontname maple-mono-nf-unhinted

Name:           maple-font
Version:        8.0.beta.3
Release:        1%{?dist}
Summary:        Maple Mono Nerd Font, unhinted
License:        OFL-1.1
URL:            https://github.com/subframe7536/maple-font
Source0:        MapleMono-NF-unhinted.zip

BuildArch:      noarch
BuildRequires:  unzip
Requires:       fontconfig

%description
Maple Mono is a monospaced font with programming ligatures. This package
contains the Nerd Font patched, unhinted variant, including beta releases.

%prep
rm -rf %{name}-%{version}
mkdir -p %{name}-%{version}
unzip -q %{SOURCE0} -d %{name}-%{version}
cd %{name}-%{version}

%build
# Fonts are pre-built upstream.

%install
cd %{name}-%{version}
install -d %{buildroot}%{_datadir}/fonts/%{fontname}
install -pm644 *.ttf %{buildroot}%{_datadir}/fonts/%{fontname}/

install -d %{buildroot}%{_docdir}/%{name}
install -pm644 LICENSE.txt %{buildroot}%{_docdir}/%{name}/LICENSE.txt
install -pm644 README.md %{buildroot}%{_docdir}/%{name}/README.md

%post
fc-cache -f %{_datadir}/fonts/%{fontname} >/dev/null 2>&1 || :

%postun
if [ $1 -eq 0 ]; then
    fc-cache -f %{_datadir}/fonts/%{fontname} >/dev/null 2>&1 || :
fi

%files
%license %{_docdir}/%{name}/LICENSE.txt
%doc %{_docdir}/%{name}/README.md
%dir %{_datadir}/fonts/%{fontname}
%{_datadir}/fonts/%{fontname}/*.ttf

%changelog
* Sat Nov 21 2026 v8wzge <v8wzge@users.noreply.github.com> - 8.0~beta.3-1
- Automated build from the latest upstream release, including prereleases
