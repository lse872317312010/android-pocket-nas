#!/usr/bin/env bash
# Run inside an empty writable directory on the target, using a verified SSH alias.
set -euo pipefail
if [[ $# != 1 ]]; then
  echo "Usage: $0 SSH_CONFIG_ALIAS | --local" >&2
  exit 2
fi
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
cd "$work"
remote="pocket-nas-test-${work##*.}"
if [[ $1 == --local ]]; then
  mkdir server
  args=(-D "/usr/lib/openssh/sftp-server -d $work/server")
elif [[ $1 =~ ^[a-zA-Z0-9][a-zA-Z0-9_.-]*$ ]]; then
  args=(-o BatchMode=yes -o StrictHostKeyChecking=yes "$1")
else
  echo "Expected an SSH config alias" >&2
  exit 2
fi
dd if=/dev/urandom of=sample.bin bs=1000000 count=100 status=none
echo "Temporary remote directory: $remote"
sftp -b - "${args[@]}" <<BATCH
mkdir $remote
cd $remote
put sample.bin uploaded.bin
rename uploaded.bin renamed.bin
ls -l renamed.bin
get renamed.bin received.bin
rm renamed.bin
cd ..
rmdir $remote
BATCH
sha256sum sample.bin received.bin
cmp sample.bin received.bin
echo "Verified 100,000,000-byte round trip, rename and cleanup."
