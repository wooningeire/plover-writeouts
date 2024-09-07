def test__match_graphemes_to_writeout_chords__baseline():
    from plover_writeouts.lib.alignment.match_ortho_steno import match_chars_to_chords

    assert (
        str(match_chars_to_chords("emilio", "E/PHEU/HREU/KWROE"))
        == "(e.E, m.PH, i.EU, l.HR, i.EU/KWR, o.OE)"
    )

def test__match_graphemes_to_writeout_chords__silent_letters():
    from plover_writeouts.lib.alignment.match_ortho_steno import match_chars_to_chords

    assert (
        str(match_chars_to_chords("pinecone", "PAOEUPB/KO*EPB"))
        == "(p.P, i.AOEU, n.-PB, e., c.K, o.OE, n.-PB, e.)"
    )

def test__match_graphemes_to_writeout_chords__silent_chords():
    from plover_writeouts.lib.alignment.match_ortho_steno import match_chars_to_chords

    assert (
        str(match_chars_to_chords("pupal", "PAOUP/KWRAL"))
        == "(p.P, u.AOU, p.-P, .KWR, a.A, l.-L)"
    )

def test__match_graphemes_to_writeout_chords__asterisk_chords():
    from plover_writeouts.lib.alignment.match_ortho_steno import match_chars_to_chords

    assert (
        str(match_chars_to_chords("zenith", "STKPWE/TPH*EUT"))
        == "(z.STKPW, e.E, n.TPH, i.EU, th.*T)"
    )

def test__match_graphemes_to_writeout_chords__length_stress_test():
    from plover_writeouts.lib.alignment.match_ortho_steno import match_chars_to_chords

    assert (
        str(match_chars_to_chords("supercalifragilisticexpialidocious", "SAOU/PER/KA/HREU/TPRA/SKWREU/HREU/STEUS/KWREBGS/PEU/KWRA/HREU/TKOERB/KWRUS"))
        == "(s.S, u.AOU, p.P, e.E, r.-R, c.K, a.A, l.HR, i.EU, f.TP, r.R, a.A, g.SKWR, i.EU, l.HR, i.EU, s.S, t.T, i.EU, c.-S, .KWR, e.E, x.-BGS, p.P, i.EU/KWR, a.A, l.HR, i.EU, d.TK, o.OE, ci.-RB/KWR, ou.U, s.-S)"
    )