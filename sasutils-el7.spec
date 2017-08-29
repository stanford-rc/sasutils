Name:           sasutils
Version:        0.3.9
Release:        1%{?dist}
Summary:        Serial Attached SCSI (SAS) utilities

License:        ASL 2.0
URL:            https://github.com/stanford-rc/sasutils
Source0:        https://files.pythonhosted.org/packages/source/s/%{name}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools
Requires:       python%{python3_pkgversion}-setuptools
Requires:       sg3_utils
Requires:       smp_utils

%{?python_provide:%python_provide python-sasutils}

%description
sasutils is a set of command-line tools and a Python library to ease the
administration of Serial Attached SCSI (SAS) fabrics.

%prep
%setup -q

%build
%py3_build

%install
%py3_install
install -d %{buildroot}/%{_mandir}/man1
install -p -m 0644 doc/man/man1/sas_counters.1 %{buildroot}/%{_mandir}/man1/
install -p -m 0644 doc/man/man1/sas_devices.1 %{buildroot}/%{_mandir}/man1/
install -p -m 0644 doc/man/man1/sas_discover.1 %{buildroot}/%{_mandir}/man1/
install -p -m 0644 doc/man/man1/ses_report.1 %{buildroot}/%{_mandir}/man1/

%files
%{_bindir}/sas_counters
%{_bindir}/sas_devices
%{_bindir}/sas_discover
%{_bindir}/sas_mpath_snic_alias
%{_bindir}/sas_sd_snic_alias
%{_bindir}/ses_report
%{python3_sitelib}/sasutils/
%{python3_sitelib}/sasutils-*-py?.?.egg-info
%{_mandir}/man1/sas_counters.1*
%{_mandir}/man1/sas_devices.1*
%{_mandir}/man1/sas_discover.1*
%{_mandir}/man1/ses_report.1*
%doc README.rst
%license LICENSE.txt

%changelog
* Tue Aug 29 2017 Stephane Thiell <sthiell@stanford.edu> 0.3.9-1
- update version

* Tue Aug 29 2017 Stephane Thiell <sthiell@stanford.edu> 0.3.8-3
- build for Python 3.4 in EPEL7

* Tue Aug 22 2017 Stephane Thiell <sthiell@stanford.edu> 0.3.8-2
- always remove shebang from Python modules
- removed unwanted Group tag
- removed useless/duplicate Provides tag

* Fri Aug 18 2017 Stephane Thiell <sthiell@stanford.edu> 0.3.8-1
- added man pages

* Wed Aug 16 2017 Stephane Thiell <sthiell@stanford.edu> 0.3.5-1
- packaging improvements

* Tue Jul  4 2017 Stephane Thiell <sthiell@stanford.edu> 0.3.4-1
- build against python3 only
- install LICENSE.txt file
- use python_provide macro and update to follow Fedora packaging guidelines

* Sat May 20 2017 Stephane Thiell <sthiell@stanford.edu> 0.3.3-1
- update version (bug fixes)

* Wed Mar 29 2017 Mikhail Lesin <mlesin@gmail.com> 0.3.2-1
- Python 3 port
- DM support
- 4K devices sizefix

* Mon Feb 20 2017 Stephane Thiell <sthiell@stanford.edu> 0.3.1-1
- update version

* Sun Feb 19 2017 Stephane Thiell <sthiell@stanford.edu> 0.3.0-1
- update version

* Fri Dec  9 2016 Stephane Thiell <sthiell@stanford.edu> 0.2.5-1
- update version

* Mon Dec  5 2016 Stephane Thiell <sthiell@stanford.edu> 0.2.4-1
- update version

* Tue Nov  8 2016 Stephane Thiell <sthiell@stanford.edu> 0.2.3-1
- update version

* Mon Oct 31 2016 Stephane Thiell <sthiell@stanford.edu> 0.2.1-1
- update version

* Mon Oct 17 2016 Stephane Thiell <sthiell@stanford.edu> 0.1.7-1
- inception
