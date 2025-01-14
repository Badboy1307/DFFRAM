# -*- coding: utf8 -*-
# Copyright ©2020-2021 The American University in Cairo and the Cloud V Project.
#
# This file is part of the DFFRAM Memory Compiler.
# See https://github.com/Cloud-V/DFFRAM for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .row import Row
from .util import d2a, sarv
from .placeable import Placeable, DataError

from opendbpy import dbInst
Instance = dbInst

import re
from types import SimpleNamespace as NS

P = Placeable

class Word(Placeable):
    def __init__(self, instances):
        self.clkgateand = None

        clkgate = r"CG\\\[(\d+)\\\]"
        clkgateand = r"CGAND" # placed at its pin at the right
        inv1 = r"INV1\\\[(\d+)\\\]"
        inv2 = r"INV2\\\[(\d+)\\\]"
        bit_ff = r"BIT\\\[(\d+)\\\]\.FF"
        bit_obuf1 = r"BIT\\\[(\d+)\\\]\.OBUF1"
        bit_obuf2 = r"BIT\\\[(\d+)\\\]\.OBUF2"

        raw_clkgates = {}
        raw_ffs = {}
        raw_obufs1 = {}
        raw_obufs2 = {}
        raw_invs1 = {}
        raw_invs2 = {}

        m = NS()
        for instance in instances:

            n = instance.getName()

            if sarv(m, "clkgate_match", re.search(clkgate, n)):
                i = int(m.clkgate_match[1])
                raw_clkgates[i] = instance

            elif sarv(m, "inv1_match", re.search(inv1, n)):
                i = int(m.inv1_match[1])
                raw_invs1[i] = instance

            elif sarv(m, "inv2_match", re.search(inv2, n)):
                i = int(m.inv2_match[1])
                raw_invs2[i] = instance

            elif sarv(m, "bit_ff_match", re.search(bit_ff, n)):
                i = int(m.bit_ff_match[1])
                raw_ffs[i] = instance

            elif sarv(m, "bit_obuf1_match", re.search(bit_obuf1, n)):
                i = int(m.bit_obuf1_match[1])
                raw_obufs1[i] = instance

            elif sarv(m, "bit_obuf2_match", re.search(bit_obuf2, n)):
                i = int(m.bit_obuf2_match[1])
                raw_obufs2[i] = instance

            elif sarv(m, "clkgateand_match", re.search(clkgateand, n)):
                self.clkgateand = instance

            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.clkgates = d2a(raw_clkgates)
        self.invs1 = d2a(raw_invs1)
        self.invs2 = d2a(raw_invs2)
        self.ffs = d2a(raw_ffs)
        self.obufs1 = d2a(raw_obufs1)
        self.obufs2 = d2a(raw_obufs2)

    def place(self, row_list, start_row=0):
        r = row_list[start_row]
        word_width = 32
        for i in range(word_width): # 32
            # TODO: Use middle placement
            # to make the clkgateand an equal distance from all
            # gates that need its output

            if i % 8 == 0: # range(4) every 8 place an inv
                r.place(self.invs1[i//8])
                r.place(self.invs2[i//8])
            if i == (word_width // 2): # 16 range(1)
                r.place(self.clkgateand)
            if i % 8 == 0: # range(4) every 8 place a clk gate
                r.place(self.clkgates[i//8])

            r.place(self.ffs[i])
            r.place(self.obufs1[i])
            r.place(self.obufs2[i])

        return start_row + 1

    def word_count(self):
        return 1


class DFFRF(Placeable): # 32 words
    def __init__(self, instances):

        raw_words = {}
        raw_decoders5x32 = {}

        word = r"\bREGF\\\[(\d+)\\\]\.RFW\b"
        decoder5x32 = r"\bDEC(\d+)\b"

        raw_rfw0_ties = {}
        raw_rfw0_invs1 = {}
        raw_rfw0_invs2 = {}
        raw_rfw0_obufs1 = {}
        raw_rfw0_obufs2 = {}

        rfw0_tie = r"RFW0\.TIE\\\[(\d+)\\\]"
        rfw0_inv1 = r"RFW0\.INV1\\\[(\d+)\\\]"
        rfw0_inv2 = r"RFW0\.INV2\\\[(\d+)\\\]"
        rfw0_obuf1 = r"\bRFW0\.BIT\\\[(\d+)\\\]\.OBUF1\b"
        rfw0_obuf2 = r"\bRFW0\.BIT\\\[(\d+)\\\]\.OBUF2\b"

        m = NS()
        for instance in instances:

            n = instance.getName()

            if sarv(m, "word_match", re.search(word, n)):
                i = int(m.word_match[1])
                raw_words[i] = raw_words.get(i) or []
                raw_words[i].append(instance)

            elif sarv(m, "decoder5x32_match", re.search(decoder5x32, n)):
                i = int(m.decoder5x32_match[1])
                raw_decoders5x32[i] = raw_decoders5x32.get(i) or []
                raw_decoders5x32[i].append(instance)

            elif sarv(m, "rfw0_obuf_match1", re.search(rfw0_obuf1, n)):
                bit = int(m.rfw0_obuf_match1[1])
                raw_rfw0_obufs1[bit] = instance

            elif sarv(m, "rfw0_obuf_match2", re.search(rfw0_obuf2, n)):
                bit = int(m.rfw0_obuf_match2[1])
                raw_rfw0_obufs2[bit] = instance

            elif sarv(m, "rfw0_tie_match", re.search(rfw0_tie, n)):
                i = int(m.rfw0_tie_match[1])
                raw_rfw0_ties[i] = instance

            elif sarv(m, "rfw0_inv1_match", re.search(rfw0_inv1, n)):
                i = int(m.rfw0_inv1_match[1])
                raw_rfw0_invs1[i] = instance

            elif sarv(m, "rfw0_inv2_match", re.search(rfw0_inv2, n)):
                i = int(m.rfw0_inv2_match[1])
                raw_rfw0_invs2[i] = instance

            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.words = d2a({k: Word(v) for k, v in raw_words.items()})
        self.decoders5x32 = d2a({k: Decoder5x32(v) for k, v in raw_decoders5x32.items()})

        self.rfw0_ties = d2a(raw_rfw0_ties)
        self.rfw0_invs1 = d2a(raw_rfw0_invs1)
        self.rfw0_invs2 = d2a(raw_rfw0_invs2)
        self.rfw0_obufs1 = d2a(raw_rfw0_obufs1)
        self.rfw0_obufs2 = d2a(raw_rfw0_obufs2)

    def place(self, row_list, start_row=0):
        #    |      5x32 decoders placement          |  |
        #    |                                       |  |
        #    |                                       |  |
        #    V                                       V  V
        #  { _ ====================================  ____   }
        # 32 _ ====================================  ____  32
        #  { D2 ==================================== D0 D1  }

        # D2 placement
        def width_rfw0():
            tot_width = 0

            for aninv in [*self.rfw0_invs1, *self.rfw0_invs2]:
                tot_width += aninv.getMaster().getWidth()
            for atie in self.rfw0_ties:
                tot_width += atie.getMaster().getWidth()
            for anobuf in [*self.rfw0_obufs1,*self.rfw0_obufs2] :
                tot_width += anobuf.getMaster().getWidth()

            return tot_width

        def rfw0_placement_start(row_list, start_row,
                                x_start, x_current,
                                x_end):
            design_width = x_end - x_start
            return x_current + ((design_width - width_rfw0()) // 2)

        def place_rfw0(row, start_loc):
            # RFWORD0 placement
            # Should center this row
            # get width of the design and then put equal
            # distance around this row both on left and right

            start_row = 0
            row.x = start_loc

            for i in range(32):
                if i % 8 == 0: # range(4)
                    row.place(self.rfw0_invs1[i//8])
                    row.place(self.rfw0_invs2[i//8])
                if i % 4 == 0: # range(8)
                    row.place(self.rfw0_ties[i//4])
                row.place(self.rfw0_obufs1[i])
                row.place(self.rfw0_obufs2[i])
            return row.x


        self.decoders5x32[2].place(row_list, start_row, (32-4)//2, flip=True)
        row0_empty_space_1_start = row_list[start_row].x
        words_start_x = row0_empty_space_1_start

        current_row = start_row + 1
        for aword in self.words:
            aword.place(row_list, current_row)
            current_row += 1

        highest_row = current_row
        words_end_x = row_list[1].x
        row0_empty_space_2_end = words_end_x

        # D0 placement
        self.decoders5x32[0].place(row_list, start_row, 4)
        # D1 placement
        self.decoders5x32[1].place(row_list, start_row, 20)

        row0_empty_space_1_end = rfw0_placement_start(row_list, 0,
                                    words_start_x,
                                    row_list[0].x,
                                    words_end_x)
        Row.fill_row(row_list,
                0,
                row0_empty_space_1_start,
                row0_empty_space_1_end)

        row0 = row_list[0]
        rfw0_placement_end = place_rfw0(row0,
                                        row0_empty_space_1_end)
        row0_empty_space_2_start = rfw0_placement_end


        Row.fill_row(row_list,
                0,
                row0_empty_space_2_start,
                row0_empty_space_2_end)

        # Fill all empty spaces on edges
        Row.fill_rows(row_list, start_row, highest_row)
        return highest_row

    def word_count(self):
        return 32

class Decoder5x32(Placeable):
    def __init__(self, instances):
        self.enbuf = None


        decoder2x4 = r"DEC(\d+)\.D"
        decoder3x8 = r"DEC(\d+)\.D(\d+)"

        raw_decoders3x8 = {} # multiple decoders so multiple entries ordered by 1st match
        self.decoder2x4 = [] # one decoder so array

        m = NS()
        for instance in instances:

            n = instance.getName()

            if sarv(m, "decoder3x8_match", re.search(decoder3x8, n)):
                i = int(m.decoder3x8_match[2])
                raw_decoders3x8[i] = raw_decoders3x8.get(i) or []
                raw_decoders3x8[i].append(instance)

            elif sarv(m, "decoder2x4_match", re.search(decoder2x4, n)):
                # TODO(ahmednofal): check if these instances
                # are not ordered so it might not be
                # the most optimal placement
                self.decoder2x4.append(instance)
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.decoders3x8 = d2a({k: Decoder3x8(v) for k, v in raw_decoders3x8.items()})
        self.decoder2x4 = Decoder2x4(self.decoder2x4)

    def place(self, row_list, start_row=0, decoder2x4_start_row=0, flip=False):
        current_row = start_row

        if flip:
            current_row = self.decoder2x4.place(row_list, decoder2x4_start_row)
            for idx in range(len(self.decoders3x8)):
                self.decoders3x8[idx].place(row_list, idx*8)
            # Row.fill_rows(row_list, start_row, current_row)

        else:
            for idx in range(len(self.decoders3x8)):
                self.decoders3x8[idx].place(row_list, idx*8)

            current_row = self.decoder2x4.place(row_list, decoder2x4_start_row)
            # Row.fill_rows(row_list, start_row, current_row)
        return start_row + 32 # 5x32 has 4 3x8 on top of each other and each is 8 rows

class Decoder3x8(Placeable):
    def __init__(self, instances):
        self.andgates = None

        andgate = r"\bAND(\d+)\b"
        abuf = r"\bABUF\\\[(\d+)\\\]"
        enbuf = r"\bENBUF\b"

        raw_andgates = {} # multiple decoders so multiple entries ordered by 1st match
        raw_abufs = {}
        self.enbuf = None

        m = NS()
        for instance in instances:

            n = instance.getName()

            if sarv(m, "andgate_match", re.search(andgate, n)):
                i = int(m.andgate_match[1])
                raw_andgates[i] = raw_andgates.get(i) or []
                raw_andgates[i] = instance
            elif sarv(m, "abuf_match", re.search(abuf, n)):
                i = int(m.abuf_match[1])
                raw_abufs[i] = raw_abufs.get(i) or []
                raw_abufs[i] = instance
            elif sarv(m, "enbuf_match", re.search(enbuf, n)):
                self.enbuf = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.andgates = d2a(raw_andgates)
        self.abufs = d2a(raw_abufs)

    def place(self, row_list, start_row=0):
        """
        By placing this decoder, you agree that rows[start_row:start_row+7]
        are at the sole mercy of this function.
        """

        for i in range(8): # range is 8 because 3x8 has 8 and gates put on on top of each other
            r = row_list[start_row + i]
            if i < len(self.andgates):
                r.place(self.andgates[i])

        i = 0
        for instance in self.abufs + [self.enbuf]:
            r = row_list[start_row + i]
            r.place(instance)
            i += 1


        return start_row + 8

class Decoder2x4(Placeable):
    def __init__(self, instances):
        self.andgates = None

        andgate = r"AND(\d+)"

        raw_andgates = {} # multiple decoders so multiple entries ordered by 1st match

        m = NS()
        for instance in instances:

            n = instance.getName()

            if sarv(m, "andgate_match", re.search(andgate, n)):
                i = int(m.andgate_match[1])
                raw_andgates[i] = raw_andgates.get(i) or []
                raw_andgates[i] = instance
            else:
                raise DataError("Unknown element in %s: %s" % (type(self).__name__, n))

        self.andgates = d2a(raw_andgates)

    def place(self, row_list, start_row=0):
        for i in range(4): # range is 8 because 3x8 has 8 and gates put on on top of each other
            r = row_list[start_row + i]
            r.place(self.andgates[i])

        return start_row + 4
