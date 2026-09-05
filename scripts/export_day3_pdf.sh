#!/usr/bin/env bash
# Print/export the exact final PPT with a Korean-capable font configuration.
set -euo pipefail
day3_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
day3_default_soffice="/Users/sungjae-cha/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/override/soffice"
day3_soffice="${DAY3_SOFFICE:-$day3_default_soffice}"
day3_pptx="$day3_root/slides/IPA_LLM_Agent_업무자동화_Day3_2026_CODEX_CLI.pptx"
if [[ ! -x "$day3_soffice" ]]; then
  echo "PDF_EXPORTER_NOT_FOUND: set DAY3_SOFFICE to the bundled LibreOffice launcher."
  exit 1
fi
if [[ -f /opt/homebrew/etc/fonts/fonts.conf && -z "${FONTCONFIG_FILE:-}" ]]; then
  export FONTCONFIG_FILE=/opt/homebrew/etc/fonts/fonts.conf
fi
mkdir -p "$day3_root/output/pdf"
"$day3_soffice" --headless --convert-to pdf --outdir "$day3_root/output/pdf" "$day3_pptx"
echo "PDF exported. Check embedded fonts with pdffonts and render every page before distribution."
