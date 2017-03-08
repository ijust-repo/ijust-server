#! /bin/bash

echo "hello!!!"
set -e

export COMPILED_DIR="/tmp/compiled"


if [ ! -d "$COMPILED_DIR" ]; then
	mkdir "$COMPILED_DIR"
fi

if [ -z "$CODE_PATH" ]; then
	echo "please export CODE_PATH environmet"
	exit 1
fi

if [ -z "$TESTCASE_DIR" ]; then
	echo "please export TESTCASE_DIR files directory"
	exit 1
fi

if [ -z "$LOG_DIR" ]; then
	export LOG_DIR="/tmp/outputs"
fi

if [ ! -d "$LOG_DIR" ]; then
		mkdir "$LOG_DIR"
	fi

if [ -z "$TAG" ]; then 
	export TAG="$HOST_NAME"
fi

echo "begin compiling"


if [ -s "$CODE_PATH" ]; then

	/bin/bash "$PL_SCRIPT_DIR/compile.sh" 2> "$LOG_DIR/compile.err"

	echo "compiled successfully"
	echo "begin tests"
	
	for tc in "$TESTCASE_DIR"/*
	do
		if [ -s "$tc" ]; then
			NAME="$(basename $tc | cut -d'.' -f 1)"
			START=$(date +%s.%N)
			timeout -k "$TIME_LIMIT"s "$TIME_LIMIT"s /bin/bash "$PL_SCRIPT_DIR/run.sh" < "$tc" 1> "$LOG_DIR/$NAME.out" 2> "$LOG_DIR/$NAME.err"
			END=$(date +%s.%N)
			DIFF=$(echo "$END - $START" | bc)
			echo $DIFF > "$LOG_DIR/$NAME.stt"
		fi
	done
	echo "end of tests"

else
	echo "there is nothing for compile"
fi

if [ -d "COMPILED_DIR" ]; then
	echo "begin of remove compiled file"
	rm -rf "$COMPILED_DIR/*"
fi

echo "end"
