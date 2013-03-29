%global php_extdir  %(php-config --extension-dir 2>/dev/null || echo "undefined")
%global __provides_exclude_from ^(%{python_sitelib}/.*\\.so|%{php_extdir}/.*\\.so)$

Name:		groonga
Version:	3.0.2
Release:	0%{?dist}
Summary:	An Embeddable Fulltext Search Engine

Group:		Applications/Text
License:	LGPLv2
URL:		http://groonga.org/
Source0:	http://packages.groonga.org/source/groonga/groonga-%{version}.tar.gz

BuildRequires:	mecab-devel
BuildRequires:	zlib-devel
BuildRequires:	lzo-devel
BuildRequires:	msgpack-devel
BuildRequires:	zeromq-devel
BuildRequires:	libevent-devel
BuildRequires:	python2-devel
BuildRequires:	php-devel
BuildRequires:	libedit-devel
BuildRequires:	pcre-devel
Requires:	%{name}-libs = %{version}-%{release}
Requires:	%{name}-plugin-suggest = %{version}-%{release}
Requires(post):	systemd-units
Requires(preun):	systemd-units
Requires(postun):	systemd-units
ExclusiveArch:		%{ix86} x86_64

%description
Groonga is an embeddable full-text search engine library.  It can
integrate with DBMS and scripting languages to enhance their search
functionality.  It also provides a standalone data store server based
on relational data model.

%package libs
Summary:	Runtime libraries for groonga
Group:		System Environment/Libraries
License:	LGPLv2 and (MIT or GPLv2)
Requires(post):	/sbin/ldconfig
Requires(postun):	/sbin/ldconfig

%description libs
This package contains the libraries for groonga

%package server-common
Summary:	Common packages for the groonga server and the groonga HTTP server
Group:		Applications/Text
License:	LGPLv2
Requires:	%{name} = %{version}-%{release}
Requires(pre):	shadow-utils

%description server-common
This package provides common settings for server use

%package server-gqtp
Summary:	Groonga GQTP server
Group:		Applications/Text
License:	LGPLv2
Requires:	%{name}-server-common = %{version}-%{release}
Requires(pre):	shadow-utils
Requires(post):	/sbin/chkconfig
Requires(preun):	/sbin/chkconfig
Requires(preun):	/sbin/service
Requires(postun):	/sbin/service
Obsoletes:	%{name}-server < 2.0.7-0

%description server-gqtp
This package contains the groonga GQTP server

%package server-http
Summary:	Groonga HTTP server (stable)
Group:		Applications/Text
License:	LGPLv2
Requires:	%{name}-server-common = %{version}-%{release}
Requires:	curl
Requires(pre):	shadow-utils
Requires(post):	/sbin/chkconfig
Requires(preun):	/sbin/chkconfig
Requires(preun):	/sbin/service
Requires(postun):	/sbin/service
Obsoletes:	%{name}-server < 2.0.7-0
Conflicts:	%{name}-httpd

%description server-http
This package contains the groonga HTTP server. It is stable but
has only requisite minimum features.

%package httpd
Summary:	Groonga HTTP server (experimental)
Group:          Applications/Text
License:        LGPLv2 and BSD
Requires:	%{name}-server-common = %{version}-%{release}
Conflicts:	%{name}-server-http

%description httpd
This package contains the groonga HTTP server. It is experimental
but has many features. Because it is based on nginx HTTP server.
It will obsolete groonga-server-http when it is stable.

%package doc
Summary:	Documentation for groonga
Group:		Documentation
License:	LGPLv2 and BSD

%description doc
Documentation for groonga

%package devel
Summary:	Libraries and header files for groonga
Group:		Development/Libraries
Requires:	%{name}-libs = %{version}-%{release}

%description devel
Libraries and header files for groonga

%package tokenizer-mecab
Summary:	MeCab tokenizer for groonga
Group:		Applications/Text
Requires:	%{name}-libs = %{version}-%{release}

%description tokenizer-mecab
MeCab tokenizer for groonga

%package plugin-suggest
Summary:	Suggest plugin for groonga
Group:		Applications/Text
Requires:	%{name}-libs = %{version}-%{release}

%description plugin-suggest
Suggest plugin for groonga

%package munin-plugins
Summary:	Munin plugins for groonga
Group:		Applications/System
Requires:	%{name}-libs = %{version}-%{release}
Requires:	munin-node
Requires(post):	munin-node
Requires(post):	/sbin/service
Requires(postun):	/sbin/service

%description munin-plugins
Munin plugins for groonga

%package python
Summary:	Python language binding for groonga
Group:		Development/Libraries
Requires:	%{name}-libs = %{version}-%{release}

%description python
Python language binding for groonga

%package php
Summary:	PHP language binding for groonga
Group:		Development/Libraries
Requires:	%{name}-libs = %{version}-%{release}

%description php
PHP language binding for groonga


%prep
#% define optflags -O0
%setup -q


%build
%configure \
  --disable-static \
  --with-package-platform=fedora \
  --with-zlib --with-lzo \
  --with-munin-plugins
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool
make %{?_smp_mflags} unitdir="%{_unitdir}"

# build python binding
cd %{_builddir}/%{name}-%{version}/bindings/python/ql
python setup.py config
sed -i.cflags -e 's|^cflags =.*|cflags = []|' setup.py
CFLAGS=-I%{_builddir}/%{name}-%{version}/include
export CFLAGS
LDFLAGS=-L%{_builddir}/%{name}-%{version}/lib/.libs
export LDFLAGS
python setup.py build

# build php binding
cd %{_builddir}/%{name}-%{version}/bindings/php
sed -i.ldflags -e 's|PHP_ADD_LIBRARY_WITH_PATH(groonga, .*)|PHP_ADD_LIBRARY(groonga, GROONGA_SHARED_LIBADD)|' config.m4
phpize
CFLAGS="%{optflags}"
export CFLAGS
LDFLAGS=-L%{_builddir}/%{name}-%{version}/lib/.libs
export LDFLAGS
# --with-groonga is only necessary to avoid error in configure
%configure --disable-static --with-groonga=%{_builddir}/%{name}-%{version}
make %{?_smp_mflags}


%install
make install DESTDIR=$RPM_BUILD_ROOT INSTALL="install -p"
rm $RPM_BUILD_ROOT%{_libdir}/groonga/plugins/*/*.la
rm $RPM_BUILD_ROOT%{_libdir}/*.la

mv $RPM_BUILD_ROOT%{_datadir}/doc/groonga groonga-doc

# Since F17, %{_unitdir} is moved from /lib/systemd/system to
# /usr/lib/systemd/system.  So we need to manually install the service
# file into the new place.  The following should work with < F17,
# though groonga package started using systemd native service since
# F17 and won't be submitted to earlier releases.
mkdir -p $RPM_BUILD_ROOT%{_unitdir}

rm -f $RPM_BUILD_ROOT/lib/systemd/system/groonga-server-http.service
install -p -m 644 data/systemd/fedora/groonga-server-http.service $RPM_BUILD_ROOT%{_unitdir}

rm -f $RPM_BUILD_ROOT/lib/systemd/system/groonga-httpd.service
install -p -m 644 data/systemd/fedora/groonga-httpd.service $RPM_BUILD_ROOT%{_unitdir}

mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/run/groonga
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/groonga/db
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/log/groonga

mv $RPM_BUILD_ROOT%{_datadir}/groonga/munin/ $RPM_BUILD_ROOT%{_datadir}/
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/munin/plugin-conf.d/
cat <<EOC > $RPM_BUILD_ROOT%{_sysconfdir}/munin/plugin-conf.d/groonga
[groonga_*]
  user groonga
  group groonga
  env.PATH %{_bindir}
  env.pid_file %{_localstatedir}/run/groonga/groonga.pid
  env.path %{_localstatedir}/lib/groonga/db/db
  env.host 127.0.0.1
  env.port 10041
  env.log_path %{_localstatedir}/log/groonga/query.log
EOC

# install python binding
cd %{_builddir}/%{name}-%{version}/bindings/python/ql
python setup.py install --root=$RPM_BUILD_ROOT

# install php binding
cd %{_builddir}/%{name}-%{version}/bindings/php
make install INSTALL_ROOT=$RPM_BUILD_ROOT INSTALL="install -p"


%post libs -p /sbin/ldconfig

%post munin-plugins
%{_sbindir}/munin-node-configure --shell --remove-also | grep -e 'groonga_' | sh
[ -f %{_localstatedir}/lock/subsys/munin-node ] && \
	/sbin/service munin-node restart > /dev/null 2>&1
:

%pre server-common
getent group groonga >/dev/null || groupadd -r groonga
getent passwd groonga >/dev/null || \
       useradd -r -g groonga -d %{_localstatedir}/lib/groonga -s /sbin/nologin \
	-c 'groonga' groonga
if [ $1 = 1 ] ; then
	mkdir -p %{_localstatedir}/lib/groonga/db
	groonga -n %{_localstatedir}/lib/groonga/db/db shutdown > /dev/null
	chown -R groonga:groonga %{_localstatedir}/lib/groonga
	mkdir -p %{_localstatedir}/run/groonga
	chown -R groonga:groonga %{_localstatedir}/run/groonga
fi
exit 0

%post server-http
%systemd_post groonga-server-http.service

%preun server-http
%systemd_preun groonga-server-http.service

%postun server-http
%systemd_postun groonga-server-http.service

%post server-gqtp
%systemd_post groonga-server-gqtp.service

%preun server-gqtp
%systemd_preun groonga-server-gqtp.service

%postun server-gqtp
%systemd_postun groonga-server-gqtp.service

%post httpd
%systemd_post groonga-httpd.service

%preun httpd
%systemd_preun groonga-httpd.service

%postun httpd
%systemd_postun groonga-httpd.service

%triggerun -- groonga < 1.3.0-1
/usr/bin/systemd-sysv-convert --save groonga >/dev/null 2>&1 ||:
/bin/systemctl --no-reload enable groonga-server-http.service >/dev/null 2>&1 ||:
/sbin/chkconfig --del groonga >/dev/null 2>&1 || :
/bin/systemctl try-restart groonga-servre-http.service >/dev/null 2>&1 || :

%postun libs -p /sbin/ldconfig

%postun munin-plugins
if [ $1 -eq 0 ]; then
	[ -f %{_localstatedir}/lock/subsys/munin-node ] && \
		/sbin/service munin-node restart >/dev/null 2>&1
	:
fi


%files
%defattr(-,root,root,-)
%{_datadir}/man/man1/*
%{_datadir}/man/*/man1/*
%{_bindir}/groonga
%{_bindir}/groonga-benchmark

%files libs
%defattr(-,root,root,-)
%doc README AUTHORS COPYING
%{_libdir}/*.so.*
%dir %{_libdir}/groonga
%dir %{_libdir}/groonga/plugins
%dir %{_libdir}/groonga/plugins/table
%dir %{_libdir}/groonga/plugins/query_expanders
%{_libdir}/groonga/plugins/table/table.so
%{_libdir}/groonga/plugins/query_expanders/tsv.so
%{_datadir}/groonga/
%config(noreplace) %{_sysconfdir}/groonga/synonyms.tsv

%files server-common

%files server-http
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/groonga/
%config(noreplace) %{_sysconfdir}/sysconfig/groonga-server-http
%dir %{_unitdir}/groonga-server-http.service
%ghost %dir %{_localstatedir}/run/%{name}
%attr(0750,groonga,groonga) %dir %{_localstatedir}/lib/%{name}
%attr(0750,groonga,groonga) %dir %{_localstatedir}/lib/%{name}/db

%files server-gqtp
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/groonga/
%config(noreplace) %{_sysconfdir}/sysconfig/groonga-server-gqtp
%dir %{_unitdir}/groonga-server-gqtp.service
%ghost %dir %{_localstatedir}/run/%{name}
%attr(0750,groonga,groonga) %dir %{_localstatedir}/lib/%{name}
%attr(0750,groonga,groonga) %dir %{_localstatedir}/lib/%{name}/db

%files httpd
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/groonga/httpd/*
%dir %{_unitdir}/groonga-httpd.service
%{_sbindir}/groonga-httpd
%{_sbindir}/groonga-httpd-restart

%files doc
%defattr(-,root,root,-)
%doc README AUTHORS COPYING
%doc groonga-doc/*

%files devel
%defattr(-,root,root,-)
%{_includedir}/groonga/
%{_libdir}/*.so
%{_libdir}/pkgconfig/groonga*.pc

%files tokenizer-mecab
%defattr(-,root,root,-)
%dir %{_libdir}/groonga/plugins/tokenizers
%{_libdir}/groonga/plugins/tokenizers/mecab.so

%files plugin-suggest
%defattr(-,root,root,-)
%dir %{_libdir}/groonga/plugins/suggest
%{_bindir}/groonga-suggest-*
%{_libdir}/groonga/plugins/suggest/suggest.so

%files munin-plugins
%defattr(-,root,root,-)
%{_datadir}/munin/plugins/*
%config(noreplace) %{_sysconfdir}/munin/plugin-conf.d/*

%files python
%defattr(-,root,root,-)
%{python_sitearch}/groongaql*

%files php
%defattr(-,root,root,-)
%{php_extdir}/groonga.so

%changelog
* Fri Mar 29 2013 HAYASHI Kentaro <hayashi@clear-code.com> - 3.0.2-0
- new upstream release.
- fix wrong directory ownership.
- filter not to export private modules.
- add missing groonga-server-gqtp related systemd macros.

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.0.9-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Mon Dec 10 2012 Daiki Ueno <dueno@redhat.com> - 2.0.9-1
- built in Fedora

* Thu Nov 29 2012 HAYASHI Kentaro <hayashi@clear-code.com> - 2.0.9-0
- new upstream release.

* Mon Oct 29 2012 Kouhei Sutou <kou@clear-code.com> - 2.0.8-0
- new upstream release.
- Remove needless "Requires". They will be added by rpmbuild automatically.
  Reported by by Daiki Ueno. Thanks!!!
- Fix license of server-gqtp.
- Fix license of server-http.
- Add more description to server-http and httpd.

* Sat Sep 29 2012 HAYASHI Kentaro <hayashi@clear-code.com> - 2.0.7-0
- new upstream release.
- Split groonga-server package into groonga-server-gqtp and
  groonga-server-http package.

* Wed Aug 29 2012 HAYASHI Kentaro <hayashi@clear-code.com> - 2.0.6-0
- new upstream release.
- Split common tasks for server use into groonga-server-common package.
- groonga-server and groonga-httpd require groonga-server-common package.

* Wed Aug 22 2012 Daiki Ueno <dueno@redhat.com> - 2.0.5-2
- use systemd-rpm macros (#850137)

* Tue Jul 31 2012 Daiki Ueno <dueno@redhat.com> - 2.0.5-1
- built in Fedora

* Sun Jul 29 2012 Kouhei Sutou <kou@clear-code.com> - 2.0.5-0
- new upstream release.

* Mon Jul  2 2012 Daiki Ueno <dueno@redhat.com> - 2.0.4-1
- built in Fedora
- add msgpack-devel to BR

* Fri Jun 29 2012 Kouhei Sutou <kou@clear-code.com> - 2.0.4-0
- new upstream release.
- groonga package does not require groonga-tokenizer-mecab package.

* Mon Jun  4 2012 Daiki Ueno <dueno@redhat.com> - 2.0.3-1
- built in Fedora

* Tue May 29 2012 Kouhei Sutou <kou@clear-code.com> - 2.0.3-0
- new upstream release.

* Tue May  1 2012 Daiki Ueno <dueno@redhat.com> - 2.0.2-1
- built in Fedora

* Sun Apr 29 2012 Kouhei Sutou <kou@clear-code.com> - 2.0.2-0
- new upstream release.
- use libedit.

* Fri Mar 30 2012 Kouhei Sutou <kou@clear-code.com> - 2.0.1-2
- Use shutdown command for stop.

* Fri Mar 30 2012 Kouhei Sutou <kou@clear-code.com> - 2.0.1-1
- Fix bind address argument parameter.
  Patch by Masaharu IWAI. Thanks!!!

* Thu Mar 29 2012 Daiki Ueno <dueno@redhat.com> - 2.0.1-1
- built in Fedora

* Thu Mar 29 2012 Kouhei Sutou <kou@clear-code.com> - 2.0.1-0
- new upstream release.
- ensure removing build directory before installing.
- grntest -> groonga-benchmark.
- remove groonga-tools package.

* Thu Mar  1 2012 Daiki Ueno <dueno@redhat.com> - 2.0.0-1
- built in Fedora

* Wed Feb 29 2012 Kouhei Sutou <kou@clear-code.com> - 2.0.0-0
- new upstream release.
- remove other permission from DB directory.
- use HTTP as the default protocol.
- support effective user and group in systemd.
  Patch by Daiki Ueno. Thanks!!!

* Thu Feb  2 2012 Daiki Ueno <dueno@redhat.com> - 1.3.0-2
- fix systemd service file

* Mon Jan 30 2012 Daiki Ueno <dueno@redhat.com> - 1.3.0-1
- built in Fedora
- migrate groonga-server initscript to systemd service (#781503)
- add groonga-php5.4.patch to compile PHP extension with PHP 5.4

* Sun Jan 29 2012 Kouhei Sutou <kou@clear-code.com> - 1.3.0-0
- new upstream release.
- groonga-server package does not require groonga-munin-plugins package.
  suggested by Masaharu IWAI. Thanks!!!
- groonga package does not require groonga-doc package.
  suggested by Masaharu IWAI. Thanks!!!

* Mon Jan 9 2012 Mamoru Tasaka <mtasaka@fedoraproject.org> - 1.2.9-2
- rebuild against new mecab

* Wed Jan  4 2012 Daiki Ueno <dueno@redhat.com> - 1.2.9-1
- build in fedora

* Thu Dec 29 2011 Kouhei Sutou <kou@clear-code.com> - 1.2.9-0
- new upstream release.

* Tue Nov 29 2011 Daiki Ueno <dueno@redhat.com> - 1.2.8-1
- build in fedora

* Tue Nov 29 2011 Kouhei Sutou <kou@clear-code.com> - 1.2.8-0
- new upstream release.
- enable zlib support.
- enable lzo support.
- add --with-package-platform=redhat configure option to install init script.
- add --with-munin-plugins cofnigure option to install Munin plugins.

* Tue Nov  1 2011 Daiki ueno <dueno@redhat.com> - 1.2.7-1
- build in fedora

* Sat Oct 29 2011 Kouhei Sutou <kou@clear-code.com> - 1.2.7-0
- new upstream release.

* Fri Sep 30 2011 Daiki Ueno <dueno@redhat.com> - 1.2.6-1
- build in fedora

* Thu Sep 29 2011 Kouhei Sutou <kou@clear-code.com> - 1.2.6-0
- new upstream release.

* Mon Sep  5 2011 Daiki Ueno <dueno@redhat.com> - 1.2.5-1
- build in fedora

* Mon Aug 29 2011 Kouhei Sutou <kou@clear-code.com> - 1.2.5-0
- new upstream release.

* Fri Jul 29 2011 Daiki Ueno <dueno@redhat.com> - 1.2.4-1
- build in fedora

* Fri Jul 29 2011 Kouhei Sutou <kou@clear-code.com> - 1.2.4-0
- new upstream release.

* Mon Jul  4 2011 Daiki Ueno <dueno@redhat.com> - 1.2.3-1
- build in fedora
- add ruby to BR

* Wed Jun 29 2011 Kouhei Sutou <kou@clear-code.com> - 1.2.3-0
- new upstream release.
- add a new groong-tools package.

* Tue May 31 2011 Daiki Ueno <dueno@redhat.com> - 1.2.2-1
- build in fedora

* Sun May 29 2011 Kouhei Sutou <kou@clear-code.com> - 1.2.2-0
- new upstream release.
- split server files into groonga-server package.

* Mon May  2 2011 Daiki Ueno <dueno@redhat.com> - 1.2.1-1
- build in fedora.

* Fri Apr 29 2011 Kouhei Sutou <kou@clear-code.com> - 1.2.1-0
- new upstream release.

* Wed Mar 30 2011 Daiki Ueno <dueno@redhat.com> - 1.2.0-1
- build in fedora.

* Tue Mar 29 2011 Kouhei Sutou <kou@clear-code.com> - 1.2.0-0
- new upstream release.

* Thu Feb 17 2011 Daiki Ueno <dueno@redhat.com> - 1.1.0-1
- build in fedora.
- don't require zeromq explicitly.

* Wed Feb 09 2011 Kouhei Sutou <kou@clear-code.com> - 1.1.0-0
- new upstream release.

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.0.8-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Mon Feb  7 2011 Dan Horák <dan[at]danny.cz> - 1.0.8-2
- add ExclusiveArch (atomic primitives implemented only for x86)

* Thu Feb  3 2011 Daiki Ueno <dueno@redhat.com> - 1.0.8-1
- build in fedora.
- don't depend on libevent explicitly.

* Wed Feb 02 2011 Kouhei Sutou <kou@clear-code.com> - 1.0.8-0
- new upstream release.

* Sat Jan 29 2011 Kouhei Sutou <kou@clear-code.com> - 1.0.7-0
- new upstream release.

* Fri Dec 31 2010 Kouhei Sutou <kou@clear-code.com> - 1.0.6-0
- new upstream release

* Wed Dec 29 2010 Kouhei Sutou <kou@clear-code.com> - 1.0.5-0
- new upstream release.

* Mon Nov 29 2010 Kouhei Sutou <kou@clear-code.com> - 1.0.4-1
- new upstream release

* Wed Nov 24 2010 Daiki Ueno <dueno@redhat.com> - 1.0.3-2
- %%ghost /var/run/*.

* Fri Oct 09 2010 Kouhei Sutou <kou@clear-code.com> - 1.0.3-1
- new upstream release.

* Thu Oct  7 2010 Daiki Ueno <dueno@redhat.com> - 1.0.2-7
- own %%_localstatedir/lib/%%name/db.
- use %%_sbindir RPM macro.

* Wed Oct  6 2010 Daiki Ueno <dueno@redhat.com> - 1.0.2-6
- use %%python_sitearch and %%php_extdir macros.
- correct directory ownership for -munin-plugins subpackage.
- supply %%optflags when building PHP binding.
- don't set CGROUP_DAEMON in initscript.

* Tue Oct  5 2010 Daiki Ueno <dueno@redhat.com> - 1.0.2-5
- correct directory ownership for -munin-plugins subpackage.
- make -doc subpackage require -libs.
- correct directory ownership for directories under %%_localstatedir.
- make initscript disabled by default
- move "build process" of Python and PHP bindings to %%build from %%install
- build against Python 2.7
- fix naming of Python and PHP bindings (python-%%{name} to %%{name}-python)

* Mon Oct  4 2010 Daiki Ueno <dueno@redhat.com> - 1.0.2-4
- package Python and PHP bindings.

* Mon Oct  4 2010 Daiki Ueno <dueno@redhat.com> - 1.0.2-3
- fix License.
- pass "-p" to the install command to preserve timestamps.
- use RPM macros %%_initddir, %%_localstatedir, %%_prefix, etc.
- use the standard snippet to creating user/group for groonga; don't
  call userdel/groupdel.
- add missing "Require(foo): bar" for /sbin/service, /sbin/chkconfig,
  /sbin/ldconfig, and /usr/sbin/munin-node-configure.
- fix attributes in %%files.
- correct directory ownership.

* Fri Oct  1 2010 Daiki Ueno <dueno@redhat.com> - 1.0.2-2
- don't require autotools when building
- pass --disable-static to %%configure

* Thu Sep 09 2010 Kouhei Sutou <kou@clear-code.com> - 1.0.2-1
- new upstream release.

* Thu Sep 06 2010 Kouhei Sutou <kou@clear-code.com> - 1.0.1-1
- new upstream release.

* Thu Sep 02 2010 Kouhei Sutou <kou@clear-code.com> - 1.0.0-1
- split packages.

* Tue Aug 24 2010 Daiki Ueno <dueno@redhat.com> - 0.7.6-1
- initial packaging for Fedora
