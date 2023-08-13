"""
author: Kanta Yamaoka
"""
from pathlib import Path
import polib
import pandas as pd
from google.cloud import translate_v2 as translate
import yaml


def extract_untranslated_msgids_per_section(po_file_path: Path, occurence_substring: str, ignore_code_snippets=True, verbose_log=False) -> list[str]:
    """Loads po file, and extracts untranslated msgids from only specified sections. Finally provides a list of untranslated msgids.
    """
    po: polib.POFile = polib.pofile(po_file_path)
    match_count: int = 0
    untranslated_msgids: list[str] = []
    for entry in po.untranslated_entries():
        # Occurences can be multiple, but this naive approach works for most of scenarios.
        first_occurence, _ = entry.occurrences[0]
        # Filters an entry by translation source path
        if occurence_substring in first_occurence:
            # Filters an entry by (a) if having a code snipet or not, and (b) if empty or not
            if (ignore_code_snippets and "```" in entry.msgid) or (len(entry.msgid.strip()) == 0):
                continue
            match_count += 1
            if verbose_log:
                print(
                    f"---{match_count}: [[Untranslated msgid from {first_occurence}]]---")
                print(entry.msgid)
            untranslated_msgids.append(entry.msgid)
    assert match_count > 0, "No hits. Something went wrong or no need to use this script."
    return untranslated_msgids


def translate_text_with_google_cloud(target: str, text: str) -> str:
    """
    https://cloud.google.com/translate/docs/basic/translating-text?hl=ja
    """
    translate_client = translate.Client()
    if isinstance(text, bytes):
        text = text.decode("utf-8")
    result = translate_client.translate(
        text, target_language=target, source_language='en')
    return result["translatedText"]


def main():
    # Configurations (depends on your local computer and which section you want to translate)
    po_file_path = Path("/Users/kantay/oss/comprehensive-rust/po/ja.po")
    translation_pairs_yaml_path = Path(
        "/Users/kantay/oss/py-cloud-translate-rust/translation_pairs.yaml")
    section_of_interest: str = "src/concurrency/"
    translation_target: str = 'ja'

    # Extracts msgids of your interest
    msgids: list[str] = extract_untranslated_msgids_per_section(
        po_file_path, section_of_interest)

    # Creates pairs of msgid and msgsrc with Google Cloud Translate API
    translation_pairs: list[dict] = []
    for msgid in msgids:
        translation: str = translate_text_with_google_cloud(
            translation_target, msgid)
        translation_pairs.append({"src": msgid, "translation": translation})
    df_pairs = pd.DataFrame(translation_pairs)

    # Finally, saves as yaml (then you'll manually adjust translations with Poedit)
    with open(translation_pairs_yaml_path, 'w') as file:
        yaml.dump({'result': df_pairs.to_dict(orient='records')},
                  file, default_flow_style=False, allow_unicode=True)


if __name__ == "__main__":
    main()
