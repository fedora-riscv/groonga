%global php_extdir  %(php-config --extension-dir 2>/dev/null || echo "undefined")
# Bug1799474 workaround
%define _legacy_common_support 1

Name:		groonga
Version:	10.0.8
Release:	%autorelease
Summary:	An Embeddable Fulltext Search Engine

License:	LGPLv2
URL:		https://groonga.org/
Source0:	https://packages.groonga.org/source/groonga/groonga-%{version}.tar.gz

BuildRequires:	gcc-c++
BuildRequires:	gcc
BuildRequires:	mecab-devel
BuildRequires:	zlib-devel
BuildRequires:	lz4-devel
BuildRequires:	msgpack-devel
BuildRequires:	zeromq-devel
BuildRequires:	libevent-devel
BuildRequires:	libedit-devel
BuildRequires:	pcre-devel
BuildRequires:	systemd-rpm-macros
BuildRequires:	libstemmer-devel
BuildRequires:	openssl-devel
BuildRequires:	re2c
BuildRequires:	libzstd-devel
BuildRequires:	rapidjson-devel
BuildRequires: make
Requires:	%{name}-libs = %{version}-%{release}
Requires:	%{name}-plugin-suggest = %{version}-%{release}
Obsoletes:	%{name}-python < 6.0.9-1
Obsoletes:	%{name}-php < 6.0.9-1

%description
Groonga is an embeddable full-text search engine library.  It can
integrate with DBMS and scripting languages to enhance their search
functionality.  It also provides a standalone data store server based
on relational data model.

%package libs
Summary:	Runtime libraries for Groonga
License:	LGPLv2 and (MIT or GPLv2)

%description libs
This package contains the libraries for Groonga

%package server-common
Summary:	Common packages for the Groonga server and the Groonga HTTP server
License:	LGPLv2
Requires:	%{name} = %{version}-%{release}
Requires(pre):	shadow-utils

%description server-common
This package provides common settings for server use

%package server-gqtp
Summary:	Groonga GQTP server
License:	LGPLv2
Requires:	%{name}-server-common = %{version}-%{release}
Requires(pre):	shadow-utils
Requires(post):	systemd
Requires(preun):	systemd
Obsoletes:	%{name}-server < 2.0.7-0

%description server-gqtp
This package contains the Groonga GQTP server

%package httpd
Summary:	Groonga HTTP server
License:	LGPLv2 and BSD
Requires:	%{name}-server-common = %{version}-%{release}
Provides:	%{name}-server-http = %{version}-%{release}
Obsoletes:	%{name}-server-http <= 4.0.7-2

%description httpd
This package contains the Groonga HTTP server. It has many features
because it is based on nginx HTTP server.

%package doc
Summary:	Documentation for Groonga
License:	LGPLv2 and BSD

%description doc
Documentation for Groonga

%package devel
Summary:	Libraries and header files for Groonga
Requires:	%{name}-libs = %{version}-%{release}

%description devel
Libraries and header files for Groonga

%package tokenizer-mecab
Summary:	MeCab tokenizer for Groonga
Requires:	%{name}-libs = %{version}-%{release}

%description tokenizer-mecab
MeCab tokenizer for Groonga

%package plugin-suggest
Summary:	Suggest plugin for Groonga
Requires:	%{name}-libs = %{version}-%{release}

%description plugin-suggest
Suggest plugin for Groonga

%package plugin-token-filters
Summary:	Token filters plugin for Groonga
Requires:	%{name}-libs = %{version}-%{release}

%description plugin-token-filters
Token filters plugins for Groonga which provides
stop word and stemming features.

%package munin-plugins
Summary:	Munin plugins for Groonga
Requires:	%{name}-libs = %{version}-%{release}
Requires:	munin-node
Requires(post):	munin-node

%description munin-plugins
Munin plugins for Groonga

%prep
#% define optflags -O0
%setup -q
%build
%configure \
  --disable-static \
  --enable-mruby \
  --with-package-platform=fedora \
  --with-zlib --with-lz4 \
  --with-munin-plugins

sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|' libtool
make %{?_smp_mflags} unitdir="%{_unitdir}"
# Exit %%build section explicitly not to execute unexpected configure script again
exit 0

%install
make install DESTDIR=$RPM_BUILD_ROOT INSTALL="install -p"
find %{buildroot} -type f -name "*.la" -delete
rm $RPM_BUILD_ROOT%{_sysconfdir}/logrotate.d/groonga-server-http

mv $RPM_BUILD_ROOT%{_datadir}/doc/groonga groonga-doc

# Since F17, %%{_unitdir} is moved from /lib/systemd/system to
# /usr/lib/systemd/system.  So we need to manually install the service
# file into the new place.  The following should work with < F17,
# though Groonga package started using systemd native service since
# F17 and won't be submitted to earlier releases.
mkdir -p $RPM_BUILD_ROOT%{_unitdir}

# Remove obsolete files
rm -f $RPM_BUILD_ROOT%{_sysconfdir}/sysconfig/groonga-server-http
rm -f $RPM_BUILD_ROOT%{_unitdir}/groonga-server-http.service

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

%ldconfig_scriptlets libs

%post munin-plugins
%{_sbindir}/munin-node-configure --shell --remove-also | grep -e 'groonga_' | sh
[ -f %{_localstatedir}/lock/subsys/munin-node ] && \
	systemctl restart munin-node > /dev/null 2>&1
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

%postun munin-plugins
if [ $1 -eq 0 ]; then
	[ -f %{_localstatedir}/lock/subsys/munin-node ] && \
		systemctl restart munin-node >/dev/null 2>&1
	:
fi


%files
%{_bindir}/groonga
%{_bindir}/groonga-benchmark
%{_bindir}/grndb

%files libs
%license COPYING
%doc README.md
%{_libdir}/*.so.*
%dir %{_libdir}/groonga
%dir %{_libdir}/groonga/plugins
%dir %{_libdir}/groonga/plugins/functions
%dir %{_libdir}/groonga/plugins/query_expanders
%dir %{_libdir}/groonga/plugins/normalizers
%dir %{_libdir}/groonga/plugins/tokenizers
%dir %{_libdir}/groonga/plugins/ruby
%dir %{_libdir}/groonga/plugins/sharding
%dir %{_libdir}/groonga/scripts/ruby
%dir %{_libdir}/groonga/scripts/ruby/command_line
%dir %{_libdir}/groonga/scripts/ruby/context
%dir %{_libdir}/groonga/scripts/ruby/expression_rewriters
%dir %{_libdir}/groonga/scripts/ruby/expression_tree
%dir %{_libdir}/groonga/scripts/ruby/groonga-log
%dir %{_libdir}/groonga/scripts/ruby/initialize
%dir %{_libdir}/groonga/scripts/ruby/logger
%dir %{_libdir}/groonga/scripts/ruby/query_logger
%{_libdir}/groonga/plugins/functions/*.so
%{_libdir}/groonga/plugins/query_expanders/tsv.so
%{_libdir}/groonga/plugins/ruby/*.rb
%{_libdir}/groonga/plugins/*.rb
%{_libdir}/groonga/plugins/sharding/*.rb
%{_libdir}/groonga/scripts/ruby/*.rb
%{_libdir}/groonga/scripts/ruby/command_line/*.rb
%{_libdir}/groonga/scripts/ruby/context/*.rb
%{_libdir}/groonga/scripts/ruby/groonga-log/*.rb
%{_libdir}/groonga/scripts/ruby/expression_rewriters/*.rb
%{_libdir}/groonga/scripts/ruby/expression_tree/*.rb
%{_libdir}/groonga/scripts/ruby/initialize/*.rb
%{_libdir}/groonga/scripts/ruby/logger/*.rb
%{_libdir}/groonga/scripts/ruby/query_logger/*.rb
%{_datadir}/groonga/
%config(noreplace) %{_sysconfdir}/groonga/synonyms.tsv

%files server-common
%config(noreplace) %{_sysconfdir}/tmpfiles.d/groonga.conf

%files server-gqtp
%config(noreplace) %{_sysconfdir}/groonga/
%config(noreplace) %{_sysconfdir}/sysconfig/groonga-server-gqtp
%config(noreplace) %{_sysconfdir}/logrotate.d/groonga-server-gqtp
%{_unitdir}/groonga-server-gqtp.service
%ghost %dir /run/%{name}
%attr(0755,groonga,groonga) %dir %{_localstatedir}/lib/%{name}
%attr(0755,groonga,groonga) %dir %{_localstatedir}/lib/%{name}/db

%files httpd
%config(noreplace) %{_sysconfdir}/groonga/httpd/*
%config(noreplace) %{_sysconfdir}/sysconfig/groonga-httpd
%config(noreplace) %{_sysconfdir}/logrotate.d/groonga-httpd
%{_unitdir}/groonga-httpd.service
%{_sbindir}/groonga-httpd
%{_sbindir}/groonga-httpd-restart
%ghost %dir /run/%{name}
%attr(0755,groonga,groonga) %dir %{_localstatedir}/lib/%{name}
%attr(0755,groonga,groonga) %dir %{_localstatedir}/lib/%{name}/db

%files doc
%doc README.md COPYING
%doc groonga-doc/*

%files devel
%{_includedir}/groonga/
%{_libdir}/*.so
%{_libdir}/pkgconfig/groonga*.pc

%files tokenizer-mecab
%{_libdir}/groonga/plugins/tokenizers/mecab.so

%files plugin-token-filters
%{_libdir}/groonga/plugins/token_filters/stop_word.so
%{_libdir}/groonga/plugins/token_filters/stem.so

%files plugin-suggest
%{_bindir}/groonga-suggest-*
%{_libdir}/groonga/plugins/suggest/suggest.so

%files munin-plugins
%{_datadir}/munin/plugins/*
%config(noreplace) %{_sysconfdir}/munin/plugin-conf.d/*

%changelog
%autochangelog
