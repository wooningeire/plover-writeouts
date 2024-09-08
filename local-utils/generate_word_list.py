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
    from plover_writeouts.lib.alignment.match_sophemes import match_sophemes
    from plover_writeouts.lib.stenophoneme.Stenophoneme import Stenophoneme

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

    
    out_path = Path(__file__).parent.parent / "local-utils/out/lapwing.hatchery"
    out_path.parent.mkdir(exist_ok=True, parents=True)

    def generate():
        sophemes_json = []

        with open(Path(__file__).parent.parent / "local-utils/data/unilex", "r", encoding="utf-8") as file:
            with open(out_path, "w+", encoding="utf-8") as out_file:
                while len(line := file.readline()) > 0:
                    translation, _, _, transcription, _, _ = line.split(":")
                    if translation not in reverse_lapwing_dict: continue

                    for outline_steno in reverse_lapwing_dict[translation]:
                        # out_file.write(" ".join(str(sopheme) for sopheme in match_sophemes(translation, transcription, outline_steno)) + "\n")

                        sophemes_json.append(tuple(sopheme.to_dict() for sopheme in match_sophemes(translation, transcription, outline_steno)))

                json.dump(sophemes_json, out_file)

    print(f"Generating entries…")
    duration = timeit.timeit(generate, number=1)
    print(f"Finished (took {duration} s)")

if __name__ == "__main__":
    _setup_plover()
    _main()