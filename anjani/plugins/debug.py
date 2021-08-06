""" Debugging purpose """
# Copyright (C) 2020 - 2021  UserbotIndo Team, <https://github.com/userbotindo.git>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import io
import sys
import traceback
from datetime import datetime
from typing import Any, ClassVar, Optional

from anjani import command, filters, plugin


class Debug(plugin.Plugin):
    name: ClassVar[str] = "Debug"

    async def cmd_ping(self, ctx: command.Context) -> str:
        start = datetime.now()
        await ctx.respond("Calculating response time...")
        end = datetime.now()
        latency = (end - start).microseconds / 1000

        return f"Latency: {latency} ms"

    async def aexec(self, code: str, ctx: command.Context) -> Any:
        """execute command"""
        head = "async def __aexec(anjani, ctx):\n    "
        code = "".join((f"\n    {line}" for line in code.split("\n")))
        exec(head + code)  # pylint: disable=exec-used
        return await locals()["__aexec"](self.bot, ctx)

    @command.filters(filters.staff_only)
    async def cmd_eval(self, ctx: command.Context) -> Optional[str]:
        """run a command"""
        cmd = ctx.input
        if not cmd:
            return "Input empty..."

        old_stderr = sys.stderr
        old_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()
        redirected_error = sys.stderr = io.StringIO()
        stdout, stderr, exc, returned = None, None, None, None

        try:
            returned = await self.aexec(cmd, ctx)
        except Exception:  # pylint: disable=broad-except
            exc = traceback.format_exc()

        stdout = redirected_output.getvalue().strip()
        stderr = redirected_error.getvalue().strip()
        sys.stdout = old_stdout
        sys.stderr = old_stderr

        evaluation = exc or stderr or stdout or returned

        output = "**CODE:**\n"
        output += f"```{cmd}```\n\n"
        try:  # handle the error while stringifying the result
            output += "**OUTPUT:**\n"
            output += f"```{self.bot.redact_message(str(evaluation))}```\n"
        except Exception:  # pylint: disable=broad-except
            output += "**Exception:**\n"
            output += f"```{traceback.format_exc()}```\n"

        if len(output) > 4096:
            with io.BytesIO(str.encode(output)) as out_file:
                out_file.name = "eval.text"
                await ctx.msg.reply_document(
                    document=out_file, caption=cmd, disable_notification=True
                )
        else:
            return output
