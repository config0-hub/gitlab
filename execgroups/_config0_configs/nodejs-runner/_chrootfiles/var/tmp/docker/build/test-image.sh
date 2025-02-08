#!/bin/sh

printTestHeader() {
    echo "$1"
    echo '----------'
}

printTestFooter() {
    echo '----------'
    echo 'Done!'
    echo
}

echo

# ---------------------------------------------------------------------------- #
# Verify `root` is the active user.                                            #
# ---------------------------------------------------------------------------- #
printTestHeader 'Checking the curent user (should be root)...'
echo $(whoami)
[ $(whoami) = 'root' ] || exit 1
printTestFooter

# ---------------------------------------------------------------------------- #
# Verify `node` is available.                                                  #
# ---------------------------------------------------------------------------- #
printTestHeader 'Testing Node.js...'
node --version
[ $? -eq 0 ] || exit 1
printTestFooter

# ---------------------------------------------------------------------------- #
# Test if the downloaded gitlab-runner binary file is indeed a binary and not, #
# for example, an HTML page representing S3's internal server error message or #
# something like that.                                                         #
# ---------------------------------------------------------------------------- #
printTestHeader 'Testing GitLab Runner...'
gitlab-runner --version
[ $? -eq 0 ] || exit 1
printTestFooter
