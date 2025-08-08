# This software is proprietary and confidential.
# Unauthorized copying, modification, distribution, or use of this software,
# via any medium, is strictly prohibited.
#
# This software is provided as an add-on to Revolution EDA distributed under the
# Mozilla Public License, version 2.0. The source code for this add-on software
# is not made available and all rights are reserved.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# (C) 2025 Revolution Semiconductor

from typing import NamedTuple

from polars import DataFrame


class viewTuple(NamedTuple):
    libraryName: str
    cellName: str
    viewName: str


class columnTag(NamedTuple):
    order: int
    name: str
    type: str


class dataFrameTuple(NamedTuple):
    header: str
    dataFrame: DataFrame
