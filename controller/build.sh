#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT
git clone --quiet --depth 1 --branch v3.5.7 https://github.com/dhun2666/scrcpy-client-for-android.git "$work/client"
cd "$work/client"
[[ "$(git rev-parse HEAD)" == 889bae6a92172f4fb8fa19ca173e330ef64e2abf ]]
git apply "$root/controller/upstream.patch"
install -m 0644 "$root"/controller/Pocket*.kt app/src/main/java/com/scrcpy/remote/ui/
install -m 0644 "$root/profiles/screen-control.json" app/src/main/assets/pocket-screen.json
install -m 0644 "$root/controller/tests/PocketStorageTest.kt" app/src/test/java/com/scrcpy/remote/
bash gradlew :app:testDebugUnitTest --tests '*PocketStorageTest' --tests '*AdbSyncTest' --tests '*ScrcpyFileTransferTest' --tests '*FileTransferTest'
bash gradlew :app:assembleDebug
install -Dm644 app/build/outputs/apk/debug/app-debug.apk "$root/build/pocket-nas-home.apk"
