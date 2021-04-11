/* Copyright 2021 NVIDIA Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */

#include <memory>
#include <utility>
#include <vector>

#include "groupby/groupby_reduce.h"
#include "column/device_column.h"
#include "cudf_util/allocators.h"
#include "cudf_util/types.h"
#include "util/gpu_task_context.h"
#include "util/zip_for_each.h"

#include <cudf/table/table.hpp>
#include <cudf/table/table_view.hpp>
#include <cudf/detail/groupby.hpp>

namespace legate {
namespace pandas {
namespace groupby {

using Columns = std::vector<cudf::column_view>;

/*static*/ int64_t GroupByReductionTask::gpu_variant(
  const Legion::Task* task,
  const std::vector<Legion::PhysicalRegion>& regions,
  Legion::Context context,
  Legion::Runtime* runtime)
{
  Deserializer ctx(task, regions);

  GroupByArgs args;
  deserialize(ctx, args);

  // TODO: Tree reduction is not yet handled
  assert(args.in_keys.size() == 1);

  if (args.in_keys[0][0].empty()) {
    for (auto& out_key : args.out_keys) out_key.make_empty();
    for (auto& out_values : args.all_out_values)
      for (auto& out_value : out_values) out_value.make_empty();
    return 0;
  }

  GPUTaskContext gpu_ctx{};
  auto stream = gpu_ctx.stream();

  Columns in_keys;
  for (auto& in_key : args.in_keys[0])
    in_keys.push_back(DeviceColumn<true>{in_key}.to_cudf_column(stream));

  Columns in_values;
  for (auto& in_value : args.in_values)
    in_values.push_back(DeviceColumn<true>{in_value[0]}.to_cudf_column(stream));

  std::vector<cudf::groupby::aggregation_request> requests;
  util::for_each(in_values, args.all_aggs, [&](auto& in_value, auto& aggs) {
    requests.emplace_back(cudf::groupby::aggregation_request());
    auto& request  = requests.back();
    request.values = in_value;
    for (auto& agg : aggs) request.aggregations.push_back(to_cudf_agg(agg));
  });

  std::vector<DeviceOutputColumn> out_keys;
  for (auto& out_key : args.out_keys) out_keys.push_back(DeviceOutputColumn{out_key});

  DeferredBufferAllocator mr;

  auto cudf_output = cudf::groupby::detail::hash::groupby(
    cudf::table_view{std::move(in_keys)}, requests, cudf::null_policy::EXCLUDE, stream, &mr);

  util::for_each(cudf_output.first->view(), out_keys, [&](auto& cudf_output, auto& output) {
    DeviceOutputColumn{output}.return_from_cudf_column(mr, cudf_output, stream);
  });
  util::for_each(cudf_output.second, args.all_out_values, [&](auto& agg_result, auto& outputs) {
    util::for_each(agg_result.results, outputs, [&](auto& result, auto& output) {
      DeviceOutputColumn{output}.return_from_cudf_column(mr, result->view(), stream);
    });
  });

  return static_cast<int64_t>(cudf_output.first->num_rows());
}

}  // namespace groupby
}  // namespace pandas
}  // namespace legate
