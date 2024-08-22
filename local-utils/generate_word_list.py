from pathlib import Path
import json
import timeit
    
from plover import system
from plover.config import DEFAULT_SYSTEM_NAME
from plover.registry import registry
from plover.steno import Stroke

def _setup_plover():
    registry.update()
    system.setup(DEFAULT_SYSTEM_NAME)

_NONPHONETIC_KEYSYMBOLS = tuple("*~-.<>{}#=$")

def _main():
    from plover_writeouts.lib.match_chars import match_chars_to_writeout_chords
    from plover_writeouts.lib.match_keysymbols import match_keysymbols_to_writeout_chords
    from plover_writeouts.lib.Sopheme import Sopheme

    transcription = "{ * o k . s I2 d $}.> ~ ae z >.> @r r"
    outline = "O/KPEU/TKAOEU/STKPWER"

    phonetic_keysymbols = tuple(filter(lambda keysymbol: not any(ch in keysymbol for ch in _NONPHONETIC_KEYSYMBOLS), transcription.split(" ")))

    stenographemes = match_chars_to_writeout_chords("oxidizer", outline)
    stenophonemes = match_keysymbols_to_writeout_chords(phonetic_keysymbols, outline)

    print(stenographemes)
    print(stenophonemes)


    sophemes: list[Sopheme] = []

    last_added_stenophoneme_index = -1
    
    last_added_key_index = -1


    for stenographeme in stenographemes:
        target_end_index = last_added_key_index + stenographeme.n_keys()
        current_stenophonemes = []

        if last_added_stenophoneme_index < len(stenophonemes) - 1:
            stenophoneme_index = last_added_stenophoneme_index + 1
            stenophonemes_key_end_index = last_added_key_index + stenophonemes[stenophoneme_index].n_keys()

            while stenophonemes_key_end_index <= target_end_index:
                last_added_key_index = stenophonemes_key_end_index
                if stenophoneme_index >= 0:
                    current_stenophonemes.append(stenophonemes[stenophoneme_index])
                last_added_stenophoneme_index = stenophoneme_index


                if stenophoneme_index == len(stenophonemes) - 1: break

                stenophoneme_index += 1
                stenophonemes_key_end_index += stenophonemes[stenophoneme_index].n_keys()
        
        sophemes.append(Sopheme(stenographeme.data, tuple(current_stenophonemes)))

    
    print(sophemes)
    print(Sopheme.join_word(sophemes))



    # with open(Path(__file__).parent.parent / "local-utils/data/lapwing-base.json", "r", encoding="utf-8") as file:
    #     lapwing_dict = json.load(file)
    
    # # lapwing_affixes_dict: dict[str, set[str]] = {}
    # reverse_lapwing_dict: dict[str, list[str]] = {}
    # for outline_steno, translation in lapwing_dict.items():
    #     # if "{^" in translation or "^}" in translation:
    #     #     if translation in reverse_lapwing_affixes_dict:
    #     #         reverse_lapwing_affixes_dict[translation].add(outline_steno) 

    #     #     continue

    #     if not translation.isalnum():
    #         continue

    #     n_strokes = len(outline_steno.split("/"))
    #     if translation in reverse_lapwing_dict and n_strokes == len(reverse_lapwing_dict[translation][0].split("/")):
    #         reverse_lapwing_dict[translation].append(outline_steno)
    #         continue
    #     elif translation in reverse_lapwing_dict and n_strokes < len(reverse_lapwing_dict[translation][0].split("/")):
    #         continue

    #     reverse_lapwing_dict[translation] = [outline_steno]

    
    # out_path = Path(__file__).parent.parent / "local-utils/out/lapwing"
    # out_path.parent.mkdir(exist_ok=True, parents=True)
    # def generate():
    #     with open(out_path, "w+", encoding="utf-8") as file:
    #         for translation, outline_stenos in reverse_lapwing_dict.items():
    #             for outline_steno in outline_stenos:
    #                 file.write(" ".join(str(sopheme) for sopheme in match_chars_to_writeout_chords(translation, outline_steno)) + "\n")
                    
    # print(f"Generating entries…")
    # duration = timeit.timeit(generate, number=1)
    # print(f"Finished (took {duration} s)")

if __name__ == "__main__":
    _setup_plover()
    _main()