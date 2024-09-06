def test__match_graphemes_to_writeout_chords__baseline():
    from plover_writeouts.lib.match_sophemes import match_sophemes

    assert (
        " ".join(str(sopheme) for sopheme in match_sophemes("zygote", " { z * ae . g ou t } ", "STKPWAOEU/TKPWOET"))
        == "z.z[STKPW] y.ae[AOEU] g.g[TKPW] o.ou[OE] t.t[-T] e."
    )