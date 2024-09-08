import json

def test__Sopheme__parse_sopheme_seq():
    from plover_writeouts.lib.sopheme.parse import parse_sopheme_seq
    from plover_writeouts.lib.sopheme.Sopheme import Sopheme, Orthokeysymbol, Keysymbol
    from plover_writeouts.lib.stenophoneme.Stenophoneme import Stenophoneme
            

    # sophemes = (
    #     Sopheme(
    #         (
    #             Orthokeysymbol(
    #                 (Keysymbol("z", "z"),), "z"
    #             ),
    #         ),
    #         (),
    #         Stenophoneme.Z,
    #     ),

    #     Sopheme(
    #         (
    #             Orthokeysymbol(
    #                 (Keysymbol("ou", "ou"),), "o"
    #             ),
    #         ),
    #         (),
    #         Stenophoneme.OO,
    #     ),
    # )

    # seq = " ".join(str(sopheme) for sopheme in sophemes)

    # print(parse_sopheme_seq("z.z[Z] o.ou[OO] d.d[D] i.ae!1[II] [[KWR]] a.@[A] c.k[K] [[KWR]] a.A5[A] l"))
    
    # assert (
    #     parse_sopheme_seq("z.z[Z] o.ou[OO] d.d[D] i.ae!1[II] [[KWR]] a.@[A] c.k[K] [[KWR]] a.A5[A] l")
    #     == (
            
    #     )
    # )