Summary:	Java Mail API
Name:		javamail
Version:	1.4.3
Release:	16
Group:		Development/Java
License:	CDDL or GPLv2 with exceptions
Url:		http://java.sun.com/products/javamail/
# Parent POM
Source0:	http://download.java.net/maven/2/com/sun/mail/all/%{version}/all-%{version}.pom
# POMs and source files for things that get built
Source1:	http://download.java.net/maven/2/javax/mail/mail/%{version}/mail-%{version}-sources.jar
Source2:	http://download.java.net/maven/2/javax/mail/mail/%{version}/mail-%{version}.pom
Source3:	http://download.java.net/maven/2/com/sun/mail/dsn/%{version}/dsn-%{version}-sources.jar
Source4:	http://download.java.net/maven/2/com/sun/mail/dsn/%{version}/dsn-%{version}.pom
# Additional POMs for things that are provided by the monolithic mail.jar
Source5:	http://download.java.net/maven/2/javax/mail/mailapi/%{version}/mailapi-%{version}.pom
Source6:	http://download.java.net/maven/2/com/sun/mail/imap/%{version}/imap-%{version}.pom
Source7:	http://download.java.net/maven/2/com/sun/mail/pop3/%{version}/pop3-%{version}.pom
Source8:	http://download.java.net/maven/2/com/sun/mail/smtp/%{version}/smtp-%{version}.pom
# http://kenai.com/projects/javamail/sources/mercurial/content/parent-distrib/pom.xml?raw=true
Source9:	%{name}-parent-distrib.pom
# Maven dependency map bits
Source10:	javamail.fragment
# Add additional OSGi information to manifest of mail.jar
Patch0:	%{name}-add-osgi-info.patch
# Remove Maven plugins we don't have yet
# Remove unavailable-on-Fedora dependencies from pom.xml
Patch1:	%{name}-cleanup-poms.patch
BuildArch:	noarch

BuildRequires:	jpackage-utils
BuildRequires:	java-1.6.0-openjdk-devel
Requires:	jpackage-utils
# Adapted from the classpathx-mail (and JPackage glassfish-javamail) Provides
Provides:	javamail-monolithic = 0:%{version}

%description
The JavaMail API provides a platform-independent and protocol-independent
framework to build mail and messaging applications.

%package javadoc
Summary:	Javadoc for %{name}
Group:		Development/Java
Requires:	jpackage-utils >= 0:1.7.5

%description javadoc
%{summary}.

%prep
%setup -c -T
mkdir -p mail dsn

(cd mail && jar xvf %SOURCE1 && cp %SOURCE2 ./pom.xml)
(cd dsn && jar xvf %SOURCE3 && cp %SOURCE4 ./pom.xml)

%patch0 -p1

for sub in *; do
	pushd $sub
	mkdir -p src/main/java src/main/resources
	mv META-INF src/main/resources
	[ -e com ] && mv com src/main/java
	[ -e javax ] && mv javax src/main/java
	popd
done

cp %SOURCE0 ./pom.xml
mkdir poms
cp %SOURCE5 %SOURCE6 %SOURCE7 %SOURCE8 %SOURCE9 poms

%patch1 -p1

# Convert license file to UTF-8
for file in mail/src/main/resources/META-INF/*.txt; do
	iconv -f ISO-8859-1 -t UTF-8 -o $file.new $file && \
	touch -r $file $file.new && \
	mv $file.new $file
done


%build
export JAVA_HOME=%_prefix/lib/jvm/java-1.6.0
# We build stuff manually because we don't want a circular build dependency.
# Can't build a full-featured version of ant without javamail
PACKAGES=""
for sub in mail dsn; do
	mkdir -p $sub/target/javadoc
	cd $sub/src/main/java
	for i in `find . -type d |sed -e 's,\./,,;s,/,.,g;s,META-INF,,'`; do
		[ "$i" = "." ] && continue
		[ "$i" = "com" ] && continue
		[ "$i" = "javax" ] && continue
		PACKAGES="$PACKAGES $i"
	done
	cp -a ../resources/META-INF .
	find . -name "*.java" |xargs $JAVA_HOME/bin/javac
	find . -name "*.class" |xargs $JAVA_HOME/bin/jar cf ../../../target/$sub.jar META-INF
	export CLASSPATH=$CLASSPATH:`pwd`/../../../target/$sub.jar
	cd ../../../..
done
mkdir doc
cd doc
cp -a ../mail/src/main/java/* .
cp -a ../dsn/src/main/java/com/sun/mail/* com/sun/mail/
javadoc -d ../target/javadoc $PACKAGES

%install
install -d -m 755 %{buildroot}%{_javadir}/%{name}
install -d -m 755 %{buildroot}%{_mavenpomdir}
install -d -m 755 p %{buildroot}%{_javadocdir}/%{name}

install -pm 644 pom.xml %{buildroot}/%{_mavenpomdir}/JPP.%{name}-all.pom

# Install everything
for sub in mail dsn; do
	install -m 644 $sub/target/$sub.jar %{buildroot}%{_javadir}/%{name}/$sub.jar
done
cp -pr target/javadoc/* %{buildroot}%{_javadocdir}/%{name}

install -d -m 755 %{buildroot}%{_javadocdir}/%{name}
install -m 644 mail/pom.xml %{buildroot}/%{_mavenpomdir}/JPP.%{name}-mail.pom
install -m 644 dsn/pom.xml %{buildroot}/%{_mavenpomdir}/JPP.%{name}-dsn.pom

# Install the remaining POMs
for sub in mailapi imap pop3 smtp; do
 install -m 644 poms/$sub-%{version}.pom \
	 %{buildroot}/%{_mavenpomdir}/JPP.%{name}-$sub.pom
done

install -m 644 poms/%{name}-parent-distrib.pom \
	%{buildroot}/%{_mavenpomdir}/JPP.%{name}-parent-distrib.pom

mkdir -p %{buildroot}%_mavendepmapfragdir
cp %SOURCE10 %{buildroot}%_mavendepmapfragdir/%{name}

%files
%doc mail/src/main/resources/META-INF/LICENSE.txt mail/overview.html
%{_javadir}/%{name}
%{_mavendepmapfragdir}/*
%{_mavenpomdir}/*.pom

%files javadoc
%{_javadocdir}/%{name}

