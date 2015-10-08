%global php_extdir  %(php-config --extension-dir 2>/dev/null || echo "undefined")
%global __provides_exclude_from ^(%{python_sitelib}/.*\\.so|%{php_extdir}/.*\\.so)$
%global _hardened_build 1

Name:		groonga
Version:	5.0.8
Release:	1%{?dist}
Summary:	An Embeddable Fulltext Search Engine

Group:		Applications/Text
License:	LGPLv2
URL:		http://groonga.org/
Source0:	http://packages.groonga.org/source/groonga/groonga-%{version}.tar.gz

BuildRequires:	mecab-devel
BuildRequires:	zlib-devel
BuildRequires:	lz4-devel
BuildRequires:	msgpack-devel
BuildRequires:	zeromq-devel
BuildRequires:	libevent-devel
BuildRequires:	python2-devel
BuildRequires:	php-devel
BuildRequires:	libedit-devel
BuildRequires:	pcre-devel
BuildRequires:	systemd
Requires:	%{name}-libs = %{version}-%{release}
Requires:	%{name}-plugin-suggest = %{version}-%{release}
Requires(post):	systemd
Requires(preun):	systemd
Requires(postun):	systemd

%description
Groonga is an embeddable full-text search engine library.  It can
integrate with DBMS and scripting languages to enhance their search
functionality.  It also provides a standalone data store server based
on relational data model.

%package libs
Summary:	Runtime libraries for Groonga
Group:		System Environment/Libraries
License:	LGPLv2 and (MIT or GPLv2)
Requires(post):	/sbin/ldconfig
Requires(postun):	/sbin/ldconfig

%description libs
This package contains the libraries for Groonga

%package server-common
Summary:	Common packages for the Groonga server and the Groonga HTTP server
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
This package contains the Groonga GQTP server

%package server-http
Summary:	Groonga HTTP server (transitional)
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
This is a transitional package to groonga-httpd.

%package httpd
Summary:	Groonga HTTP server
Group:          Applications/Text
License:        LGPLv2 and BSD
Requires:	%{name}-server-common = %{version}-%{release}
Provides:	%{name}-server-http = %{version}-%{release}
Obsoletes:	%{name}-server-http <= 4.0.7-2

%description httpd
This package contains the Groonga HTTP server. It has many features
because it is based on nginx HTTP server.

%package doc
Summary:	Documentation for Groonga
Group:		Documentation
License:	LGPLv2 and BSD

%description doc
Documentation for Groonga

%package devel
Summary:	Libraries and header files for Groonga
Group:		Development/Libraries
Requires:	%{name}-libs = %{version}-%{release}

%description devel
Libraries and header files for Groonga

%package tokenizer-mecab
Summary:	MeCab tokenizer for Groonga
Group:		Applications/Text
Requires:	%{name}-libs = %{version}-%{release}

%description tokenizer-mecab
MeCab tokenizer for Groonga

%package plugin-suggest
Summary:	Suggest plugin for Groonga
Group:		Applications/Text
Requires:	%{name}-libs = %{version}-%{release}

%description plugin-suggest
Suggest plugin for Groonga

%package plugin-token-filters
Summary:	Token filters plugin for Groonga
Group:		Applications/Text
Requires:	%{name}-libs = %{version}-%{release}

%description plugin-token-filters
Token filters plugins for Groonga which provides
stop word and stemming features.

%package munin-plugins
Summary:	Munin plugins for Groonga
Group:		Applications/System
Requires:	%{name}-libs = %{version}-%{release}
Requires:	munin-node
Requires(post):	munin-node
Requires(post):	/sbin/service
Requires(postun):	/sbin/service

%description munin-plugins
Munin plugins for Groonga

%package python
Summary:	Python language binding for Groonga
Group:		Development/Libraries
Requires:	%{name}-libs = %{version}-%{release}

%description python
Python language binding for Groonga

%package php
Summary:	PHP language binding for Groonga
Group:		Development/Libraries
Requires:	%{name}-libs = %{version}-%{release}

%description php
PHP language binding for Groonga


%prep
#% define optflags -O0
%setup -q

%build
%configure \
  --disable-static \
  --enable-mruby \
  --with-package-platform=fedora \
  --with-zlib --with-lz4 \
  --with-munin-plugins \
  --without-libstemmer

sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|' libtool
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
# though Groonga package started using systemd native service since
# F17 and won't be submitted to earlier releases.
mkdir -p $RPM_BUILD_ROOT%{_unitdir}

rm -f $RPM_BUILD_ROOT/lib/systemd/system/groonga-server-http.service
install -p -m 644 data/systemd/fedora/groonga-server-http.service $RPM_BUILD_ROOT%{_unitdir}

rm -f $RPM_BUILD_ROOT/lib/systemd/system/groonga-httpd.service
install -p -m 644 data/systemd/fedora/groonga-httpd.service $RPM_BUILD_ROOT%{_unitdir}

mkdir -p $RPM_BUILD_ROOT/run/groonga
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/lib/groonga/db
mkdir -p $RPM_BUILD_ROOT%{_localstatedir}/log/groonga
mkdir -p $RPM_BUILD_ROOT%{_libdir}/groonga/plugins/normalizers

mv $RPM_BUILD_ROOT%{_datadir}/groonga/munin/ $RPM_BUILD_ROOT%{_datadir}/
mkdir -p $RPM_BUILD_ROOT%{_sysconfdir}/munin/plugin-conf.d/
cat <<EOC > $RPM_BUILD_ROOT%{_sysconfdir}/munin/plugin-conf.d/groonga
[groonga_*]
  user groonga
  group groonga
  env.PATH %{_bindir}
  env.database_path %{_localstatedir}/lib/groonga/db/db
  env.host 127.0.0.1

  env.http_host 127.0.0.1
  env.http_port 10041
  env.http_database_path %{_localstatedir}/lib/groonga/db/db
  env.http_pid_path /run/groonga/groonga-http.pid
  env.http_query_log_path %{_localstatedir}/log/groonga/query-http.log

  env.httpd_host 127.0.0.1
  env.httpd_port 10041
  env.httpd_database_path %{_localstatedir}/lib/groonga/db/db
  env.httpd_pid_path /run/groonga/groonga-httpd.pid
  env.httpd_query_log_path %{_localstatedir}/log/groonga/httpd/groonga-query.log

  env.gqtp_host 127.0.0.1
  env.gqtp_port 10043
  env.gqtp_database_path %{_localstatedir}/lib/groonga/db/db
  env.gqtp_pid_path /run/groonga/groonga-gqtp.pid
  env.gqtp_query_log_path %{_localstatedir}/log/groonga/query-gqtp.log
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
	mkdir -p /run/groonga
	chown -R groonga:groonga /run/groonga
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
%{_bindir}/grndb

%files libs
%defattr(-,root,root,-)
%doc README.md COPYING
%{_libdir}/*.so.*
%dir %{_libdir}/groonga
%dir %{_libdir}/groonga/plugins
%dir %{_libdir}/groonga/plugins/functions
%dir %{_libdir}/groonga/plugins/table
%dir %{_libdir}/groonga/plugins/query_expanders
%dir %{_libdir}/groonga/plugins/normalizers
%dir %{_libdir}/groonga/plugins/tokenizers
%dir %{_libdir}/groonga/plugins/token_filters
%dir %{_libdir}/groonga/plugins/suggest
%dir %{_libdir}/groonga/plugins/ruby
%dir %{_libdir}/groonga/plugins/sharding
%dir %{_libdir}/groonga/scripts/ruby
%dir %{_libdir}/groonga/scripts/ruby/command_line
%dir %{_libdir}/groonga/scripts/ruby/context
%dir %{_libdir}/groonga/scripts/ruby/initialize
%dir %{_libdir}/groonga/scripts/ruby/logger
%dir %{_libdir}/groonga/scripts/ruby/query_logger
%{_libdir}/groonga/plugins/functions/vector.so
%{_libdir}/groonga/plugins/table/table.so
%{_libdir}/groonga/plugins/query_expanders/tsv.so
%{_libdir}/groonga/plugins/sharding.rb
%{_libdir}/groonga/plugins/ruby/*.so
%{_libdir}/groonga/plugins/sharding/*.rb
%{_libdir}/groonga/scripts/ruby/*.rb
%{_libdir}/groonga/scripts/ruby/command_line/*.rb
%{_libdir}/groonga/scripts/ruby/context/*.rb
%{_libdir}/groonga/scripts/ruby/initialize/*.rb
%{_libdir}/groonga/scripts/ruby/logger/*.rb
%{_libdir}/groonga/scripts/ruby/query_logger/*.rb
%{_datadir}/groonga/
%config(noreplace) %{_sysconfdir}/groonga/synonyms.tsv

%files server-common

%files server-http
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/groonga/
%config(noreplace) %{_sysconfdir}/sysconfig/groonga-server-http
%{_unitdir}/groonga-server-http.service
%ghost %dir /run/%{name}
%attr(0755,groonga,groonga) %dir %{_localstatedir}/lib/%{name}
%attr(0755,groonga,groonga) %dir %{_localstatedir}/lib/%{name}/db

%files server-gqtp
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/groonga/
%config(noreplace) %{_sysconfdir}/sysconfig/groonga-server-gqtp
%{_unitdir}/groonga-server-gqtp.service
%ghost %dir /run/%{name}
%attr(0755,groonga,groonga) %dir %{_localstatedir}/lib/%{name}
%attr(0755,groonga,groonga) %dir %{_localstatedir}/lib/%{name}/db

%files httpd
%defattr(-,root,root,-)
%config(noreplace) %{_sysconfdir}/groonga/httpd/*
%{_unitdir}/groonga-httpd.service
%{_sbindir}/groonga-httpd
%{_sbindir}/groonga-httpd-restart
%ghost %dir /run/%{name}
%attr(0755,groonga,groonga) %dir %{_localstatedir}/lib/%{name}
%attr(0755,groonga,groonga) %dir %{_localstatedir}/lib/%{name}/db

%files doc
%defattr(-,root,root,-)
%doc README.md COPYING
%doc groonga-doc/*

%files devel
%defattr(-,root,root,-)
%{_includedir}/groonga/
%{_libdir}/*.so
%{_libdir}/pkgconfig/groonga*.pc

%files tokenizer-mecab
%defattr(-,root,root,-)
%{_libdir}/groonga/plugins/tokenizers/mecab.so

%files plugin-token-filters
%defattr(-,root,root,-)
%{_libdir}/groonga/plugins/token_filters/stop_word.so

%files plugin-suggest
%defattr(-,root,root,-)
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
* Fri Oct 9 2015 HAYASHI Kentaro <hayashi@clear-code.com> - 5.0.8-1
- new upstream release.

* Tue Sep 1 2015 HAYASHI Kentaro <hayashi@clear-code.com> - 5.0.7-1
- new upstream release.

* Sat Aug 1 2015 Masafumi Yokoyama <yokoyama@clear-code.com> - 5.0.6-1
- new upstream release.

* Mon Jun 29 2015 Masafumi Yokoyama <yokoyama@clear-code.com> - 5.0.5-1
- new upstream release.

* Tue Jun 23 2015 Thomas Spura <tomspur@fedoraproject.org> - 5.0.4-3
- rebuilt for new zeromq 4.1.2

* Wed Jun 17 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 5.0.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Tue Jun 2 2015 HAYASHI Kentaro <hayashi@clear-code.com> - 5.0.4-1
- new upstream release.

* Thu Apr 30 2015 HAYASHI Kentaro <hayashi@clear-code.com> - 5.0.3-1
- new upstream release.
- add vector plugin.

* Sun Apr 19 2015 Peter Robinson <pbrobinson@fedoraproject.org> 5.0.2-2
- Drop ExclusiveArch, atomic primitives now supported on all arches

* Wed Apr 1 2015 HAYASHI Kentaro <hayashi@clear-code.com> - 5.0.2-1
- new upstream release.
- drop fix-crash-by-missing-libedit-initialization.patch
  This patch is already imported into upstream.

* Mon Mar 30 2015 HAYASHI Kentaro <hayashi@clear-code.com> - 5.0.1-1
- new upstream release.
- add a patch to fix crash in standalone mode.
  fix-crash-by-missing-libedit-initialization.patch

* Wed Feb 25 2015 HAYASHI Kentaro <hayashi@clear-code.com> - 5.0.0-1
- new upstream release.
- enable mruby by default.

* Wed Jan 14 2015 HAYASHI Kentaro <hayashi@clear-code.com> - 4.1.0-1
- new upstream release.

* Tue Jan 6 2015 HAYASHI Kentaro <hayashi@clear-code.com> - 4.0.9.1-1
- new upstream release.
- remove needless 'g' option to remove rpath.
- use /run/groonga to fix dir-or-file-in-var-run error.

* Mon Dec 1 2014 HAYASHI Kentaro <hayashi@clear-code.com> - 4.0.8-1
- new upstream release.
- make groonga-httpd as default HTTP server package
- drop groonga-server-http, it is just changed to transitional package

* Tue Nov 4 2014 HAYASHI Kentaro <hayashi@clear-code.com> - 4.0.7-1
- new upstream release.
- drop lzo support.
- add lz4 support.
- add groonga-plugin-token-filters sub package.

* Mon Oct 6 2014 HAYASHI Kentaro <hayashi@clear-code.com> - 4.0.6-1
- new upstream release.
- drop a needless patch to fix groonga-httpd service startup failure.

* Mon Sep 8 2014 HAYASHI Kentaro <hayashi@clear-code.com> - 4.0.5-1
- new upstream release.
- add a patch to fix groonga-httpd service startup failure.
  add-missing-mkdir-for-groonga-httpd-service.patch

* Sat Aug 16 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.0.4-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Thu Jul 31 2014 HAYASHI Kentaro <hayashi@clear-code.com> - 4.0.4-1
- new upstream release.

* Tue Jul 1 2014 HAYASHI Kentaro <hayashi@clear-code.com> - 4.0.3-1
- new upstream release.

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 4.0.2-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Fri May 30 2014 HAYASHI Kentaro <hayashi@clear-code.com> - 4.0.2-1
- new upstream release.

* Mon Mar 31 2014 HAYASHI Kentaro <hayashi@clear-code.com> - 4.0.1-1
- new upstream release.

* Mon Feb 10 2014 HAYASHI Kentaro <hayashi@clear-code.com> - 4.0.0-1
- new upstream release.

* Mon Feb 3 2014 HAYASHI Kentaro <hayashi@clear-code.com> - 3.1.2-1
- new upstream release.

* Tue Dec 31 2013 HAYASHI Kentaro <hayashi@clear-code.com> - 3.1.1-1
- new upstream release.

* Fri Nov 29 2013 HAYASHI Kentaro <hayashi@clear-code.com> - 3.1.0-1
- new upstream release.

* Tue Oct 29 2013 HAYASHI Kentaro <hayashi@clear-code.com> - 3.0.9-1
- new upstream release.

* Sun Sep 29 2013 HAYASHI Kentaro <hayashi@clear-code.com> - 3.0.8-1
- new upstream release.

* Thu Aug 29 2013 HAYASHI Kentaro <hayashi@clear-code.com> - 3.0.7-1
- new upstream release.

* Wed Jul 31 2013 HAYASHI Kentaro <hayashi@clear-code.com> - 3.0.6-2
- unify own directories of plugins.

* Mon Jul 29 2013 HAYASHI Kentaro <hayashi@clear-code.com> - 3.0.6-1
- new upstream release.

* Sat Jun 29 2013 HAYASHI Kentaro <hayashi@clear-code.com> - 3.0.5-1
- new upstream release.

* Wed May 29 2013 HAYASHI Kentaro <hayashi@clear-code.com> - 3.0.4-1
- new upstream release.

* Mon Apr 29 2013 HAYASHI Kentaro <hayashi@clear-code.com> - 3.0.3-1
- new upstream release.
- enable the PIE compiler flags. 

* Fri Mar 29 2013 HAYASHI Kentaro <hayashi@clear-code.com> - 3.0.2-1
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

* Sat Oct 09 2010 Kouhei Sutou <kou@clear-code.com> - 1.0.3-1
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

* Mon Sep 06 2010 Kouhei Sutou <kou@clear-code.com> - 1.0.1-1
- new upstream release.

* Thu Sep 02 2010 Kouhei Sutou <kou@clear-code.com> - 1.0.0-1
- split packages.

* Tue Aug 24 2010 Daiki Ueno <dueno@redhat.com> - 0.7.6-1
- initial packaging for Fedora
