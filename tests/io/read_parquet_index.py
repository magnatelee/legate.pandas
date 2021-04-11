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

import os

import pandas as pd

from legate import pandas as lp

for idx in range(6):
    path = os.path.join(
        os.path.dirname(__file__), "files", f"read_parquet_index{idx}.parquet"
    )

    df = pd.read_parquet(path)

    ldf = lp.read_parquet(path)

    assert ldf.equals(df)

    names = ["a", "b"]

    df = pd.read_parquet(path, columns=names)

    ldf = lp.read_parquet(path, columns=names)

    assert ldf.equals(df)
