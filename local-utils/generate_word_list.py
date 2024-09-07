from pathlib import Path
import json
import re
from dataclasses import dataclass
import timeit
    
from plover import system
from plover.config import DEFAULT_SYSTEM_NAME
from plover.registry import registry


def _setup_plover():
    registry.update()
    system.setup(DEFAULT_SYSTEM_NAME)

@dataclass(frozen=True)
class _Affix:
    text: str
    is_prefix: bool


def _main():
    from plover_writeouts.lib.match_sophemes import match_sophemes

    with open(Path(__file__).parent.parent / "local-utils/data/lapwing-base.json", "r", encoding="utf-8") as file:
        lapwing_dict = json.load(file)
    
    # reverse_lapwing_affixes_dict: dict[str, set[str]] = {}
    reverse_lapwing_dict: dict[str, list[str]] = {}
    for outline_steno, translation in lapwing_dict.items():
        # if "{^" in translation or "^}" in translation:
        #     if translation in reverse_lapwing_affixes_dict:
        #         reverse_lapwing_affixes_dict[_Affix(re.sub(translation, ))].add(outline_steno) 

        #     continue

        if not translation.isalnum():
            continue

        n_strokes = len(outline_steno.split("/"))
        if translation in reverse_lapwing_dict and n_strokes == len(reverse_lapwing_dict[translation][0].split("/")):
            reverse_lapwing_dict[translation].append(outline_steno)
            continue
        elif translation in reverse_lapwing_dict and n_strokes < len(reverse_lapwing_dict[translation][0].split("/")):
            continue

        reverse_lapwing_dict[translation] = [outline_steno]

    
    out_path = Path(__file__).parent.parent / "local-utils/out/lapwing"
    out_path.parent.mkdir(exist_ok=True, parents=True)

    def generate():
        with open(Path(__file__).parent.parent / "local-utils/data/unilex", "r", encoding="utf-8") as file:
            with open(out_path, "w+", encoding="utf-8") as out_file:
                while True:
                    line = file.readline()
                    if len(line) == 0: break

                    translation, _, _, transcription, _, _ = line.split(":")
                    if translation not in reverse_lapwing_dict: continue

                    for outline_steno in reverse_lapwing_dict[translation]:
                        # phonos = match_keysymbols_to_writeout_chords(tuple(phonetic_keysymbols), outline_steno)
                        # sophemes = match_chars_to_phonos(translation, phonos)

                        out_file.write(" ".join(str(sopheme) for sopheme in match_sophemes(translation, transcription, outline_steno)) + "\n")

                        # out_file.write(" ".join(f"{sopheme.ortho}.({' '.join(
                        #     keysymbol
                        #     for stenophoneme in sopheme.stenophonemes
                        #     for keysymbol in stenophoneme.data
                        # )})" for sopheme in sophemes) + "\n")
                    
    print(f"Generating entries…")
    duration = timeit.timeit(generate, number=1)
    print(f"Finished (took {duration} s)")

if __name__ == "__main__":
    _setup_plover()
    _main()