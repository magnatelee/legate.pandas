# Copyright 2021 NVIDIA Corporation
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
#

import pandas as pd
from numpy.random import permutation

from legate import pandas as lp
from tests.utils import equals_scalar, must_fail


def _test(ex, df, *args):
    def _make_access():
        df.at[args]

    must_fail(ex, _make_access)


for index in [
    pd.RangeIndex(10),
    pd.RangeIndex(1, 21, 2),
    pd.RangeIndex(21, 1, -2),
    pd.Index(permutation(10)),
]:
    print(f"Index: {index}")
    df = pd.DataFrame(
        {
            "a": range(10),
            "b": range(1, 11),
            "c": [str(i) * 3 for i in range(10)],
            "d": [str(i % 3) for i in range(10)],
        },
        index=index,
    )
    df["c"] = df["c"].astype(pd.StringDtype())
    df["d"] = df["d"].astype("category")
    ldf = lp.DataFrame(df)

    for idx, col in enumerate(["a", "b", "c", "d"]):
        print(f"Testing ldf.at[{index[idx + 3]}, {col}].__getitem__")
        out_pd = df.at[index[idx + 3], col]
        out_lp = ldf.at[index[idx + 3], col]
        assert equals_scalar(out_lp, out_pd)

    for idx, (col, val) in enumerate(zip(["a", "b", "c"], [100, 200, "5678"])):
        print(f"Testing ldf.at[{index[idx + 3]}, {col}].__setitem__")
        df.at[index[idx + 3], col] = val
        ldf.at[index[idx + 3], col] = val

        out_pd = df.at[index[idx + 3], col]
        out_lp = ldf.at[index[idx + 3], col]
        assert equals_scalar(out_lp, out_pd)

# Negative tests

ldf = lp.DataFrame({"a": range(10), "b": range(1, 11)})
_test(ValueError, ldf, slice(None))
_test(ValueError, ldf, [], [])
