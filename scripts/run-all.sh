#!/bin/bash
#
#

set -e

t3(){
	echo ">>> t3 $@"
	poetry run t3 "$@"
}

test_fsync(){
	t3 fsync ls /Downloads
	echo -n hello > a.txt
	t3 fsync push a.txt /Downloads
	t3 fsync pull /Downloads/a.txt b.txt
	if ! cmp a.txt b.txt
	then
		echo ">>> ERROR: a.txt != b.txt"
		exit 1
	fi
	rm a.txt b.txt
}

test_app(){
	t3 app install --help
	t3 app uninstall --help
	t3 app launch com.apple.Preferences
	t3 app kill --help
	t3 app list
	t3 app current
	t3 app info com.apple.stocks
	t3 app ps
}

t3 list
t3 developer
t3 exec version
t3 screenshot a.png && rm a.png
t3 reboot -h

test_fsync
test_app



