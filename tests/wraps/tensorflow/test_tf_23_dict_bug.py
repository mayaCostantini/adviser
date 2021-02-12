#!/usr/bin/env python3
# thoth-adviser
# Copyright(C) 2020 Fridolin Pokorny
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Test a wrap that notifies a bug in summary output spotted on TensorFlow 2.3."""

import pytest

from thoth.adviser.enums import RecommendationType
from thoth.adviser.pipeline_builder import PipelineBuilderContext
from thoth.adviser.state import State
from thoth.adviser.wraps import TensorFlow23DictSummary

from ...base import AdviserUnitTestCase


class TestTensorFlow23DictSummary(AdviserUnitTestCase):
    """Test a wrap that notifies a bug in summary output spotted on TensorFlow 2.3."""

    UNIT_TESTED = TensorFlow23DictSummary

    def test_verify_multiple_should_include(self) -> None:
        """Verify multiple should_include calls do not loop endlessly."""
        builder_context = PipelineBuilderContext(recommendation_type=RecommendationType.LATEST)

        pipeline_config = list(self.UNIT_TESTED.should_include(builder_context))
        assert {"package_name": "tensorflow"} in pipeline_config
        assert {"package_name": "tensorflow-cpu"} in pipeline_config
        assert {"package_name": "tensorflow-gpu"} in pipeline_config
        assert {"package_name": "intel-tensorflow"} in pipeline_config
        assert len(pipeline_config) == 4

        for item in pipeline_config:
            unit = self.UNIT_TESTED()
            unit.update_configuration(item)
            builder_context.add_unit(unit)

        assert list(self.UNIT_TESTED.should_include(builder_context)) == [], "The unit must not be included"

    def test_run_noop(self) -> None:
        """Test no justification added if TensorFlow 2.3 is not resolved."""
        state = State()
        assert not state.justification
        assert "tensorflow" not in state.resolved_dependencies

        state.add_resolved_dependency(("tensorflow", "2.2.0", "https://pypi.org/simple"))

        unit = TensorFlow23DictSummary()
        unit.run(state)

        assert len(state.justification) == 0

    @pytest.mark.parametrize("tf_version", ["2.3.0"])
    def test_run(self, tf_version: str) -> None:
        """Test adding justification added if TensorFlow 2.3 is resolved."""
        state = State()
        assert not state.justification
        assert "tensorflow" not in state.resolved_dependencies

        state.add_resolved_dependency(("tensorflow", tf_version, "https://pypi.org/simple"))

        unit = TensorFlow23DictSummary()
        unit.run(state)

        assert len(state.justification) == 1
        assert set(state.justification[0].keys()) == {"type", "message", "link"}
        assert state.justification[0]["type"] == "WARNING"
        assert state.justification[0]["message"], "No justification message provided"
        assert state.justification[0]["link"], "Empty link to justification document provided"
