#!/bin/bash

test_abs_path=$(realpath --no-symlinks ${BASH_SOURCE})
test_abs_dir=$(dirname ${test_abs_path})
test_filename=$(basename ${BASH_SOURCE})

RED="\033[0;31m"
GREEN="\033[0;32m"
NC="\033[0m"

log_path=${test_abs_dir}/test.log
recipe_path=${test_abs_dir}/../../recipes/boognish-brown
# The following is a creative commons licensed song
url=https://www.youtube.com/watch?v=B4RqeAvE7iA
workspace=${test_abs_dir}/workspace
set_c=
set_l=
log_to_console=

OUTFILE=test.mp3

USAGE="USAGE: $test_filename [-h] [-c|-l LOG] [-r RECIPE] [-u URL]
  -h           Print help message
  -c           Log to console [Default: Disabled]
  -l LOG       Path to log file [Default: ${log_path}]
  -r RECIPE    Path to a recipe file [Default: ${recipe_path}]
  -u URL       Youtube URL for source song [Default: ${url}]
"

while getopts ":chl:o:r:u:" opt; do
    case ${opt} in
	c )
            set_c=1
            log_to_console=1
            ;;
        h )
            printf "$USAGE"
            exit 0
            ;;
        l )
            set_l=1
            log_path=$(realpath --no-symlinks $OPTARG)
            ;;
        r )
            recipe_path=$(realpath --no-symlinks $OPTARG)
            ;;
        u )
            url=$OPTARG
            ;;
        \? )
            echo "Invalid option: $OPTARG" 1>&2
            printf "$USAGE" 1>&2
            exit 1
            ;;
    esac
done
shift $((OPTIND -1))

if [ ! -z $set_c ] && [ ! -z $set_l ]; then
    echo "The -c and -l parameters are mutually exclusive. Only set one."
    printf "$USAGE"
    exit 1
fi

quietly() {
    "$@" > /dev/null 2>&1
}

log() {
    if [ -z $log_to_console ]; then
        "$@" >> ${log_path} 2>&1
    else
	"$@"
    fi
}

setup() {
    mkdir -p ${workspace}
}

cleanup() {
    rm -rf ${workspace}
}

handle_fail() {
    cleanup
    log echo "Failed"
    echo -e "${RED}Failed${NC}"
    exit 1
}

try() {
    "$@" || handle_fail
}


# Perform setup
try log setup
try log pushd ${workspace}

# Run brownify
try log brownify ${url} ${workspace}/${OUTFILE} --recipe-file ${recipe_path}

# See if a file was successfully created
if [ -f ${workspace}/${OUTFILE} ]; then
    log echo "Output mp3 file created successfully"
else
    handle_fail
fi

# Clean up
try log popd
try log cleanup

echo -e "${GREEN}Success${NC}"
