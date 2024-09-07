def test__match_sophemes__baseline():
    from plover_writeouts.lib.match_sophemes import match_sophemes

    assert (
        " ".join(str(sopheme) for sopheme in match_sophemes("acquiesce", " { ~ a . k w ii . * e s } ", "A/KWEU/KWRES"))
        == "a.a!2[A] cq.k[K] u.w[W] i.ii[EE] [[KWR]] e.e!1[E] sc.s[S] e."
    )

    assert (
        " ".join(str(sopheme) for sopheme in match_sophemes("zygote", " { z * ae . g ou t } ", "STKPWAOEU/TKPWOET"))
        == "z.z[Z] y.ae!1[II] g.g[G] o.ou[OO] t.t[T] e."
    )

def test__match_sophemes__keysymbol_cluster_with_gap():
    from plover_writeouts.lib.match_sophemes import match_sophemes

    assert (
        " ".join(str(sopheme) for sopheme in match_sophemes("ation", " { ee sh n } ", "AEUGS"))
        == "a.ee[AA] (ti.sh o. n.n)[[-GS]]"
    )

def test__match_sophemes__shortest_forms():
    from plover_writeouts.lib.match_sophemes import match_sophemes

    assert (
        " ".join(sopheme.shortest_form() for sopheme in match_sophemes("yet", " { y * e t } ", "KWHET"))
        == "y e.e!1[E] t"
    )
