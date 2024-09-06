def test__match_graphemes_to_writeout_chords__baseline():
    from plover_writeouts.lib.match_sophemes import match_sophemes

    assert (
        " ".join(str(sopheme) for sopheme in match_sophemes("zygote", " { z * ae . g ou t } ", "STKPWAOEU/TKPWOET"))
        == "z.z[Z] y.ae[II] g.g[G] o.ou[OO] t.t[T] e."
    )