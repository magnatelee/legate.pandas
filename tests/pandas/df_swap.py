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

from legate import pandas as lp
from tests.utils import equals

df = pd.DataFrame({"col1": [1, 2, 3], "col2": [4, 5, 6]})
ldf = lp.DataFrame(df)

ldf[["col2", "col1"]] = ldf[["col1", "col2"]]
assert ldf.columns[0] == "col1"
assert ldf.columns[1] == "col2"
assert equals(ldf.col1, df.col2)
assert equals(ldf.col2, df.col1)
