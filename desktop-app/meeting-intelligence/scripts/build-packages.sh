#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
DIST_DIR="${PROJECT_DIR}/dist"
BUILD_DIR="$(mktemp -d "${TMPDIR:-/tmp}/meeting-intelligence-build.XXXXXX")"
trap 'rm -rf "${BUILD_DIR}"' EXIT

command -v go >/dev/null 2>&1 || {
  echo "Go 1.22+ is required." >&2
  exit 1
}

mkdir -p "${DIST_DIR}"
cd "${PROJECT_DIR}"

go test ./...

CGO_ENABLED=0 GOOS=windows GOARCH=amd64 go build \
  -trimpath -ldflags="-s -w" \
  -o "${DIST_DIR}/MeetingIntelligence-Windows.exe" .

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Windows launcher built. Run this script on macOS to produce the .pkg." >&2
  exit 0
fi

CGO_ENABLED=0 GOOS=darwin GOARCH=amd64 go build \
  -trimpath -ldflags="-s -w" \
  -o "${BUILD_DIR}/MeetingIntelligence-amd64" .
CGO_ENABLED=0 GOOS=darwin GOARCH=arm64 go build \
  -trimpath -ldflags="-s -w" \
  -o "${BUILD_DIR}/MeetingIntelligence-arm64" .
lipo -create \
  "${BUILD_DIR}/MeetingIntelligence-amd64" \
  "${BUILD_DIR}/MeetingIntelligence-arm64" \
  -output "${BUILD_DIR}/MeetingIntelligence"

APP_ROOT="${BUILD_DIR}/pkg-root/Applications/Meeting Intelligence.app/Contents"
mkdir -p "${APP_ROOT}/MacOS"
install -m 0755 "${BUILD_DIR}/MeetingIntelligence" "${APP_ROOT}/MacOS/MeetingIntelligence"
install -m 0644 "${PROJECT_DIR}/packaging/macos/Info.plist" "${APP_ROOT}/Info.plist"
xattr -cr "${BUILD_DIR}/pkg-root"
find "${BUILD_DIR}/pkg-root" -name '._*' -delete

COPYFILE_DISABLE=1 COPY_EXTENDED_ATTRIBUTES_DISABLE=1 pkgbuild \
  --root "${BUILD_DIR}/pkg-root" \
  --filter '(^|/)\._[^/]*$' \
  --filter '(^|/)\.DS_Store$' \
  --identifier "kr.ipa.meeting-intelligence" \
  --version "2.1.0" \
  --install-location "/" \
  "${DIST_DIR}/MeetingIntelligence-macOS.pkg"

(
  cd "${DIST_DIR}"
  shasum -a 256 MeetingIntelligence-Windows.exe MeetingIntelligence-macOS.pkg > SHA256SUMS
)

echo "Built packages:"
echo "  ${DIST_DIR}/MeetingIntelligence-Windows.exe"
echo "  ${DIST_DIR}/MeetingIntelligence-macOS.pkg"
