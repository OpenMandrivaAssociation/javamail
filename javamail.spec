%define uversion %(echo %{version} |sed -e 's,\\.,_,g')

Name:           javamail
Version:	1_6_2
Release:        2
Summary:        Java Mail API
License:        CDDL or GPLv2 with exceptions
URL:            https://javaee.github.io/javamail/
BuildArch:      noarch

Source0:        https://github.com/javaee/javamail/archive/JAVAMAIL-%{uversion}.tar.gz
Patch0:		javamail-ant-openjdk-12.patch
Patch1:		javamail-1.6.2-gimap-compile.patch
Patch2:		javamail-1.6.2-ant-modular.patch

BuildRequires:	jdk-current
BuildRequires:	javapackages-local
BuildRequires:	javax.activation
BuildRequires:	ant

%description
The JavaMail API provides a platform-independent and protocol-independent
framework to build mail and messaging applications.


%package javadoc
Summary:        Javadoc for %{name}

%description javadoc
%{summary}.


%prep
%autosetup -p1 -n javamail-JAVAMAIL-%{uversion}

if [ -e dsn/src/main/java/module-info.java ]; then
	echo "Lack of module-info in DSN module has been fixed upstream."
	echo "Please remove the workaround."
	exit 1
fi
cat >dsn/src/main/java/module-info.java <<EOF
module com.sun.mail.dsn {
	exports com.sun.mail.dsn;
	requires java.mail;
	requires java.logging;
	requires java.desktop;
}
EOF

%build
# Unfortunately, the ant build files are hopelessly outdated to the point
# of being unusable (incorrect module handling) and we can't use maven because
# we don't like circular dependencies -- so we have to do things manually

. /etc/profile.d/90java.sh

mkdir out

cd mail/src/main/java
cp ../../../../mailapi/src/main/java/module-info.java .
cp ../resources/javax/mail/*.java javax/mail/
find javax com/sun/mail/util com/sun/mail/auth com/sun/mail/handlers -name "*.java" |xargs javac -d ../../../../out/mailapi -p %{_javadir}/modules module-info.java
javadoc -d ../../../../out/doc-java.mail com.sun.mail.util com.sun.mail.auth com.sun.mail.handlers -p %{_javadir}/modules --add-modules=java.activation -html4
cd ../../../../out/mailapi
cp -a ../../mail/src/main/resources/META-INF .
jar cf ../java.mail-%{version}.jar module-info.class javax com/sun/mail/util com/sun/mail/auth com/sun/mail/handlers META-INF
cd ../..
cp pom.xml out/java.mail-%{version}.pom

for i in imap smtp pop3; do
	EXTRAS=""
	[ "$i" = "imap" ] && EXTRAS=com/sun/mail/iap
	cd mail/src/main/java
	cp -f ../../../../$i/src/main/java/module-info.java .
	find com/sun/mail/$i $EXTRAS -name "*.java" |xargs javac -d ../../../../out/$i -p %{_javadir}/modules:../../../../out module-info.java
	javadoc -d ../../../../out/doc-$i com.sun.mail.$i $(echo $EXTRAS |sed -e 's,/,.,g') -p %{_javadir}/modules:../../../../out --add-modules=java.activation,java.mail -html4
	cd ../../../../out/$i
	jar cf ../$i-%{version}.jar .
	cd ../..
	cp $i/pom.xml out/$i-%{version}.pom
done

for i in dsn gimap; do
	cd $i/src/main/java
	find . -name "*.java" |xargs javac -d ../../../../out/$i -p %{_javadir}/modules:../../../../out
	cd ../../../../out/$i
	jar cf ../$i-%{version}.jar .
	cd ../..
	cp $i/pom.xml out/$i-%{version}.pom
done

for i in out/*.jar; do
	jar i $i
done


%install
mkdir -p %{buildroot}%{_javadir}/modules %{buildroot}%{_mavenpomdir} %{buildroot}%{_javadocdir}
cp out/*.jar %{buildroot}%{_javadir}/modules/
for i in java.mail imap smtp pop3 dsn gimap; do
	ln -s modules/$i-%{version}.jar %{buildroot}%{_javadir}/
	ln -s modules/$i-%{version}.jar %{buildroot}%{_javadir}/$i.jar
	cp out/$i-%{version}.pom %{buildroot}%{_mavenpomdir}/
	[ -d out/doc-$i ] && cp -a out/doc-$i %{buildroot}%{_javadocdir}/$i
	%add_maven_depmap $i-%{version}.pom $i-%{version}.jar
done

%files
%{_javadir}/*.jar
%{_javadir}/modules/*.jar
%{_mavenpomdir}/*
%{_datadir}/maven-metadata/*.xml

%files javadoc
%{_javadocdir}/*
